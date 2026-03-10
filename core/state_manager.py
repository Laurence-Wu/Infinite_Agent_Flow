"""
Thread-safe StateManager shared between the Flask web layer and the Planner.

All reads/writes are protected by threading.Lock() to prevent race
conditions when the Planner archives a task while Flask is reading state.
"""

from __future__ import annotations

import copy
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class TaskSnapshot:
    """Immutable snapshot of the engine state at a point in time."""
    current_card_id: Optional[str] = None
    current_workflow: Optional[str] = None
    current_version: Optional[str] = None
    current_instruction: Optional[str] = None
    current_loop_id: str = "main"
    card_index: int = 0
    total_cards: int = 0
    status: str = "idle"            # idle | running | completed | error | timeout
    started_at: Optional[str] = None
    last_updated: Optional[str] = None
    history: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None


class StateManager:
    """
    Central, thread-safe state container.

    Flask reads via get_snapshot() → acquires lock, returns a *copy*.
    Planner writes via set_*/update_* → acquires lock, mutates in-place.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._state = TaskSnapshot()

    # ------------------------------------------------------------------ #
    #  Read (Flask side)
    # ------------------------------------------------------------------ #

    def get_snapshot(self) -> Dict[str, Any]:
        """Return a dict copy of the current state (thread-safe)."""
        with self._lock:
            total = self._state.total_cards
            completed = len(self._state.history)
            cycles = completed // total if total > 0 else 0
            return {
                "current_card_id": self._state.current_card_id,
                "current_workflow": self._state.current_workflow,
                "current_version": self._state.current_version,
                "current_instruction": self._state.current_instruction,
                "card_index": self._state.card_index,
                "total_cards": self._state.total_cards,
                "progress_pct": self._progress_pct(),
                "completed_total": completed,
                "cycles_completed": cycles,
                "current_loop_id": self._state.current_loop_id,
                "status": self._state.status,
                "started_at": self._state.started_at,
                "last_updated": self._state.last_updated,
                "history": copy.deepcopy(self._state.history),
                "error": self._state.error,
            }

    # ------------------------------------------------------------------ #
    #  Write (Planner / Dealer side)
    # ------------------------------------------------------------------ #

    def set_current_card(
        self,
        card_id: str,
        workflow: str,
        version: str,
        instruction: str,
        card_index: int,
        total_cards: int,
        loop_id: str = "main",
    ) -> None:
        """Update the active card (called by Dealer after writing task file)."""
        with self._lock:
            self._state.current_card_id = card_id
            self._state.current_workflow = workflow
            self._state.current_version = version
            self._state.current_instruction = instruction
            self._state.current_loop_id = loop_id
            self._state.card_index = card_index
            self._state.total_cards = total_cards
            self._state.status = "running"
            self._state.started_at = datetime.now().isoformat()
            self._state.last_updated = self._state.started_at
            self._state.error = None

    def mark_completed(self, summary: str) -> None:
        """Archive the current card into history and reset active state."""
        with self._lock:
            now = datetime.now().isoformat()
            self._state.history.append({
                "card_id": self._state.current_card_id,
                "workflow": self._state.current_workflow,
                "version": self._state.current_version,
                "summary": summary,
                "completed_at": now,
            })
            self._state.status = "completed"
            self._state.last_updated = now

    def mark_error(self, error_msg: str) -> None:
        """Flag the current card as errored (e.g. timeout)."""
        with self._lock:
            self._state.status = "error"
            self._state.error = error_msg
            self._state.last_updated = datetime.now().isoformat()

    def set_idle(self) -> None:
        """Reset to idle (no active card)."""
        with self._lock:
            self._state.current_card_id = None
            self._state.current_instruction = None
            self._state.status = "idle"
            self._state.last_updated = datetime.now().isoformat()

    def set_workflow_finished(self) -> None:
        """Mark the entire workflow as done."""
        with self._lock:
            self._state.status = "workflow_finished"
            self._state.last_updated = datetime.now().isoformat()

    # ------------------------------------------------------------------ #
    #  Internal helpers
    # ------------------------------------------------------------------ #

    def _progress_pct(self) -> float:
        """Calculate progress as position within the current cycle (0-100%).
        Uses card_index, not history length, so circular loops stay in range."""
        if self._state.total_cards == 0:
            return 0.0
        return round((self._state.card_index / self._state.total_cards) * 100, 1)
