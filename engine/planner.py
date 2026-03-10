"""
CardsPlanner — Watchdog-based task monitor, archiver, and workflow advancer.

Watches current_task.md for the stop token using OS-native file events
(watchdog).  On detection: extracts summary, archives the task, appends
to master_summary.md, and advances to the next card via Picker → Dealer.

Includes a per-card timeout fallback to prevent indefinite hangs.
"""

from __future__ import annotations

import json
import logging
import random
import re
import shutil
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from watchdog.events import FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer

from core.config import EngineConfig
from core.exceptions import TaskFileError, TaskTimeoutError
from core.state_manager import StateManager

logger = logging.getLogger(__name__)

FRUIT_POOL: List[str] = [
    "apple", "banana", "cherry", "date", "elderberry",
    "fig", "grape", "honeydew", "kiwi", "lemon",
    "mango", "nectarine", "orange", "papaya", "quince",
    "raspberry", "starfruit", "tangerine", "ugli", "vanilla",
    "watermelon", "ximenia", "yellowfruit", "zucchini",
]


# ---------------------------------------------------------------------- #
#  Watchdog event handler
# ---------------------------------------------------------------------- #

class _TaskFileHandler(FileSystemEventHandler):
    """Watches for modifications to current_task.md."""

    def __init__(self, planner: "CardsPlanner"):
        super().__init__()
        self._planner = planner

    def on_modified(self, event):
        if event.is_directory:
            return
        # Only react to the specific task file
        src = Path(event.src_path).resolve()
        if src == self._planner.config.task_file.resolve():
            self._planner._on_task_file_changed()


# ---------------------------------------------------------------------- #
#  CardsPlanner
# ---------------------------------------------------------------------- #

