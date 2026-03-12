"""
AgentOrchestrator \u2014 Main entry point for the Card Dealer engine.

Ties together: EngineConfig, StateManager, CardsPicker, CardsDealer,
CardsPlanner, and the Flask web dashboard.

Usage:
    python orchestrator.py --workspace ./output --workflow sample_workflow --version v1
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import signal
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

from core.config import EngineConfig
from core.state_manager import StateManager
from engine.dealer import CardsDealer
from engine.picker import CardsPicker
from engine.planner import CardsPlanner
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

    def __init__(self, state: "StateManager", agent_id: str | None = None):
        super().__init__()
        self._state = state
        self._agent_id = agent_id
        self.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        ))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._state.push_log(self.format(record), agent_id=self._agent_id)
        except Exception:
            pass


class AgentOrchestrator:
    """
    Public API for the Card Dealer engine.

    Accepts the target workspace directory, spins up all components,
    starts the Flask dashboard in a daemon thread, then runs the
    Planner's watchdog-based main loop.
    """

    def __init__(
        self,
        workspace_path: str,
        workflow_name: str,
        version: str,
        workflows_path: str | None = None,
        flask_port: int = 5000,
        attach_url: str | None = None,
        agent_id: str | None = None,
    ):
        # ---- Config ----
        wf_path = workflows_path or str(PROJECT_ROOT / "workflows")
        self.config = EngineConfig(
            workspace_path=workspace_path,
            workflows_path=wf_path,
            flask_port=flask_port,
        )

        # ---- Shared state ----
        self._attach_url = attach_url
        if attach_url:
            # If no agent_id provided, derive from workspace name
            self._agent_id = agent_id or Path(workspace_path).resolve().name
            from core.state_manager import RemoteStateManager
            self.state = RemoteStateManager(attach_url, self._agent_id)
        else:
            self._agent_id = agent_id or "default"
            self.state = StateManager()

        # ---- Log capture \u2192 dashboard ring buffer ----
        _log_handler = _StateLogHandler(self.state, agent_id=self._agent_id)
        logging.getLogger().addHandler(_log_handler)

        # ---- Engine components ----
        self.picker  = CardsPicker(self.config)
        self.dealer  = CardsDealer(self.config, self.state)
        self.planner = CardsPlanner(self.config, self.state, self.picker, self.dealer)
        self.scanner = WorkspaceScanner(self.config)

        # ---- Web dashboard ----
        self.app = create_app(self.config, self.state, self.picker, self.scanner)

        # ---- Workflow identity ----
        self._workflow_name = workflow_name
        self._version = version
        self._frontend_proc: subprocess.Popen | None = None
        self._ngrok_proc:    subprocess.Popen | None = None
        self._ngrok_auth:    str | None = None  # set before run()

    # ------------------------------------------------------------------ #
    #  Public methods
    # ------------------------------------------------------------------ #

    def run(self) -> None:
        """
        Start the dashboard (background thread), then run the planner
        in the foreground (blocks until workflow completes).
        """
        if self._attach_url:
            logger.info("Attached to existing dashboard at %s (skipping local Flask)", self._attach_url)
        else:
            self._start_web()
            logger.info(
                "Dashboard running at http://%s:%d",
                self.config.flask_host,
                self.config.flask_port,
            )

        logger.info(
            "Starting workflow: %s/%s \u2192 workspace: %s",
            self._workflow_name,
            self._version,
            self.config.resolved_workspace,
        )

        self._start_frontend()
        self._start_ngrok()
        try:
            self.planner.run(self._workflow_name, self._version)
        except KeyboardInterrupt:
            logger.info("Interrupted by user.")
            self.planner.stop()
        finally:
            self._stop_ngrok()
            self._stop_frontend()

    def deal_next(self) -> None:
        """Manually advance one card (useful for interactive/debug mode)."""
        snapshot = self.state.get_snapshot(self._agent_id)
        current_id = snapshot.get("current_card_id")

        if current_id is None:
            # No card dealt yet \u2014 deal the first one
            card = self.picker.get_first_card(self._workflow_name, self._version)
        else:
            card = self.picker.get_next_card(
                self._workflow_name, self._version, current_id
            )
            if card is None:
                logger.info("Workflow already finished.")
                return

        total = self.picker.get_total_cards(self._workflow_name, self._version)
        idx = self.picker.get_card_index(
            self._workflow_name, self._version, card.id
        )
        self.dealer.deal_card(card, card_index=idx, total_cards=total)
        logger.info("Manually dealt card: %s", card.id)

    # ------------------------------------------------------------------ #
    #  Internal
    # ------------------------------------------------------------------ #

    def _start_web(self) -> None:
        """Start Flask in a daemon thread (non-blocking)."""
        thread = threading.Thread(
            target=self.app.run,
            kwargs={
                "host": self.config.flask_host,
                "port": self.config.flask_port,
                "debug": False,
                "use_reloader": False,
            },
            daemon=True,
            name="flask-dashboard",
        )
        thread.start()

    def _start_frontend(self) -> None:
        """Start the Next.js dev server as a subprocess (non-blocking)."""
        frontend_dir = PROJECT_ROOT / "frontend"
        if not (frontend_dir / "package.json").exists():
            return
        if not (frontend_dir / "node_modules").exists():
            logger.warning(
                "frontend/node_modules not found \u2014 run 'cd frontend && npm install' first. "
                "Skipping Next.js startup."
            )
            return

        npm = "npm.cmd" if sys.platform == "win32" else "npm"
        
        # Determine port for Next.js to proxy to
        proxy_port = str(self.config.flask_port)
        if self._attach_url:
            try:
                parsed = urllib.parse.urlparse(self._attach_url)
                if parsed.port:
                    proxy_port = str(parsed.port)
            except Exception:
                pass

        env = os.environ.copy()
        env["FLASK_PORT"] = proxy_port

        try:
            self._frontend_proc = subprocess.Popen(
                [npm, "run", "dev"],
                cwd=str(frontend_dir),
                env=env,
                # New process group so we can kill the whole tree cleanly
                creationflags=(
                    subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
                ),
            )
            logger.info("Next.js frontend started at http://localhost:3000 (proxying to port %s)", proxy_port)
        except FileNotFoundError:
            logger.warning("npm not found \u2014 Next.js frontend will not start.")

    def _stop_frontend(self) -> None:
        """Kill the Next.js process tree."""
        proc = self._frontend_proc
        if proc is None:
            return
        logger.info("Stopping Next.js frontend (pid %d)\u2026", proc.pid)
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                    capture_output=True,
                )
            else:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception as exc:
            logger.warning("Could not stop frontend process: %s", exc)
        finally:
            self._frontend_proc = None

    def _start_ngrok(self) -> None:
        """Start an ngrok HTTP tunnel pointing at port 3000.
        Only runs if self._ngrok_auth is set (passed via --ngrok-auth CLI arg).
        Fetches and logs the public URL from ngrok's local API once it is ready."""
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
            )
            logger.info("ngrok tunnel starting\u2026 fetching public URL.")
            threading.Thread(target=self._log_ngrok_url, daemon=True).start()
        except FileNotFoundError:
            logger.warning("ngrok not found in PATH \u2014 tunnel will not start.")

    def _log_ngrok_url(self) -> None:
        """Poll ngrok's local API until the tunnel URL is available, then log it."""
        for attempt in range(15):
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
        logger.warning("Could not determine ngrok public URL after 15s.")

    def _stop_ngrok(self) -> None:
        """Kill the ngrok process tree."""
        proc = self._ngrok_proc
        if proc is None:
            return
        logger.info("Stopping ngrok tunnel (pid %d)\u2026", proc.pid)
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                    capture_output=True,
                )
            else:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception as exc:
            logger.warning("Could not stop ngrok: %s", exc)
        finally:
            self._ngrok_proc = None


