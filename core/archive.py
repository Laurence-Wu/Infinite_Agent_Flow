"""
ArchiveManager — structured, append-only archive of completed task cards.

Each completed card gets its own timestamped subdirectory:

    {workspace}/archive/{loop_id}/{alias}_{YYYYMMDD_HHMMSS}/
        task.md      — full current_task.md content at time of completion
        summary.md   — extracted ## Summary section (or last-5-lines fallback)
        logs.jsonl   — log lines captured during this card (one JSON string per line)
        meta.json    — card_id, alias, loop_id, workflow, version,
                       started_at, completed_at, agent_id

Invariants:
    - Never deletes any file.
    - Never overwrites (timestamp in folder name guarantees uniqueness).
    - write failures are silently swallowed (best-effort, never crash the engine).
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ArchiveManager:
    """Append-only archive manager per workspace."""

    def __init__(self, workspace: Path) -> None:
        self._root = workspace / "archive"
        self._root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def save_completed(
        self,
        alias: str,
        loop_id: str,
        task_content: str,
        log_lines: List[str],
        meta: Dict[str, Any],
    ) -> Optional[Path]:
        """Write a structured subdirectory for a completed card.

        Returns the path to the created directory, or None on I/O failure.
        The workflow JSON files in ``workflows/`` are never touched.
        """
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_alias = re.sub(r"[^\w-]", "_", alias)
        folder = self._root / loop_id / f"{safe_alias}_{ts}"

        try:
            folder.mkdir(parents=True, exist_ok=True)

            # 1. Full task content (agent's annotated instruction)
            (folder / "task.md").write_text(task_content, encoding="utf-8")

            # 2. Extracted summary (## Summary block or fallback)
            summary = _extract_summary(task_content)
            (folder / "summary.md").write_text(summary, encoding="utf-8")

            # 3. Log lines — one JSON-encoded string per line
            (folder / "logs.jsonl").write_text(
                "\n".join(json.dumps(line) for line in log_lines),
                encoding="utf-8",
            )

            # 4. Metadata
            (folder / "meta.json").write_text(
                json.dumps(meta, indent=2, default=str),
                encoding="utf-8",
            )

            logger.debug("Archived %s → %s", alias, folder)
            return folder

        except OSError as exc:
            logger.error("Archive write failed for %s: %s", alias, exc)
            return None

    def list_entries(
        self,
        loop_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Return metadata dicts for recent completions, newest first."""
        results: List[Dict[str, Any]] = []
        search_root = self._root / loop_id if loop_id else self._root
        if not search_root.exists():
            return results

        for meta_path in sorted(search_root.rglob("meta.json"), reverse=True):
            if len(results) >= limit:
                break
            try:
                data = json.loads(meta_path.read_text(encoding="utf-8"))
                data["_folder"] = str(meta_path.parent.relative_to(self._root))
                results.append(data)
            except (OSError, json.JSONDecodeError):
                continue

        return results

    def get_entry(self, loop_id: str, folder: str) -> Optional[Dict[str, Any]]:
        """Return all content for a specific archive entry by loop_id + folder name."""
        entry_path = self._root / loop_id / folder
        if not entry_path.is_dir():
            return None

        result: Dict[str, Any] = {"folder": folder, "loop_id": loop_id}

        for fname, key in [
            ("meta.json", "meta"),
            ("summary.md", "summary"),
            ("task.md", "task"),
        ]:
            fp = entry_path / fname
            if fp.exists():
                try:
                    raw = fp.read_text(encoding="utf-8")
                    result[key] = json.loads(raw) if fname.endswith(".json") else raw
                except (OSError, json.JSONDecodeError):
                    pass

        logs_path = entry_path / "logs.jsonl"
        if logs_path.exists():
            try:
                result["log_lines"] = [
                    json.loads(line)
                    for line in logs_path.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
            except (OSError, json.JSONDecodeError):
                result["log_lines"] = []

        return result


# ------------------------------------------------------------------ #
#  Module-level helpers (reused by planner._extract_summary too)
# ------------------------------------------------------------------ #

def extract_summary(content: str) -> str:
    """Extract the ## Summary section from task content.

    The instruction template itself contains a placeholder ## Summary block,
    so we take the LAST match — which is the one the agent actually wrote.
    Falls back to the last 5 non-empty lines if no header is found.
    Exported so ``CardsPlanner`` can reuse the same logic.
    """
    matches = list(re.finditer(r"##\s*[Ss]ummary\s*\n(.*?)(?=!\[|\Z)", content, re.DOTALL))
    if matches:
        return matches[-1].group(1).strip()
    lines = [ln.strip() for ln in content.split("\n") if ln.strip()]
    return "\n".join(lines[-5:]) if lines else "(no summary)"


# Private alias used within this module
_extract_summary = extract_summary
