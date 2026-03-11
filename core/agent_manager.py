"""
AgentRegistry — manages multiple independent CardsPlanner instances.

Each agent has its own EngineConfig, StateManager, CardsPicker, CardsDealer,
and CardsPlanner running in a daemon thread from a shared ThreadPoolExecutor.

All agents share a single HookManager so their active_workflows entries
accumulate in the same dictionary and appear together on the dashboard.

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
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------- #
#  AgentEntry
# ---------------------------------------------------------------------- #

@dataclass
class AgentEntry:
    """All components that belong to a single running agent."""

    agent_id: str
    workspace: str
    workflow: str
    version: str
    # Engine components (each agent owns its own instances)
    state: Any    # core.state_manager.StateManager
    planner: Any  # engine.planner.CardsPlanner
    dealer: Any   # engine.dealer.CardsDealer
    picker: Any   # engine.picker.CardsPicker
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())


# ---------------------------------------------------------------------- #
#  AgentRegistry
# ---------------------------------------------------------------------- #

class AgentRegistry:
    """
    Thread-safe registry of AgentEntry instances.

    Usage
    -----
    1. Instantiate once in orchestrator.py, passing the shared HookManager.
    2. Call register() for the main (pre-started) agent_0.
    3. Call start_agent() to spawn additional agents from the web UI.
    4. Inject this registry into DashboardRouter so control endpoints work.
    """

    _MAX_AGENTS = 10

    def __init__(self, hook_manager: Any, workflows_path: str) -> None:
        self._hook_manager = hook_manager
        self._workflows_path = workflows_path
        self._agents: Dict[str, AgentEntry] = {}
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(
            max_workers=self._MAX_AGENTS,
            thread_name_prefix="agent",
        )
        self._start_health_monitor()

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

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
    ) -> None:
        """Register a pre-started agent (e.g. the main agent_0)."""
        entry = AgentEntry(
            agent_id=agent_id,
            workspace=workspace,
            workflow=workflow,
            version=version,
            state=state,
            planner=planner,
            dealer=dealer,
            picker=picker,
        )
        with self._lock:
            self._agents[agent_id] = entry
        logger.info("Registered agent %s (workspace=%s)", agent_id, workspace)

    def start_agent(self, workspace: str, workflow: str, version: str) -> str:
        """
        Spawn a new independent agent in the thread pool.

        Creates a complete engine stack (config, state, picker, dealer, planner)
        for the given workspace and workflow, then submits planner.run() to the
        executor.  Returns the new agent_id.
        """
        # Lazy imports to avoid circular dependencies at module load time
        from core.config import EngineConfig
        from core.state_manager import StateManager
        from engine.dealer import CardsDealer
        from engine.picker import CardsPicker
        from engine.planner import CardsPlanner

        with self._lock:
            agent_id = f"agent_{len(self._agents)}"

        persist_file = Path(workspace).resolve() / ".carddealer_state.json"

        config = EngineConfig(
            workspace_path=workspace,
            workflows_path=self._workflows_path,
        )

        # Restore state from disk if a crash-recovery file exists
        if persist_file.exists():
            state = StateManager.restore(
                persist_path=persist_file,
                hook_manager=self._hook_manager,
                agent_id=agent_id,
            )
            logger.info("Agent %s: restored state from %s", agent_id, persist_file)
        else:
            state = StateManager(
                hook_manager=self._hook_manager,
                persist_path=persist_file,
                agent_id=agent_id,
            )

        picker = CardsPicker(config)
        dealer = CardsDealer(config, state)
        planner = CardsPlanner(config, state, picker, dealer)

        entry = AgentEntry(
            agent_id=agent_id,
            workspace=workspace,
            workflow=workflow,
            version=version,
            state=state,
            planner=planner,
            dealer=dealer,
            picker=picker,
        )
        with self._lock:
            self._agents[agent_id] = entry

        self._executor.submit(self._run_agent, agent_id, workflow, version)
        logger.info("Started agent %s on workspace=%s workflow=%s", agent_id, workspace, workflow)
        return agent_id

    def stop_agent(self, agent_id: str) -> bool:
        """Stop a running agent gracefully."""
        entry = self._get(agent_id)
        if entry is None:
            logger.warning("stop_agent: unknown agent %s", agent_id)
            return False
        entry.planner.stop()
        logger.info("Stopped agent %s", agent_id)
        return True

    def pause_agent(self, agent_id: str) -> bool:
        """Pause an agent after its current card completes."""
        entry = self._get(agent_id)
        if entry is None:
            logger.warning("pause_agent: unknown agent %s", agent_id)
            return False
        entry.planner.pause()
        return True

    def resume_agent(self, agent_id: str) -> bool:
        """Resume a paused agent."""
        entry = self._get(agent_id)
        if entry is None:
            logger.warning("resume_agent: unknown agent %s", agent_id)
            return False
        entry.planner.resume()
        return True

    def deal_next(self, agent_id: str = "agent_0") -> Dict[str, Any]:
        """
        Manually advance one card for the given agent.

        Useful for interactive/debug mode or the 'Deal Next' dashboard button.
        """
        entry = self._get(agent_id)
        if entry is None:
            return {"ok": False, "error": f"unknown agent: {agent_id}"}

        snap = entry.state.get_snapshot()
        current_id = snap.get("current_card_id")

        try:
            if current_id is None:
                card = entry.picker.get_first_card(entry.workflow, entry.version)
            else:
                card = entry.picker.get_next_card(entry.workflow, entry.version, current_id)

            if card is None:
                return {"ok": False, "error": "workflow finished — no next card"}

            total = entry.picker.get_total_cards(entry.workflow, entry.version)
            idx = entry.picker.get_card_index(entry.workflow, entry.version, card.id)
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
            snap = e.state.get_snapshot()
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
            })
        return result

    # ------------------------------------------------------------------ #
    #  Internal helpers
    # ------------------------------------------------------------------ #

    def _get(self, agent_id: str) -> Optional[AgentEntry]:
        with self._lock:
            return self._agents.get(agent_id)

    def _run_agent(self, agent_id: str, workflow: str, version: str) -> None:
        """Thread-pool target: runs planner.run() and logs completion/errors."""
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
        """
        Background daemon thread that logs a warning when an agent's state
        has not been updated for more than 20 minutes while still 'running'.
        """
        def _monitor() -> None:
            while True:
                time.sleep(60)
                with self._lock:
                    agent_ids = list(self._agents.keys())
                for aid in agent_ids:
                    entry = self._get(aid)
                    if entry is None:
                        continue
                    snap = entry.state.get_snapshot()
                    if snap.get("status") != "running":
                        continue
                    last_updated = snap.get("last_updated")
                    if not last_updated:
                        continue
                    try:
                        lu = datetime.fromisoformat(last_updated)
                        age = (datetime.now() - lu.replace(tzinfo=None)).total_seconds()
                        if age > 1200:  # 20 minutes
                            logger.warning(
                                "Agent %s appears stuck — no state update for %.0f s.",
                                aid,
                                age,
                            )
                    except (ValueError, TypeError):
                        pass

        t = threading.Thread(
            target=_monitor,
            name="agent-health-monitor",
            daemon=True,
        )
        t.start()
