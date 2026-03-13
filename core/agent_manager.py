"""
AgentRegistry — manages multiple independent CardsPlanner instances.

Each agent has its own stack (config, state, picker, dealer, planner, archive)
created via ``core.agent_factory.build_agent_stack()``.  All agents share a
single HookManager so their states accumulate in ``active_workflows`` and
appear together on the dashboard.

A background health-monitor thread checks every 60 s for stuck agents
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
#  AgentEntry — thin wrapper around AgentStack for registry bookkeeping
# ---------------------------------------------------------------------- #

@dataclass
class AgentEntry:
    """All components that belong to a single running agent."""
    agent_id: str
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
#  AgentRegistry
# ---------------------------------------------------------------------- #

class AgentRegistry:
    """
    Thread-safe registry of AgentEntry instances.

    Usage:
    1. Instantiate once in orchestrator.py, passing the shared HookManager.
    2. Call ``register_stack()`` for the main (pre-started) agent.
    3. Call ``start_agent()`` to spawn additional agents from the web UI.
    4. Inject this registry into DashboardRouter so control endpoints work.
    """

    _MAX_AGENTS = 10

    def __init__(self, hook_manager: Any, workflows_path: str) -> None:
        self._hook_manager = hook_manager
        self._workflows_path = workflows_path
        self._agents: Dict[str, AgentEntry] = {}
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(
            max_workers=self._MAX_AGENTS,
            thread_name_prefix="agent",
        )
        self._start_health_monitor()

    # ------------------------------------------------------------------ #
    #  Registration
    # ------------------------------------------------------------------ #

    @locked()
    def register_stack(self, stack: Any) -> None:
        """Register a pre-built AgentStack (e.g. the main agent from orchestrator)."""
        entry = AgentEntry(
            agent_id=stack.agent_id,
            workspace=str(stack.config.resolved_workspace),
            workflow=getattr(stack, "workflow", "unknown"),
            version=getattr(stack, "version", "v1"),
            state=stack.state,
            planner=stack.planner,
            dealer=stack.dealer,
            picker=stack.picker,
            archive=stack.archive,
        )
        self._agents[stack.agent_id] = entry
        logger.info("Registered agent %s (workspace=%s)", stack.agent_id, entry.workspace)

    @locked()
    def register(
        self,
        agent_id: str,
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
        entry = AgentEntry(
            agent_id=agent_id,
            workspace=workspace,
            workflow=workflow,
            version=version,
            state=state,
            planner=planner,
            dealer=dealer,
            picker=picker,
            archive=archive,
        )
        self._agents[agent_id] = entry
        logger.info("Registered agent %s (workspace=%s)", agent_id, workspace)

    # ------------------------------------------------------------------ #
    #  Agent lifecycle
    # ------------------------------------------------------------------ #

    def start_agent(self, workspace: str, workflow: str, version: str) -> str:
        """Spawn a new independent agent in the thread pool. Returns agent_id."""
        from core.agent_factory import build_agent_stack

        with self._lock:
            agent_id = f"agent_{len(self._agents)}"

        stack = build_agent_stack(
            workspace=workspace,
            workflow=workflow,
            version=version,
            agent_id=agent_id,
            hook_manager=self._hook_manager,
            workflows_path=self._workflows_path,
        )

        entry = AgentEntry(
            agent_id=agent_id,
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
            self._agents[agent_id] = entry

        self._executor.submit(self._run_agent, agent_id, workflow, version)
        logger.info("Started agent %s on workspace=%s workflow=%s", agent_id, workspace, workflow)
        return agent_id

    @locked()
    def stop_agent(self, agent_id: str) -> bool:
        entry = self._agents.get(agent_id)
        if entry is None:
            logger.warning("stop_agent: unknown agent %s", agent_id)
            return False
        entry.planner.stop()
        logger.info("Stopped agent %s", agent_id)
        return True

    @locked()
    def pause_agent(self, agent_id: str) -> bool:
        entry = self._agents.get(agent_id)
        if entry is None:
            logger.warning("pause_agent: unknown agent %s", agent_id)
            return False
        entry.planner.pause()
        return True

    @locked()
    def resume_agent(self, agent_id: str) -> bool:
        entry = self._agents.get(agent_id)
        if entry is None:
            logger.warning("resume_agent: unknown agent %s", agent_id)
            return False
        entry.planner.resume()
        return True

    def deal_next(self, agent_id: str = "default") -> Dict[str, Any]:
        """Manually advance one card for the given agent."""
        entry = self._get(agent_id)
        if entry is None:
            return {"ok": False, "error": f"unknown agent: {agent_id}"}

        snap = entry.state.get_snapshot(agent_id)
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
            return {"ok": True, "agent_id": agent_id, "card_id": card.id}
        except Exception as exc:
            logger.error("deal_next failed for agent %s: %s", agent_id, exc)
            return {"ok": False, "error": str(exc)}

    def list_agents(self) -> List[Dict[str, Any]]:
        """Return a serialisable snapshot of all registered agents."""
        with self._lock:
            entries = list(self._agents.values())

        result = []
        for e in entries:
            snap = e.state.get_snapshot(e.agent_id)
            result.append({
                "agent_id": e.agent_id,
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

    def get_agent_snapshot(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Return the full snapshot for one agent, or None if not found."""
        entry = self._get(agent_id)
        if entry is None:
            return None
        snap = entry.state.get_snapshot(agent_id)
        snap["workspace"] = entry.workspace
        snap["is_paused"] = entry.planner.is_paused()
        return snap

    # ------------------------------------------------------------------ #
    #  Internal helpers
    # ------------------------------------------------------------------ #

    def _get(self, agent_id: str) -> Optional[AgentEntry]:
        with self._lock:
            return self._agents.get(agent_id)

    def _run_agent(self, agent_id: str, workflow: str, version: str) -> None:
        entry = self._get(agent_id)
        if entry is None:
            return
        try:
            entry.planner.run(workflow, version)
        except Exception as exc:
            logger.error("Agent %s crashed: %s", agent_id, exc, exc_info=True)
        finally:
            logger.info("Agent %s run loop exited.", agent_id)

    def _start_health_monitor(self) -> None:
        """Background daemon: warns when an agent appears stuck (> 20 min no update)."""
        def _monitor() -> None:
            while True:
                time.sleep(60)
                with self._lock:
                    agent_ids = list(self._agents.keys())
                for aid in agent_ids:
                    entry = self._get(aid)
                    if entry is None:
                        continue
                    snap = entry.state.get_snapshot(aid)
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
                                "Agent %s appears stuck — no state update for %.0f s.", aid, age
                            )
                    except (ValueError, TypeError):
                        pass

        t = threading.Thread(target=_monitor, name="agent-health-monitor", daemon=True)
        t.start()
