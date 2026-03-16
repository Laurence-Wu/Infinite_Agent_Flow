"""
AgentOrchestrator — Main entry point for the Card Dealer engine.

Peer-agent model: every process running this file is equal.
The FIRST process owns the Flask/Next.js dashboard.
Subsequent processes attach with ``--server URL`` and report state
to the existing dashboard via RemoteStateManager.

Usage:
    # First agent — owns the dashboard
    python orchestrator.py --workspace ./output --workflow sample_workflow --version v1

    # Peer agent — attaches to existing dashboard
    python orchestrator.py --workspace ./output2 --workflow other_workflow --version v1 \\
        --server http://localhost:5000 --agent-id agent_1
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.dealer_factory import build_dealer_stack
from core.dealer_manager import DealerRegistry
from core.hook_manager import HookManager
from core.tmux_manager import TmuxManager
from engine.scanner import WorkspaceScanner
from web.app import create_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("orchestrator")


class _StateLogHandler(logging.Handler):
    """Captures log records into the StateManager's ring buffer for the dashboard."""

    def __init__(self, state, agent_id: str | None = None):
        super().__init__()
        self._state = state
        self._agent_id = agent_id
        self.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        ))

    # Loggers whose output should NOT appear in the per-agent live log
    _EXCLUDED_LOGGERS = {"werkzeug", "urllib3", "httpx", "httpcore"}

    def emit(self, record: logging.LogRecord) -> None:
        if record.name.split(".")[0] in self._EXCLUDED_LOGGERS:
            return
        try:
            self._state.push_log(self.format(record), agent_id=self._agent_id)
        except Exception:
            pass


