"""
WorkspaceScanner — scans the engine workspace for recent file activity.

Excludes:
  - The archive subdirectory (finished task files)
  - Hidden directories (.git, .claude, etc.)
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from core.config import EngineConfig


class WorkspaceScanner:
    """
    Scans workspace_path for recently modified files.

    Usage:
        scanner = WorkspaceScanner(config)
        files = scanner.scan(max_files=20)
    """

    def __init__(self, config: EngineConfig) -> None:
        self._workspace = config.resolved_workspace
        self._archive   = config.resolved_workspace / config.archive_dir

    def scan(self, max_files: int = 20) -> list[dict]:
        """
        Return up to max_files recently modified files, newest first.

        Each entry: {"path": str, "mtime": ISO-8601 str, "size": int bytes}
        """
        results: list[dict] = []

        for entry in self._workspace.rglob("*"):
            if self._should_skip(entry):
                continue
            try:
                stat = entry.stat()
            except OSError:
                continue

            mtime_dt = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
            results.append({
                "path":  entry.relative_to(self._workspace).as_posix(),
                "mtime": mtime_dt.isoformat(),
                "size":  stat.st_size,
            })

        results.sort(key=lambda f: f["mtime"], reverse=True)
        return results[:max_files]

    def _should_skip(self, entry: Path) -> bool:
        """Return True if this path should be excluded from scan results."""
        if entry.is_dir():
            return True

        # Exclude archive subtree
        if entry.is_relative_to(self._archive):
            return True

        # Exclude hidden directories (.git, .claude, etc.)
        parts = entry.relative_to(self._workspace).parts
        return any(p.startswith(".") for p in parts)
