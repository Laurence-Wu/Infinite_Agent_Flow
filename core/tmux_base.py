"""
Low-level tmux command layer.

Handles platform detection (Linux/macOS vs Windows/WSL), subprocess
execution, path conversion, session health checks, and pane capture.
All higher-level modules (TmuxDetector, TmuxManager) inherit from this.
"""
from __future__ import annotations

import logging
import platform
import subprocess
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


class TmuxBase:
    """Thin wrapper around tmux subprocess calls with cross-platform support."""

    def __init__(self, workspace: Path, session_name: str) -> None:
        self._workspace = Path(workspace).resolve()
        self._session   = session_name
        self._base      = self._resolve_base()

    # ------------------------------------------------------------------ #
    #  Platform detection
    # ------------------------------------------------------------------ #

    def _resolve_base(self) -> List[str]:
        """Return ['tmux'] on Linux/macOS, ['wsl', 'tmux'] on Windows."""
        if platform.system() == "Windows":
            probe = subprocess.run(
                ["wsl", "tmux", "-V"],
                capture_output=True,
                text=True,
            )
            if probe.returncode != 0:
                raise RuntimeError(
                    "TmuxManager requires WSL2 with tmux on Windows. "
                    "Install with: wsl -- sudo apt-get install -y tmux"
                )
            return ["wsl", "tmux"]
        return ["tmux"]

    # ------------------------------------------------------------------ #
    #  Path conversion
    # ------------------------------------------------------------------ #

    def _wsl_path(self, p: Path) -> str:
        """Convert a Windows path to a WSL path; no-op on Linux/macOS."""
        if platform.system() == "Windows":
            r = subprocess.run(
                ["wsl", "wslpath", str(p)],
                capture_output=True,
                text=True,
            )
            return r.stdout.strip() if r.returncode == 0 else str(p)
        return str(p)

    # ------------------------------------------------------------------ #
    #  Command execution
    # ------------------------------------------------------------------ #

    def _run(self, *args: str, check: bool = False) -> subprocess.CompletedProcess:
        cmd = self._base + list(args)
        logger.debug("tmux: %s", " ".join(cmd))
        return subprocess.run(cmd, capture_output=True, text=True, check=check)

    # ------------------------------------------------------------------ #
    #  Session queries
    # ------------------------------------------------------------------ #

    def is_alive(self) -> bool:
        """Return True if the tmux session exists."""
        return self._run("has-session", "-t", self._session).returncode == 0

    def capture(self, lines: int = 30) -> List[str]:
        """Return the last `lines` non-empty lines of pane output."""
        if not self.is_alive():
            return []
        result = self._run("capture-pane", "-p", "-t", self._session, "-S", f"-{lines}")
        return [l for l in (result.stdout or "").splitlines() if l.strip()]