# ---------------------------------------------------------------------- #
#  CLI
# ---------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(
        description="CardDealer \u2014 Agent Instruction Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example:\n"
            "  python orchestrator.py --workspace ./output "
            "--workflow sample_workflow --version v1"
        ),
    )
    parser.add_argument(
        "--workspace", "-w",
        required=True,
        help="Target directory where current_task.md and archive are managed.",
    )
    parser.add_argument(
        "--workflow", "-f",
        required=True,
        help="Name of the workflow to run (directory name under workflows/).",
    )
    parser.add_argument(
        "--version", "-v",
        default="v1",
        help="Workflow version (default: v1).",
    )
    parser.add_argument(
        "--workflows-path",
        default=None,
        help="Custom path to the workflows root directory.",
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=5000,
        help="Flask dashboard port (default: 5000).",
    )
    parser.add_argument(
        "--attach",
        default=None,
        metavar="URL",
        help=(
            "Connect to an existing dashboard at URL (e.g. http://localhost:5000). "
            "Skips starting a local Flask server."
        ),
    )
    parser.add_argument(
        "--agent-id",
        default=None,
        help="Unique identifier for this agent instance (default: workspace name).",
    )
    parser.add_argument(
        "--ngrok-auth",
        default=None,
        metavar="USER:PASS",
        help=(
            "Start an ngrok tunnel to the Next.js frontend (port 3000) "
            "protected by HTTP basic auth. Example: --ngrok-auth 'alice:secret'"
        ),
    )

    args = parser.parse_args()

    orchestrator = AgentOrchestrator(
        workspace_path=args.workspace,
        workflow_name=args.workflow,
        version=args.version,
        workflows_path=args.workflows_path,
        flask_port=args.port,
        attach_url=args.attach,
        agent_id=args.agent_id,
    )
    orchestrator._ngrok_auth = args.ngrok_auth
    orchestrator.run()


if __name__ == "__main__":
    main()
