"""
Manages a named tmux session that runs the AI agent CLI (Gemini, Claude, etc.).

Cross-platform:
  - Linux / macOS / WSL-native : calls `tmux` directly
  - Windows (host)             : calls `wsl tmux` (requires WSL2 + tmux inside WSL)
"""
from __future__ import annotations

import logging
import platform
import subprocess
import threading
import time
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class TmuxManager:
    """Controls a single named tmux session for the workspace AI agent."""

    def __init__(
        self,
        workspace: Path,
        session_name: str,
        loop_file: Path,
        agent_command: str = "gemini",
        startup_wait: int = 20,
    ) -> None:
        self._workspace = Path(workspace).resolve()
        self._session = session_name
        self._loop_file = Path(loop_file).resolve()
        self._agent_command = agent_command
        self._startup_wait = startup_wait
        self._base = self._resolve_base()
        self._starting = False  # True while the background startup thread is running

    # ------------------------------------------------------------------ #
    #  Platform detection
    # ------------------------------------------------------------------ #

    def _resolve_base(self) -> List[str]:
        """Return the base command list: ['tmux'] on Linux/Mac, ['wsl','tmux'] on Windows."""
        if platform.system() == "Windows":
            # Verify WSL + tmux are available
            probe = subprocess.run(
                ["wsl", "tmux", "-V"],
                capture_output=True,
                text=True,
            )
            if probe.returncode != 0:
                raise RuntimeError(
                    "TmuxManager requires WSL2 with tmux installed on Windows. "
                    "Install with: wsl -- sudo apt-get install -y tmux"
                )
            return ["wsl", "tmux"]
        return ["tmux"]

    # ------------------------------------------------------------------ #
    #  Internal helper
    # ------------------------------------------------------------------ #

    def _run(self, *args: str, check: bool = False) -> subprocess.CompletedProcess:
        cmd = self._base + list(args)
        logger.debug("tmux: %s", " ".join(cmd))
        return subprocess.run(cmd, capture_output=True, text=True, check=check)

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def is_alive(self) -> bool:
        """Return True if the tmux session exists."""
        result = self._run("has-session", "-t", self._session)
        return result.returncode == 0

    def start(self) -> None:
        """
        Create the tmux session, launch the agent, and (in a background thread)
        wait for startup then paste AGENT_LOOP.md into the pane.

        Returns immediately — caller must check `is_starting` or `is_alive()`.
        """
        if self.is_alive():
            logger.info("tmux session '%s' already running — skipping start", self._session)
            return

        workspace_str = str(self._workspace)
        if platform.system() == "Windows":
            # Convert Windows path to WSL path (e.g. C:\foo -> /mnt/c/foo)
            result = subprocess.run(
                ["wsl", "wslpath", workspace_str],
                capture_output=True, text=True,
            )
            workspace_str = result.stdout.strip() if result.returncode == 0 else workspace_str

        self._run("new-session", "-d", "-s", self._session, "-c", workspace_str)
        self._run("send-keys", "-t", self._session, self._agent_command, "Enter")
        logger.info(
            "tmux session '%s' created — running '%s', waiting %ds before sending loop file",
            self._session, self._agent_command, self._startup_wait,
        )

        self._starting = True
        t = threading.Thread(target=self._send_loop_file, daemon=True, name="tmux-startup")
        t.start()

    def _send_loop_file(self) -> None:
        """Background: sleep, send Ctrl+Y to accept any agent consent prompt, then paste AGENT_LOOP.md."""
        try:
            time.sleep(self._startup_wait)
            if not self.is_alive():
                logger.warning("tmux session '%s' died during startup wait", self._session)
                return

            # Send Ctrl+Y to accept agent consent / "Take control?" prompts
            self._run("send-keys", "-t", self._session, "C-y", "")
            time.sleep(0.5)

            loop_path = str(self._loop_file)
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["wsl", "wslpath", loop_path], capture_output=True, text=True
                )
                loop_path = result.stdout.strip() if result.returncode == 0 else loop_path

            self._run("load-buffer", loop_path)
            self._run("paste-buffer", "-t", self._session)
            self._run("send-keys", "-t", self._session, "", "Enter")
            logger.info("AGENT_LOOP.md pasted into tmux session '%s'", self._session)
        finally:
            self._starting = False

    def stop(self) -> None:
        """Send Ctrl-C three times then kill the session."""
        if not self.is_alive():
            return
        for _ in range(3):
            self._run("send-keys", "-t", self._session, "C-c", "")
        time.sleep(1)
        self._run("kill-session", "-t", self._session)
        logger.info("tmux session '%s' stopped", self._session)

    def restart(self) -> None:
        """Stop (if alive) then start fresh."""
        self.stop()
        time.sleep(1)
        self.start()

    def capture(self, lines: int = 30) -> List[str]:
        """Return the last `lines` lines of pane output."""
        if not self.is_alive():
            return []
        result = self._run("capture-pane", "-p", "-t", self._session, "-S", f"-{lines}")
        raw = result.stdout or ""
        return [l for l in raw.splitlines() if l.strip()]

    def status(self) -> dict:
        """Return a status dict suitable for the /api/session endpoint."""
        alive = self.is_alive()
        return {
            "alive": alive,
            "starting": self._starting,
            "session_name": self._session,
            "agent_command": self._agent_command,
            "workspace": str(self._workspace),
            "pane_lines": self.capture(30) if alive else [],
        }
