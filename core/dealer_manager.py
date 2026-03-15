"""
DealerRegistry — manages multiple independent CardsPlanner instances.

A "dealer" is the CardDealer workflow runner: planner + picker + dealer + state.
It writes current_task.md and waits for the AI agent to complete each card.

The AI agent (Gemini, Claude, etc.) runs separately in a tmux session — see
core/tmux_manager.py and /api/agent endpoints.

All dealers share a single HookManager so their states accumulate and appear
together on the dashboard.

A background health-monitor thread checks every 60 s for stuck dealers
(running status with no state update for > 20 min) and logs a warning.
"""

from __future__ import annotations

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.decorators import locked, log_call

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------- #
#  DealerEntry — thin wrapper around DealerStack for registry bookkeeping
# ---------------------------------------------------------------------- #

@dataclass
class DealerEntry:
    """All components that belong to a single running Card Dealer instance."""
    dealer_id: str
    workspace: str
    workflow: str
    version: str
    state: Any     # StateManager
    planner: Any   # CardsPlanner
    dealer: Any    # CardsDealer
    picker: Any    # CardsPicker
    archive: Any   # ArchiveManager
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())


# ---------------------------------------------------------------------- #
#  DealerRegistry
# ---------------------------------------------------------------------- #

class DealerRegistry:
    """
    Thread-safe registry of DealerEntry instances.

    Usage:
    1. Instantiate once in orchestrator.py, passing the shared HookManager.
    2. Call ``register_stack()`` for the main (pre-started) dealer.
    3. Call ``start_dealer()`` to spawn additional dealers from the web UI.
    4. Inject this registry into DashboardRouter so control endpoints work.
    """

    _MAX_DEALERS = 10

    def __init__(self, hook_manager: Any, workflows_path: str) -> None:
        self._hook_manager = hook_manager
        self._workflows_path = workflows_path
        self._dealers: Dict[str, DealerEntry] = {}
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(
            max_workers=self._MAX_DEALERS,
            thread_name_prefix="dealer",
        )
        # Per-dealer tmux: either a live TmuxManager object (primary agent)
        # or a cached status dict pushed by remote attached agents.
        self._tmux_managers: Dict[str, Any] = {}          # dealer_id → TmuxManager
        self._tmux_cache: Dict[str, Dict] = {}            # dealer_id → status snapshot
        self._start_health_monitor()

    # ------------------------------------------------------------------ #
    #  Registration
    # ------------------------------------------------------------------ #

    @locked()
    def register_stack(self, stack: Any) -> None:
        """Register a pre-built DealerStack (e.g. the main dealer from orchestrator)."""
        entry = DealerEntry(
            dealer_id=stack.agent_id,
            workspace=str(stack.config.resolved_workspace),
            workflow=getattr(stack, "workflow", "unknown"),
            version=getattr(stack, "version", "v1"),
            state=stack.state,
            planner=stack.planner,
            dealer=stack.dealer,
            picker=stack.picker,
            archive=stack.archive,
        )
        self._dealers[stack.agent_id] = entry
        logger.info("Registered dealer %s (workspace=%s)", stack.agent_id, entry.workspace)

    @locked()
    def register(
        self,
        dealer_id: str,
        planner: Any,
        state: Any,
        dealer: Any,
        picker: Any,
        workspace: str,
        workflow: str,
        version: str,
        archive: Any = None,
    ) -> None:
        """Register individual components (backward-compat with old orchestrator code)."""
        entry = DealerEntry(
            dealer_id=dealer_id,
            workspace=workspace,
            workflow=workflow,
            version=version,
            state=state,
            planner=planner,
            dealer=dealer,
            picker=picker,
            archive=archive,
        )
        self._dealers[dealer_id] = entry
        logger.info("Registered dealer %s (workspace=%s)", dealer_id, workspace)

    # ------------------------------------------------------------------ #
    #  Dealer lifecycle
    # ------------------------------------------------------------------ #

    def start_dealer(self, workspace: str, workflow: str, version: str,
                     dealer_id: Optional[str] = None) -> str:
        """Spawn a new independent dealer in the thread pool. Returns dealer_id."""
        from core.dealer_factory import build_dealer_stack

        with self._lock:
            if dealer_id is None:
                dealer_id = f"dealer_{len(self._dealers)}"

        stack = build_dealer_stack(
            workspace=workspace,
            workflow=workflow,
            version=version,
            dealer_id=dealer_id,
            hook_manager=self._hook_manager,
            workflows_path=self._workflows_path,
        )

        entry = DealerEntry(
            dealer_id=dealer_id,
            workspace=workspace,
            workflow=workflow,
            version=version,
            state=stack.state,
            planner=stack.planner,
            dealer=stack.dealer,
            picker=stack.picker,
            archive=stack.archive,
        )
        with self._lock:
            self._dealers[dealer_id] = entry

        self._executor.submit(self._run_dealer, dealer_id, workflow, version)
        logger.info("Started dealer %s on workspace=%s workflow=%s", dealer_id, workspace, workflow)
        return dealer_id

    @locked()
    def stop_dealer(self, dealer_id: str) -> bool:
        entry = self._dealers.get(dealer_id)
        if entry is None:
            logger.warning("stop_dealer: unknown dealer %s", dealer_id)
            return False
        entry.planner.stop()
        del self._dealers[dealer_id]
        logger.info("Stopped dealer %s", dealer_id)
        return True

    @locked()
    def pause_dealer(self, dealer_id: str) -> bool:
        entry = self._dealers.get(dealer_id)
        if entry is None:
            logger.warning("pause_dealer: unknown dealer %s", dealer_id)
            return False
        entry.planner.pause()
        return True

    @locked()
    def resume_dealer(self, dealer_id: str) -> bool:
        entry = self._dealers.get(dealer_id)
        if entry is None:
            logger.warning("resume_dealer: unknown dealer %s", dealer_id)
            return False
        entry.planner.resume()
        return True

    def deal_next(self, dealer_id: str = "default") -> Dict[str, Any]:
        """Manually advance one card for the given dealer."""
        entry = self._get(dealer_id)
        if entry is None:
            return {"ok": False, "error": f"unknown dealer: {dealer_id}"}

        snap = entry.state.get_snapshot(dealer_id)
        current_id = snap.get("current_card_id")

        try:
            if current_id is None:
                card = entry.picker.get_first_card((entry.workflow, entry.version))
            else:
                card = entry.picker.get_next_card((entry.workflow, entry.version), current_id)

            if card is None:
                return {"ok": False, "error": "workflow finished — no next card"}

            total = entry.picker.get_total_cards((entry.workflow, entry.version))
            idx = entry.picker.get_card_index((entry.workflow, entry.version), card.id)
            entry.dealer.deal_card(card, card_index=idx, total_cards=total)
            return {"ok": True, "dealer_id": dealer_id, "card_id": card.id}
        except Exception as exc:
            logger.error("deal_next failed for dealer %s: %s", dealer_id, exc)
            return {"ok": False, "error": str(exc)}

    # ------------------------------------------------------------------ #
    #  Per-dealer tmux access
    # ------------------------------------------------------------------ #

    def register_tmux(self, dealer_id: str, tmux_manager: Any) -> None:
        """Register a live TmuxManager for the primary agent."""
        with self._lock:
            self._tmux_managers[dealer_id] = tmux_manager

    def update_pane_cache(self, dealer_id: str, status: Dict) -> None:
        """Store a tmux status snapshot pushed by an attached (remote) agent."""
        with self._lock:
            self._tmux_cache[dealer_id] = status

    def get_tmux_status(self, dealer_id: str) -> Optional[Dict]:
        """Return tmux status for a dealer — live if TmuxManager present, else cached."""
        with self._lock:
            mgr = self._tmux_managers.get(dealer_id)
            if mgr is not None:
                return mgr.status()
            return self._tmux_cache.get(dealer_id)

    def get_tmux_manager(self, dealer_id: str) -> Optional[Any]:
        """Return the live TmuxManager for dealer_id, or None."""
        with self._lock:
            return self._tmux_managers.get(dealer_id)

    def list_dealers(self) -> List[Dict[str, Any]]:
        """Return a serialisable snapshot of all registered dealers."""
        with self._lock:
            entries = list(self._dealers.values())

        result = []
        for e in entries:
            snap = e.state.get_snapshot(e.dealer_id)
            result.append({
                "dealer_id": e.dealer_id,
                "workspace": e.workspace,
                "workflow": e.workflow,
                "version": e.version,
                "status": snap.get("status", "unknown"),
                "current_card_id": snap.get("current_card_id"),
                "started_at": e.started_at,
                "last_updated": snap.get("last_updated"),
                "is_paused": e.planner.is_paused(),
                "cycles_completed": snap.get("cycles_completed", 0),
                "completed_total": snap.get("completed_total", 0),
                "progress_pct": snap.get("progress_pct", 0),
                "card_index": snap.get("card_index", 0),
                "total_cards": snap.get("total_cards", 0),
                "error": snap.get("error"),
            })
        return result

    def get_dealer_snapshot(self, dealer_id: str) -> Optional[Dict[str, Any]]:
        """Return the full snapshot for one dealer, or None if not found."""
        entry = self._get(dealer_id)
        if entry is None:
            return None
        snap = entry.state.get_snapshot(dealer_id)
        snap["workspace"] = entry.workspace
        snap["is_paused"] = entry.planner.is_paused()
        return snap

    # ------------------------------------------------------------------ #
    #  Internal helpers
    # ------------------------------------------------------------------ #

    def _get(self, dealer_id: str) -> Optional[DealerEntry]:
        with self._lock:
            return self._dealers.get(dealer_id)

    def _run_dealer(self, dealer_id: str, workflow: str, version: str) -> None:
        entry = self._get(dealer_id)
        if entry is None:
            return
        try:
            entry.planner.run(workflow, version)
        except Exception as exc:
            logger.error("Dealer %s crashed: %s", dealer_id, exc, exc_info=True)
        finally:
            logger.info("Dealer %s run loop exited.", dealer_id)

    def _start_health_monitor(self) -> None:
        """Background daemon: warns when a dealer appears stuck (> 20 min no update)."""
        def _monitor() -> None:
            while True:
                time.sleep(60)
                with self._lock:
                    dealer_ids = list(self._dealers.keys())
                for did in dealer_ids:
                    entry = self._get(did)
                    if entry is None:
                        continue
                    snap = entry.state.get_snapshot(did)
                    if snap.get("status") != "running":
                        continue
                    last_updated = snap.get("last_updated")
                    if not last_updated:
                        continue
                    try:
                        lu = datetime.fromisoformat(last_updated)
                        age = (datetime.now() - lu.replace(tzinfo=None)).total_seconds()
                        if age > 1200:
                            logger.warning(
                                "Dealer %s appears stuck — no state update for %.0f s.", did, age
                            )
                    except (ValueError, TypeError):
                        pass

        t = threading.Thread(target=_monitor, name="dealer-health-monitor", daemon=True)
        t.start()