class AgentOrchestrator:
    """
    Entry point that ties all engine components together.

    If ``server_url`` is None: owns the Flask dashboard + Next.js frontend.
    If ``server_url`` is set: peer-attach mode — skips Flask, reports state remotely.
    """

    def __init__(
        self,
        workspace_path: str,
        workflow_name: str,
        version: str,
        workflows_path: str | None = None,
        flask_port: int = 5000,
        server_url: str | None = None,
        agent_id: str | None = None,
        ngrok_auth: str | None = None,
        session_name: str | None = None,
        auto_start: bool = False,
        agent_command: str | None = None,
    ):
        wf_path = workflows_path or str(PROJECT_ROOT / "workflows")
        self._server_url = server_url
        self._flask_port = flask_port
        self._workflow_name = workflow_name
        self._version = version
        self._frontend_proc: subprocess.Popen | None = None
        self._ngrok_proc: subprocess.Popen | None = None
        self._ngrok_auth: str | None = ngrok_auth
        self._auto_start = auto_start

        # Derive agent_id: explicit > workspace name > "default"
        derived_id = agent_id or (
            Path(workspace_path).resolve().name if server_url else "default"
        )

        self._hook_manager = HookManager()

        # Build entire agent stack through the factory (single source of truth)
        self._stack = build_dealer_stack(
            workspace=workspace_path,
            workflow=workflow_name,
            version=version,
            dealer_id=derived_id,
            hook_manager=self._hook_manager,
            server_url=server_url,
            workflows_path=wf_path,
        )

        # Wire logs into the state ring-buffer so the dashboard shows them
        _log_handler = _StateLogHandler(self._stack.state, agent_id=derived_id)
        logging.getLogger().addHandler(_log_handler)

        self.scanner = WorkspaceScanner(self._stack.config)

        # Build TmuxManager — command + wait can be overridden via CLI flags
        cfg = self._stack.config
        ws = cfg.resolved_workspace
        cmd = agent_command or cfg.agent_command
        sname = session_name or f"{cmd.split()[0]}_{ws.name}"
        self._tmux = TmuxManager(
            workspace=ws,
            session_name=sname,
            loop_file=(ws / "AGENT_LOOP.md") if (ws / "AGENT_LOOP.md").exists()
                      else (PROJECT_ROOT / "workspace" / "AGENT_LOOP.md"),
            agent_command=cmd,
            startup_wait=cfg.agent_startup_wait,
        )

        # Dashboard mode only: create registry and Flask app
        if server_url is None:
            self._registry = DealerRegistry(self._hook_manager, wf_path)
            self._registry.register_stack(self._stack)
            self._registry.register_tmux(derived_id, self._tmux)
            self.app = create_app(
                config=self._stack.config,
                state=self._stack.state,
                picker=self._stack.picker,
                scanner=self.scanner,
                registry=self._registry,
                archive=self._stack.archive,
                tmux_manager=self._tmux,
            )
        else:
            self._registry = None
            self.app = None

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def run(self) -> None:
        """
        Start dashboard (if owner), then run the planner loop (blocks).
        """
        if self._server_url:
            logger.info(
                "Peer-attach mode: reporting state to %s as agent '%s'",
                self._server_url, self._stack.agent_id,
            )
            # Push tmux pane snapshot to the primary server every 3 s
            threading.Thread(
                target=self._push_pane_loop,
                daemon=True,
                name="pane-push",
            ).start()
        else:
            self._start_web()
            logger.info(
                "Dashboard running at http://localhost:%d", self._flask_port,
            )
            self._start_frontend()
            self._start_ngrok()

        # Auto-start the AI agent tmux session if requested
        if self._auto_start:
            logger.info(
                "Auto-starting tmux session '%s' with command '%s'",
                self._tmux.session_name, self._tmux.agent_command,
            )
            threading.Thread(target=self._tmux.start, daemon=True, name="tmux-autostart").start()

        # Background health monitor
        threading.Thread(target=self._monitor_health, daemon=True, name="health-monitor").start()

        logger.info(
            "Starting workflow: %s/%s → workspace: %s",
            self._workflow_name, self._version,
            self._stack.config.resolved_workspace,
        )

        _interrupted = False
        try:
            self._stack.planner.run(self._workflow_name, self._version)
        except KeyboardInterrupt:
            logger.info("Interrupted by user.")
            _interrupted = True
            self._stack.planner.stop()
        finally:
            if not self._server_url and _interrupted:
                self._stop_tmux()
                self._stop_ngrok()
                self._stop_frontend()

        # Planner stopped via API (not Ctrl+C) — keep Flask alive so the
        # dashboard remains accessible for further control (restart, new dealers).
        if not self._server_url and not _interrupted:
            logger.info(
                "Planner finished. Dashboard still running at "
                "http://localhost:%d — press Ctrl+C to exit.",
                self._flask_port,
            )
            try:
                threading.Event().wait()
            except KeyboardInterrupt:
                logger.info("Interrupted by user.")
                self._stop_tmux()
                self._stop_ngrok()
                self._stop_frontend()

    # ------------------------------------------------------------------ #
    #  Internal
    # ------------------------------------------------------------------ #

    def _push_pane_loop(self) -> None:
        """Attached-agent only: push tmux pane snapshot to primary server every 3 s.
        Reads back any queued agent command (start/stop/pause/restart) from the response.
        """
        url = f"{self._server_url}/api/dealer/{self._stack.agent_id}/pane-update"
        while True:
            try:
                status = self._tmux.status()
                body = json.dumps(status).encode()
                req = urllib.request.Request(
                    url, data=body,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read())
                cmd = data.get("cmd")
                if cmd:
                    if cmd == "start":
                        threading.Thread(target=self._tmux.start, daemon=True).start()
                    elif cmd == "stop":
                        self._tmux.stop()
                    elif cmd == "pause":
                        self._tmux.pause()
                    elif cmd == "restart":
                        threading.Thread(target=self._tmux.restart, daemon=True).start()
            except Exception:
                pass
            time.sleep(3)

    def _monitor_health(self) -> None:
        """Periodically checks whether the tmux session is alive and logs if it dies."""
        CHECK_INTERVAL = 30  # seconds
        was_alive: bool | None = None
        while True:
            time.sleep(CHECK_INTERVAL)
            try:
                alive = self._tmux.is_alive()
                if was_alive is True and not alive:
                    logger.warning(
                        "tmux session '%s' is dead — use the dashboard or "
                        "scripts/restart_agent.sh to recover",
                        self._tmux.session_name,
                    )
                elif was_alive is False and alive:
                    logger.info("tmux session '%s' is now alive", self._tmux.session_name)
                was_alive = alive
            except Exception:
                pass

    def _start_web(self) -> None:
        thread = threading.Thread(
            target=self.app.run,
            kwargs={
                "host": self._stack.config.flask_host,
                "port": self._flask_port,
                "debug": False,
                "use_reloader": False,
            },
            daemon=True,
            name="flask-dashboard",
        )
        thread.start()

    def _start_frontend(self) -> None:
        frontend_dir = PROJECT_ROOT / "frontend"
        if not (frontend_dir / "package.json").exists():
            return
        if not (frontend_dir / "node_modules").exists():
            logger.warning(
                "frontend/node_modules not found — run 'cd frontend && npm install'. "
                "Skipping Next.js startup."
            )
            return

        npm = "npm.cmd" if sys.platform == "win32" else "npm"
        env = os.environ.copy()
        env["FLASK_PORT"] = str(self._flask_port)

        try:
            self._frontend_proc = subprocess.Popen(
                [npm, "run", "dev"],
                cwd=str(frontend_dir),
                env=env,
                creationflags=(
                    subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
                ),
                start_new_session=(sys.platform != "win32"),
            )
            logger.info(
                "Next.js frontend started at http://localhost:3000 (proxying to port %d)",
                self._flask_port,
            )
        except FileNotFoundError:
            logger.warning("npm not found — Next.js frontend will not start.")

    def _stop_tmux(self) -> None:
        try:
            self._tmux.stop()
            logger.info("tmux session '%s' stopped on exit.", self._tmux.session_name)
        except Exception as exc:
            logger.warning("Could not stop tmux session on exit: %s", exc)

    def _stop_frontend(self) -> None:
        from core.process_utils import kill_process_tree
        kill_process_tree(self._frontend_proc, "Next.js frontend")
        self._frontend_proc = None

    def _start_ngrok(self) -> None:
        if not self._ngrok_auth:
            return
        cmd = ["ngrok", "http", "3000", f"--basic-auth={self._ngrok_auth}"]
        try:
            self._ngrok_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=(
                    subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
                ),
                start_new_session=(sys.platform != "win32"),
            )
            logger.info("ngrok tunnel starting… fetching public URL.")
            threading.Thread(target=self._log_ngrok_url, daemon=True).start()
        except FileNotFoundError:
            logger.warning("ngrok not found in PATH — tunnel will not start.")

    def _log_ngrok_url(self) -> None:
        for _ in range(15):
            time.sleep(1)
            try:
                with urllib.request.urlopen(
                    "http://127.0.0.1:4040/api/tunnels", timeout=2
                ) as resp:
                    data = json.loads(resp.read())
                    for tunnel in data.get("tunnels", []):
                        if tunnel.get("proto") == "https":
                            logger.info(
                                "ngrok public URL: %s  (basic-auth protected)",
                                tunnel["public_url"],
                            )
                            return
            except Exception:
                pass
        logger.warning("Could not determine ngrok public URL after 15 s.")

    def _stop_ngrok(self) -> None:
        from core.process_utils import kill_process_tree
        kill_process_tree(self._ngrok_proc, "ngrok tunnel")
        self._ngrok_proc = None


