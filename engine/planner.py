"""
CardsPlanner — Watchdog-based task monitor, archiver, and workflow advancer.

Watches current_task.md for the stop token using OS-native file events
(watchdog).  On detection: extracts branch label, archives the task to
the structured archive, advances to the next card via Picker → Dealer.

Branching
---------
Cards declare named exits in their ``branches`` dict:
    "branches": {"approved": "card_05", "needs_rework": "card_03"}

The agent signals which exit to take by appending the label to the token:
    ![next:approved]!       → routes to card_05
    ![next]!                → uses card's default ``next_card``

Pause / Resume
--------------
``pause()`` / ``resume()`` / ``is_paused()`` are fully implemented via a
threading.Event.  The planner blocks in ``_handle_completion`` before
advancing so already-in-flight cards always finish cleanly.
"""

from __future__ import annotations

import logging
import random
import re
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from core.config import EngineConfig
from core.exceptions import TaskFileError, WorkflowValidationError
from core.state_manager import StateManager
from engine.picker import WorkflowIdentifier

logger = logging.getLogger(__name__)

FRUIT_POOL: List[str] = [
    "apple", "banana", "cherry", "date", "elderberry",
    "fig", "grape", "honeydew", "kiwi", "lemon",
    "mango", "nectarine", "orange", "papaya", "quince",
    "raspberry", "starfruit", "tangerine", "ugli", "vanilla",
    "watermelon", "ximenia", "yellowfruit", "zucchini",
]

# Matches:  ![next]!   or   ![next:some_label]!
# Must be the only non-whitespace content on its line.
_STOP_RE = re.compile(r"(?m)^!\[next(?::(\w+))?\]!\s*$")