class CardsPlanner:
    """
    Monitors the task file, archives completed tasks, and advances
    the workflow.  Runs in its own thread alongside Flask.
    """

    def __init__(
        self,
        config: EngineConfig,
        state: StateManager,
        picker,           # engine.picker.CardsPicker  (avoid circular import)
        dealer,           # engine.dealer.CardsDealer
    ):
        self.config = config
        self._state = state
        self._picker = picker
        self._dealer = dealer

        self._observer: Optional[Observer] = None
        self._timeout_timer: Optional[threading.Timer] = None
        self._stop_event = threading.Event()
        self._processing_lock = threading.Lock()  # Prevent duplicate handling
        self._ignoring_events = False              # Suppress during transitions

        # Track current card for archival
        self._current_card_id: Optional[str] = None
        self._current_workflow: Optional[str] = None
        self._current_version: Optional[str] = None
        self._current_loop_id: str = "main"
        # Maps loop_id → id of that loop's first card (used to detect cycle completion).
        self._first_card_id_per_loop: Dict[str, str] = {}
        self._first_card_id: Optional[str] = None  # kept for single-loop backward compat

        # Compiled forgiving stop-token regex
        self._stop_re = re.compile(config.stop_token_regex)

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def start_workflow(self, workflow_name: str, version: str) -> None:
        """
        Kick off a workflow: deal the first card and begin monitoring.
        """
        first_card = self._picker.get_first_card(workflow_name, version)
        total = self._picker.get_total_cards(workflow_name, version)
        idx = 0

        self._current_card_id = first_card.id
        self._current_workflow = workflow_name
        self._current_version = version
        self._current_loop_id = first_card.loop_id
        self._first_card_id = first_card.id  # backward compat

        # Build per-loop first-card registry from the loaded workflow.
        wf = self._picker.load_workflow(workflow_name, version)
        self._first_card_id_per_loop = {
            lid: cards[0].id for lid, cards in wf.loops.items()
        }

        self._dealer.deal_card(first_card, card_index=idx, total_cards=total)
        self._start_monitoring(first_card.max_time_seconds)
        logger.info("Workflow %s/%s started with card %s", workflow_name, version, first_card.id)

    def run(self, workflow_name: str, version: str) -> None:
        """
        Blocking entry point: starts the workflow and waits until
        all cards are processed or stop() is called.
        """
        self.start_workflow(workflow_name, version)
        self._stop_event.wait()
        self._cleanup()
        logger.info("Planner run loop exited.")

    def stop(self) -> None:
        """Signal the planner to shut down gracefully."""
        self._stop_event.set()

    # ------------------------------------------------------------------ #
    #  File monitoring
    # ------------------------------------------------------------------ #

    def _start_monitoring(self, max_time_seconds: Optional[int] = None) -> None:
        """Start the watchdog observer and optional timeout timer."""
        # Cancel any existing timer
        self._cancel_timeout()

        # Set up watchdog — create a fresh observer each cycle
        watch_dir = str(self.config.resolved_workspace)
        handler = _TaskFileHandler(self)

        # Mark old observer for stop (don't join — may be current thread)
        old_observer = self._observer
        if old_observer is not None:
            old_observer.stop()
            # Don't join here; old observer thread will exit on its own

        self._observer = Observer()
        self._observer.schedule(handler, watch_dir, recursive=False)
        self._observer.daemon = True
        self._observer.start()

        # Set up timeout
        timeout = max_time_seconds or self.config.default_timeout_seconds
        self._timeout_timer = threading.Timer(timeout, self._on_timeout)
        self._timeout_timer.daemon = True
        self._timeout_timer.start()

        logger.debug("Monitoring started (timeout=%ds)", timeout)

    def _on_task_file_changed(self) -> None:
        """Called by the watchdog handler when current_task.md is modified.
        Defers heavy work to a separate thread to avoid deadlock."""
        if self._ignoring_events:
            return  # Suppress events during card transitions

        try:
            content = self._dealer.read_current_task()
            if content is None:
                return
        except TaskFileError:
            return       # file might be mid-write; ignore transient errors

        if self._stop_re.search(content):
            if self._ignoring_events:
                return  # Flag set between file-read and here; discard
            # Defer to a new thread so the watchdog callback returns
            # immediately and we can safely stop/restart the observer.
            if self._processing_lock.acquire(blocking=False):
                self._ignoring_events = True  # Suppress immediately
                logger.info("Stop token detected in task file.")
                self._cancel_timeout()
                t = threading.Thread(
                    target=self._handle_completion_safe,
                    args=(content,),
                    daemon=True,
                )
                t.start()

    def _on_timeout(self) -> None:
        """Called when a card exceeds its time limit."""
        logger.warning(
            "Card %s timed out after limit.",
            self._current_card_id,
        )
        self._state.mark_error(
            f"Card '{self._current_card_id}' timed out. "
            "Check current_task.md for partial output."
        )
        # Try to advance anyway (treat as completed with error summary)
        content = self._dealer.read_current_task() or ""
        self._handle_completion(content, timed_out=True)

    # ------------------------------------------------------------------ #
    #  Task completion & archival
    # ------------------------------------------------------------------ #

    def _handle_completion_safe(self, content: str, timed_out: bool = False) -> None:
        """Thread-safe wrapper that releases the processing lock when done."""
        try:
            self._handle_completion(content, timed_out)
        finally:
            self._processing_lock.release()

    def _handle_completion(self, content: str, timed_out: bool = False) -> None:
        """Archive the finished task and advance to the next card."""
        summary = self._extract_summary(content, timed_out)
        self._ignoring_events = True  # Suppress events during transition
        self._archive_task(content, summary)
        self._state.mark_completed(summary)
        self._advance_workflow()
        time.sleep(0.5)  # Let stale watchdog events flush
        self._ignoring_events = False

    def _extract_summary(self, content: str, timed_out: bool = False) -> str:
        """
        Extract the agent's summary from the task content.
        Looks for text between a '## Summary' header and the stop token.
        Falls back to the last 5 non-empty lines if no header is found.
        """
        if timed_out:
            return f"[TIMEOUT] Card '{self._current_card_id}' did not complete in time."

        # Try to find a ## Summary section
        summary_match = re.search(
            r"##\s*[Ss]ummary\s*\n(.*?)(?=!\[|\Z)",
            content,
            re.DOTALL,
        )
        if summary_match:
            return summary_match.group(1).strip()

        # Fallback: last non-empty lines before stop token
        lines = [l.strip() for l in content.split("\n") if l.strip()]
        return "\n".join(lines[-5:]) if lines else "(no summary available)"

    def _archive_task(self, content: str, summary: str) -> None:
        """Move current_task.md to archive/ and append to master_summary.md."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        card_id = self._current_card_id or "unknown"
        archive_name = f"{card_id}_{timestamp}.md"
        archive_dest = self.config.archive_path / archive_name

        try:
            # Move task file to archive
            task_file = self.config.task_file
            if task_file.exists():
                shutil.move(str(task_file), str(archive_dest))
            else:
                # File was already moved or deleted; write content directly
                archive_dest.write_text(content, encoding="utf-8")

            # Append summary to master file
            master = self.config.master_summary_file
            entry = (
                f"\n## {card_id} — {self._current_workflow}/{self._current_version}\n"
                f"**Completed**: {datetime.now().isoformat()}\n\n"
                f"{summary}\n\n---\n"
            )
            with master.open("a", encoding="utf-8") as f:
                f.write(entry)

            logger.info("Archived %s to %s", card_id, archive_dest)

        except OSError as exc:
            logger.error("Archive failed: %s", exc)

    # ------------------------------------------------------------------ #
    #  Workflow advancement
    # ------------------------------------------------------------------ #

    def _advance_workflow(self) -> None:
        """Pick the next card and deal it, or finish the workflow."""
        if self._stop_event.is_set():
            return

        next_card = self._picker.get_next_card(
            self._current_workflow,
            self._current_version,
            self._current_card_id,
        )

        if next_card is None:
            logger.info("Workflow %s/%s completed!", self._current_workflow, self._current_version)
            self._state.set_workflow_finished()
            self._stop_event.set()
            return

        next_loop = next_card.loop_id
        is_cross_loop = (next_loop != self._current_loop_id)
        is_loop_complete = (
            not is_cross_loop
            and next_card.id == self._first_card_id_per_loop.get(self._current_loop_id)
        )

        if is_loop_complete:
            # Reshuffle only this loop's cards, leaving other loops untouched.
            new_first_id = self._reshuffle_card_names(
                self._current_workflow, self._current_version,
                loop_id=self._current_loop_id,
            )
            self._first_card_id_per_loop[self._current_loop_id] = new_first_id
            self._first_card_id = new_first_id  # backward compat
            # Reload the freshly-renamed first card of this loop.
            next_card = self._picker.get_loop_first_card(
                self._current_workflow, self._current_version,
                self._current_loop_id,
            )
        elif is_cross_loop:
            self._current_loop_id = next_loop
            logger.info("Cross-loop transition → loop '%s'", next_loop)

        total = self._picker.get_total_cards(self._current_workflow, self._current_version)
        idx = self._picker.get_card_index(self._current_workflow, self._current_version, next_card.id)

        # Stop old observer BEFORE writing the new card file,
        # so it doesn't catch the file-write event and false-trigger.
        if self._observer is not None:
            self._observer.stop()
            self._observer = None

        self._current_card_id = next_card.id
        self._dealer.deal_card(next_card, card_index=idx, total_cards=total)
        self._start_monitoring(next_card.max_time_seconds)

        logger.info("Advanced to card %s (%d/%d)", next_card.id, idx + 1, total)

    # ------------------------------------------------------------------ #
    #  Card name obfuscation
    # ------------------------------------------------------------------ #

    def _reshuffle_card_names(
        self, workflow_name: str, version: str, *, loop_id: str = "main"
    ) -> str:
        """
        Rename all card JSON files belonging to *loop_id* in the workflow
        version directory to a new set of randomly selected fruit names,
        updating the internal "id" and "next_card" pointers to match.
        Cards in other loops are left completely untouched.

        Invalidates the picker's in-memory cache so the renamed files are
        reloaded on the next access.

        Returns the new first card's ID (alphabetically first fruit name).
        """
        cache_key = f"{workflow_name}/{version}"
        wf = self._picker._workflows.get(cache_key)
        if wf is None:
            wf = self._picker.load_workflow(workflow_name, version)

        # Follow the next_card chain from this loop's first card.
        loop_first = wf.get_loop_first_card(loop_id)
        ordered = []
        visited: set = set()
        card = loop_first
        while card is not None and card.id not in visited:
            ordered.append(card)
            visited.add(card.id)
            if card.next_card is None:
                break
            try:
                next_c = wf.get_card(card.next_card)
                # Stop when we would re-enter the loop or cross into another loop.
                if next_c.id == loop_first.id or next_c.loop_id != loop_id:
                    break
                card = next_c
            except Exception:
                break

        n = len(ordered)
        # Pick n unique fruits; sort so alphabetical order == logical order.
        fruits = sorted(random.sample(FRUIT_POOL, n))

        old_ids = [c.id for c in ordered]
        mapping = {old_ids[i]: fruits[i] for i in range(n)}

        wf_dir = (
            self._picker._config.resolved_workflows / workflow_name / version
        )

        # Write new files first (safety: no data loss if something fails).
        for i, card in enumerate(ordered):
            new_id = fruits[i]
            new_next = fruits[(i + 1) % n]     # wraps back to fruits[0] for last card

            old_path = wf_dir / f"{card.id}.json"
            with old_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)

            data["id"] = new_id
            data["next_card"] = new_next

            new_path = wf_dir / f"{new_id}.json"
            with new_path.open("w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)

        # Delete old files (only after all new files are safely written).
        for card in ordered:
            old_path = wf_dir / f"{card.id}.json"
            if old_path.exists():
                old_path.unlink()

        # Invalidate picker cache so it reloads from the renamed files.
        self._picker._workflows.pop(cache_key, None)

        logger.info(
            "Reshuffled %s/%s: %s → %s",
            workflow_name, version, old_ids, fruits,
        )
        return fruits[0]

    # ------------------------------------------------------------------ #
    #  Cleanup
    # ------------------------------------------------------------------ #

    def _cancel_timeout(self) -> None:
        if self._timeout_timer is not None:
            self._timeout_timer.cancel()
            self._timeout_timer = None

    def _cleanup(self) -> None:
        """Stop observer and timer."""
        self._cancel_timeout()
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=2)
            self._observer = None