# ---------------------------------------------------------------------- #
#  CLI
# ---------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(
        description="CardDealer — Agent Instruction Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  # Dashboard owner\n"
            "  python orchestrator.py --workspace ./output "
            "--workflow sample_workflow --version v1\n\n"
            "  # Peer attach\n"
            "  python orchestrator.py --workspace ./output2 "
            "--workflow other_workflow --version v1 "
            "--server http://localhost:5000 --agent-id agent_1"
        ),
    )
    parser.add_argument("--workspace", "-w", required=True,
        help="Target directory where current_task.md and archive are managed.")
    parser.add_argument("--workflow", "-f", required=True,
        help="Name of the workflow to run (directory name under workflows/).")
    parser.add_argument("--version", "-v", default="v1",
        help="Workflow version (default: v1).")
    parser.add_argument("--workflows-path", default=None,
        help="Custom path to the workflows root directory.")
    parser.add_argument("--port", "-p", type=int, default=5000,
        help="Flask dashboard port (default: 5000). Ignored in peer-attach mode.")
    parser.add_argument("--server", "--attach", default=None, metavar="URL",
        help=(
            "Attach to an existing dashboard at URL (e.g. http://localhost:5000). "
            "Skips starting a local Flask server."
        ),
    )
    parser.add_argument("--agent-id", default=None,
        help="Unique identifier for this agent (default: workspace directory name).")
    parser.add_argument("--ngrok-auth", default=None, metavar="USER:PASS",
        help="Start an ngrok tunnel to the frontend (port 3000) with HTTP basic auth.")
    parser.add_argument("--session-name", default=None, metavar="NAME",
        help="tmux session name (default: <agent_command>_<workspace>).")
    parser.add_argument("--agent-command", default=None, metavar="CMD",
        help="AI agent CLI command to run in the tmux session (default: from config, usually 'gemini').")
    parser.add_argument("--auto-start", action="store_true",
        help="Automatically start the tmux agent session when the orchestrator launches.")

    args = parser.parse_args()

    orchestrator = AgentOrchestrator(
        workspace_path=args.workspace,
        workflow_name=args.workflow,
        version=args.version,
        workflows_path=args.workflows_path,
        flask_port=args.port,
        server_url=args.server,
        agent_id=args.agent_id,
        ngrok_auth=args.ngrok_auth,
        session_name=args.session_name,
        auto_start=args.auto_start,
        agent_command=args.agent_command,
    )
    orchestrator.run()


if __name__ == "__main__":
    main()
