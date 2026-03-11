"""
CardsPlanner \u2014 Watchdog-based task monitor, archiver, and workflow advancer.

Watches current_task.md for the ![next]! token using OS-native file events
(watchdog).  On detection: extracts summary, archives the task, appends
to master_summary.md, and advances to the next card via Picker \u2192 Dealer.
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
from core.exceptions import TaskFileError, WorkflowValidationError
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
        self._stop_event = threading.Event()
        self._processing_lock = threading.Lock()  # Prevent duplicate handling
        self._ignoring_events = False              # Suppress during transitions

        # Track current card for archival
        self._current_card_id: Optional[str] = None
        self._current_workflow: Optional[str] = None
        self._current_version: Optional[str] = None
        self._current_loop_id: str = "main"
        # Maps loop_id \u2192 id of that loop's first card (used to detect cycle completion).
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
        wf = self._picker.load_workflow(workflow_name, version)
        first_card = wf.first_card
        aliased_first = wf.get_aliased_card(first_card.id)
        total = wf.total_cards
        idx = 0

        self._current_card_id = first_card.id
        self._current_workflow = workflow_name
        self._current_version = version
        self._current_loop_id = first_card.loop_id
        self._first_card_id = first_card.id  # backward compat

        # Build per-loop first-card registry from the loaded workflow.
        self._first_card_id_per_loop = {
            lid: cards[0].id for lid, cards in wf.loops.items()
        }

        self._dealer.deal_card(aliased_first, card_index=idx, total_cards=total)
        self._start_monitoring()
        logger.info("Workflow %s/%s started with card %s", workflow_name, version, first_card.id)

    def run(self, workflow_name: str, version: str) -> None:
        """
        Blocking entry point: starts the workflow and waits until
        all cards are processed or stop() is called.

        Uses a polling loop with a short timeout so that Ctrl+C
        (SIGINT / KeyboardInterrupt) is reliably received on Windows.
        """
        self.start_workflow(workflow_name, version)
        try:
            while not self._stop_event.is_set():
                self._stop_event.wait(timeout=0.5)
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received \u2014 shutting down.")
        finally:
            self._cleanup()
            logger.info("Planner run loop exited.")

    def stop(self) -> None:
        """Signal the planner to shut down gracefully."""
        self._stop_event.set()

    # ------------------------------------------------------------------ #
    #  File monitoring
    # ------------------------------------------------------------------ #

    def _start_monitoring(self) -> None:
        """Start the watchdog observer for the workspace directory."""
        watch_dir = str(self.config.resolved_workspace)
        handler = _TaskFileHandler(self)

        old_observer = self._observer
        if old_observer is not None:
            old_observer.stop()

        self._observer = Observer()
        self._observer.schedule(handler, watch_dir, recursive=False)
        self._observer.daemon = True
        self._observer.start()

        logger.debug("Monitoring started \u2014 waiting for ![next]!")

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
                logger.info("![next]! detected \u2014 advancing workflow.")
                t = threading.Thread(
                    target=self._handle_completion_safe,
                    args=(content,),
                    daemon=True,
                )
                t.start()

    # ------------------------------------------------------------------ #
    #  Task completion & archival
    # ------------------------------------------------------------------ #

    def _handle_completion_safe(self, content: str) -> None:
        """Thread-safe wrapper that releases the processing lock when done.
        On unhandled exception, signals the main loop to exit so the process
        does not hang indefinitely."""
        try:
            self._handle_completion(content)
        except Exception as exc:
            logger.error("Fatal error in completion handler: %s", exc, exc_info=True)
            self._stop_event.set()   # unblock run() so Ctrl+C / restart works
            raise
        finally:
            self._processing_lock.release()

    def _handle_completion(self, content: str) -> None:
        """Archive the finished task and advance to the next card."""
        summary = self._extract_summary(content)
        self._ignoring_events = True  # Suppress events during transition
        self._archive_task(content, summary)
        self._state.mark_completed(summary)
        self._advance_workflow()
        time.sleep(0.5)  # Let stale watchdog events flush
        self._ignoring_events = False

    def _extract_summary(self, content: str) -> str:
        """
        Extract the agent's summary from the task content.
        Looks for text between a '## Summary' header and the ![next]! token.
        Falls back to the last 5 non-empty lines if no header is found.
        """
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
        # Use alias for filename if it exists
        wf = self._picker.load_workflow(self._current_workflow, self._current_version)
        alias = wf.alias_map.get(card_id, card_id)
        archive_name = f"{alias}_{timestamp}.md"
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
                f"\n## {alias} ({card_id}) \u2014 {self._current_workflow}/{self._current_version}\n"
                f"**Completed**: {datetime.now().isoformat()}\n\n"
                f"{summary}\n\n---\n"
            )
            with master.open("a", encoding="utf-8") as f:
                f.write(entry)

            logger.info("Archived %s to %s", alias, archive_dest)

        except OSError as exc:
            logger.error("Archive failed: %s", exc)

    # ------------------------------------------------------------------ #
    #  Workflow advancement
    # ------------------------------------------------------------------ #

    def _advance_workflow(self) -> None:
        """Pick the next card and deal it, or finish the workflow."""
        if self._stop_event.is_set():
            return

        wf = self._picker.load_workflow(self._current_workflow, self._current_version)
        current_card = wf.get_card(self._current_card_id)
        next_card_id = current_card.next_card

        if next_card_id is None:
            logger.info("Workflow %s/%s completed!", self._current_workflow, self._current_version)
            self._state.set_workflow_finished()
            self._stop_event.set()
            return

        # Resolve next card object (could be an alias or internal ID)
        next_card_obj = wf.get_card(next_card_id)
        
        next_loop = next_card_obj.loop_id
        is_cross_loop = (next_loop != self._current_loop_id)
        is_loop_complete = (
            not is_cross_loop
            and next_card_obj.id == self._first_card_id_per_loop.get(self._current_loop_id)
        )

        if is_loop_complete:
            # Reshuffle only this loop's cards in memory.
            new_first_internal_id = self._reshuffle_card_names(
                self._current_workflow, self._current_version,
                loop_id=self._current_loop_id,
            )
            self._first_card_id_per_loop[self._current_loop_id] = new_first_internal_id
            self._first_card_id = new_first_internal_id  # backward compat
            # Resolve the new aliased version of the loop start
            aliased_next = wf.get_aliased_card(new_first_internal_id)
        else:
            if is_cross_loop:
                self._current_loop_id = next_loop
                logger.info("Cross-loop transition \u2192 loop '%s'", next_loop)
            aliased_next = wf.get_aliased_card(next_card_obj.id)

        total = wf.total_cards
        idx = wf.card_index(aliased_next.id)

        # Stop old observer BEFORE writing the new card file
        if self._observer is not None:
            self._observer.stop()
            self._observer = None

        self._current_card_id = aliased_next.id
        self._dealer.deal_card(aliased_next, card_index=idx, total_cards=total)
        self._start_monitoring()

        logger.info("Advanced to card %s (%d/%d)", aliased_next.id, idx + 1, total)

    # ------------------------------------------------------------------ #
    #  Card name obfuscation
    # ------------------------------------------------------------------ #

    def _reshuffle_card_names(
        self, workflow_name: str, version: str, *, loop_id: str = "main"
    ) -> str:
        """
        Assign a new set of randomly selected fruit names as aliases for
        all cards in *loop_id*. Original files on disk are UNCHANGED.

        Returns the internal ID of the first card in the loop.
        """
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
        # Collect alias names owned by OTHER loops so we never reuse them.
        other_loop_aliases: set = set()
        for lid, loop_cards in wf.loops.items():
            if lid != loop_id:
                for c in loop_cards:
                    alias = wf.alias_map.get(c.id)
                    if alias:
                        other_loop_aliases.add(alias)

        available = [f for f in FRUIT_POOL if f not in other_loop_aliases]
        if len(available) < n:
            raise WorkflowValidationError(
                workflow=workflow_name,
                detail=(
                    f"Fruit pool exhausted: need {n} names for loop '{loop_id}' "
                    f"but only {len(available)} are free. "
                    f"Expand FRUIT_POOL or reduce loop size."
                ),
            )
        # Pick n unique fruits; sort so alphabetical order == logical order.
        fruits = sorted(random.sample(available, n))

        # Update the workflow's in-memory alias map
        new_aliases = {ordered[i].id: fruits[i] for i in range(n)}
        wf.set_loop_aliases(loop_id, new_aliases)

        logger.info(
            "Reshuffled %s/%s loop '%s' in memory: %s \u2192 %s",
            workflow_name, version, loop_id, 
            [c.id for c in ordered], fruits,
        )
        return ordered[0].id

    # ------------------------------------------------------------------ #
    #  Cleanup
    # ------------------------------------------------------------------ #

    def _cleanup(self) -> None:
        """Stop the watchdog observer."""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=2)
            self._observer = None