def _parse_branch_label(content: str) -> Optional[str]:
    """Return the branch label from the stop token, or None (use default)."""
    m = _STOP_RE.search(content)
    if not m:
        return None
    return m.group(1)  # e.g. "approved" or None


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
        picker,            # engine.picker.CardsPicker
        dealer,            # engine.dealer.CardsDealer
        agent_id: str = "default",
    ):
        self.config = config
        self._state = state
        self._picker = picker
        self._dealer = dealer
        self._agent_id = agent_id

        self._observer: Optional[Observer] = None
        self._stop_event = threading.Event()
        self._processing_lock = threading.Lock()
        self._ignoring_events = False

        # Pause support — set = not paused (clear = paused)
        self._paused_event = threading.Event()
        self._paused_event.set()

        # Current card tracking
        self._current_card_id: Optional[str] = None
        self._current_workflow: Optional[str] = None
        self._current_version: Optional[str] = None
        self._current_loop_id: str = "main"
        self._card_started_at: Optional[str] = None

        # Per-loop first-card registry (for loop-cycle detection)
        self._first_card_id_per_loop: Dict[str, str] = {}
        self._first_card_id: Optional[str] = None

        self._stop_re = _STOP_RE

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def start_workflow(self, workflow_name: str, version: str) -> None:
        """Kick off a workflow: deal the first card and begin monitoring."""
        wf = self._picker.load_workflow((workflow_name, version))
        first_card = wf.first_card
        aliased_first = wf.get_aliased_card(first_card.id)
        total = wf.total_cards

        self._current_card_id = first_card.id
        self._current_workflow = workflow_name
        self._current_version = version
        self._current_loop_id = first_card.loop_id
        self._first_card_id = first_card.id
        self._card_started_at = datetime.now().isoformat()

        self._first_card_id_per_loop = {
            lid: cards[0].id for lid, cards in wf.loops.items()
        }

        self._dealer.deal_card(aliased_first, card_index=0, total_cards=total)
        self._start_monitoring()
        logger.info(
            "Workflow %s/%s started with card %s (agent=%s)",
            workflow_name, version, first_card.id, self._agent_id,
        )

    def run(self, workflow_name: str, version: str) -> None:
        """Blocking entry point: start workflow and wait until done or stopped."""
        self.start_workflow(workflow_name, version)
        try:
            while not self._stop_event.is_set():
                self._stop_event.wait(timeout=0.5)
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt — shutting down.")
        finally:
            self._cleanup()
            logger.info("Planner run loop exited (agent=%s).", self._agent_id)

    def stop(self) -> None:
        """Signal the planner to shut down gracefully."""
        self._stop_event.set()
        self._paused_event.set()   # unblock any waiting _handle_completion

    def pause(self) -> None:
        """Pause before advancing to the next card after the current one completes."""
        self._paused_event.clear()
        logger.info("Planner paused (agent=%s).", self._agent_id)

    def resume(self) -> None:
        """Resume a paused planner."""
        self._paused_event.set()
        logger.info("Planner resumed (agent=%s).", self._agent_id)

    def is_paused(self) -> bool:
        return not self._paused_event.is_set()

    # ------------------------------------------------------------------ #
    #  File monitoring
    # ------------------------------------------------------------------ #

    def _start_monitoring(self) -> None:
        watch_dir = str(self.config.resolved_workspace)
        handler = _TaskFileHandler(self)

        if self._observer is not None:
            self._observer.stop()

        self._observer = Observer()
        self._observer.schedule(handler, watch_dir, recursive=False)
        self._observer.daemon = True
        self._observer.start()
        logger.debug("Monitoring started — waiting for ![next]! (agent=%s)", self._agent_id)

    def _on_task_file_changed(self) -> None:
        """Called by watchdog when current_task.md is modified."""
        if self._ignoring_events:
            return

        try:
            content = self._dealer.read_current_task()
            if content is None:
                return
        except TaskFileError:
            return

        if self._stop_re.search(content):
            if self._ignoring_events:
                return
            if self._processing_lock.acquire(blocking=False):
                self._ignoring_events = True
                label = _parse_branch_label(content) or "default"
                logger.info(
                    "![next%s]! detected — advancing workflow (agent=%s).",
                    f":{label}" if label != "default" else "",
                    self._agent_id,
                )
                t = threading.Thread(
                    target=self._handle_completion_safe,
                    args=(content,),
                    daemon=True,
                )
                t.start()

    # ------------------------------------------------------------------ #
    #  Task completion, archival, and advancement
    # ------------------------------------------------------------------ #

    def _handle_completion_safe(self, content: str) -> None:
        try:
            self._handle_completion(content)
        except Exception as exc:
            logger.error(
                "Fatal error in completion handler (agent=%s): %s",
                self._agent_id, exc, exc_info=True,
            )
            self._stop_event.set()
            raise
        finally:
            self._processing_lock.release()

    def _handle_completion(self, content: str) -> None:
        """Archive the finished task and advance to the next card."""
        from core.archive import extract_summary

        self._ignoring_events = True
        summary = extract_summary(content)

        # Archive to structured subdirectory
        self._archive_task(content, summary)

        # Update state
        self._state.mark_completed(summary, agent_id=self._agent_id)

        # Honour pause — block here (not mid-card)
        self._paused_event.wait()

        if not self._stop_event.is_set():
            branch_label = _parse_branch_label(content)
            self._advance_workflow(branch_label=branch_label)

        time.sleep(0.5)   # flush stale watchdog events
        self._ignoring_events = False

    def _archive_task(self, content: str, summary: str) -> None:
        """Delegate archival to dealer's ArchiveManager, or fall back to flat file."""
        card_id = self._current_card_id or "unknown"
        wf = self._picker.load_workflow((self._current_workflow, self._current_version))
        alias = wf.alias_map.get(card_id, card_id)

        # Capture log lines for this card's execution window
        snap = self._state.get_snapshot(self._agent_id)
        log_lines: List[str] = list(snap.get("log_lines", []))

        meta = {
            "card_id": card_id,
            "alias": alias,
            "loop_id": self._current_loop_id,
            "workflow": self._current_workflow,
            "version": self._current_version,
            "agent_id": self._agent_id,
            "started_at": self._card_started_at,
            "completed_at": datetime.now().isoformat(),
        }

        archive_mgr = getattr(self._dealer, "_archive", None)
        if archive_mgr is not None:
            archive_mgr.save_completed(
                alias=alias,
                loop_id=self._current_loop_id,
                task_content=content,
                log_lines=log_lines,
                meta=meta,
            )
        else:
            # Fallback: write flat .md to archive dir (backward compat)
            self._archive_task_flat(content, alias)

        # Always append to master_summary.md for backward compat
        self._append_master_summary(alias, card_id, summary)

    def _archive_task_flat(self, content: str, alias: str) -> None:
        """Legacy flat-file archive (used when no ArchiveManager is injected)."""
        import shutil
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_dest = self.config.archive_path / f"{alias}_{timestamp}.md"
        try:
            task_file = self.config.task_file
            if task_file.exists():
                shutil.move(str(task_file), str(archive_dest))
            else:
                archive_dest.write_text(content, encoding="utf-8")
            logger.info("Archived (flat) %s → %s", alias, archive_dest)
        except OSError as exc:
            logger.error("Flat archive failed: %s", exc)

    def _append_master_summary(self, alias: str, card_id: str, summary: str) -> None:
        """Append a one-line entry to archive/master_summary.md."""
        master = self.config.master_summary_file
        entry = (
            f"\n## {alias} ({card_id}) — {self._current_workflow}/{self._current_version}\n"
            f"**Agent**: {self._agent_id}  "
            f"**Completed**: {datetime.now().isoformat()}\n\n"
            f"{summary}\n\n---\n"
        )
        try:
            with master.open("a", encoding="utf-8") as f:
                f.write(entry)
        except OSError as exc:
            logger.error("master_summary write failed: %s", exc)

    # ------------------------------------------------------------------ #
    #  Workflow advancement with branching
    # ------------------------------------------------------------------ #

    def _advance_workflow(self, branch_label: Optional[str] = None) -> None:
        """Pick the next card (honouring branch label) and deal it."""
        if self._stop_event.is_set():
            return

        wf = self._picker.load_workflow((self._current_workflow, self._current_version))
        current_card = wf.get_card(self._current_card_id)

        # resolve_next uses branch label first, falls back to next_card
        next_card_id = current_card.resolve_next(branch_label)

        if next_card_id is None:
            logger.info(
                "Workflow %s/%s completed! (agent=%s)",
                self._current_workflow, self._current_version, self._agent_id,
            )
            self._state.set_workflow_finished(agent_id=self._agent_id)
            self._stop_event.set()
            return

        if branch_label and branch_label in current_card.branches:
            logger.info(
                "Branch '%s' taken → %s (agent=%s)",
                branch_label, next_card_id, self._agent_id,
            )

        next_card_obj = wf.get_card(next_card_id)
        next_loop = next_card_obj.loop_id
        is_cross_loop = (next_loop != self._current_loop_id)
        is_loop_complete = (
            not is_cross_loop
            and next_card_obj.id == self._first_card_id_per_loop.get(self._current_loop_id)
        )

        if is_loop_complete:
            new_first = self._reshuffle_card_names(
                (self._current_workflow, self._current_version),
                loop_id=self._current_loop_id,
            )
            self._first_card_id_per_loop[self._current_loop_id] = new_first
            self._first_card_id = new_first
            aliased_next = wf.get_aliased_card(new_first)
        else:
            if is_cross_loop:
                self._current_loop_id = next_loop
                logger.info("Cross-loop transition → loop '%s'", next_loop)
            aliased_next = wf.get_aliased_card(next_card_obj.id)

        total = wf.total_cards
        idx = wf.card_index(aliased_next.id)

        if self._observer is not None:
            self._observer.stop()
            self._observer = None

        self._current_card_id = aliased_next.id
        self._card_started_at = datetime.now().isoformat()
        self._dealer.deal_card(aliased_next, card_index=idx, total_cards=total)
        self._start_monitoring()

        logger.info(
            "Advanced to card %s (%d/%d) (agent=%s)",
            aliased_next.id, idx + 1, total, self._agent_id,
        )

    # ------------------------------------------------------------------ #
    #  Card name obfuscation
    # ------------------------------------------------------------------ #

    def _reshuffle_card_names(
        self, identifier: WorkflowIdentifier, *, loop_id: str = "main"
    ) -> str:
        """Assign new fruit aliases for all cards in loop_id in memory.
        Workflow JSON files on disk are never touched.
        Returns the internal ID of the first card in the loop.
        """
        wf = self._picker.load_workflow(identifier)
        workflow_name = identifier[0]

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
                if next_c.id == loop_first.id or next_c.loop_id != loop_id:
                    break
                card = next_c
            except Exception:
                break

        n = len(ordered)
        other_aliases: set = set()
        for lid, loop_cards in wf.loops.items():
            if lid != loop_id:
                for c in loop_cards:
                    alias = wf.alias_map.get(c.id)
                    if alias:
                        other_aliases.add(alias)

        available = [f for f in FRUIT_POOL if f not in other_aliases]
        if len(available) < n:
            raise WorkflowValidationError(
                workflow=workflow_name,
                detail=(
                    f"Fruit pool exhausted: need {n} names for loop '{loop_id}' "
                    f"but only {len(available)} are free."
                ),
            )

        fruits = sorted(random.sample(available, n))
        new_aliases = {ordered[i].id: fruits[i] for i in range(n)}
        wf.set_loop_aliases(loop_id, new_aliases)

        logger.info(
            "Reshuffled loop '%s': %s → %s",
            loop_id, [c.id for c in ordered], fruits,
        )
        return ordered[0].id

    # ------------------------------------------------------------------ #
    #  Cleanup
    # ------------------------------------------------------------------ #

    def _cleanup(self) -> None:
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=2)
            self._observer = None
