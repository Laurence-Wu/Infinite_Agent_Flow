"""
Agent stack factory — single source of truth for building agent components.

Both ``orchestrator.py`` and ``AgentRegistry.start_agent()`` call
``build_agent_stack()`` instead of duplicating the construction sequence.

Stack:
    EngineConfig → ArchiveManager → StateManager (local or remote)
    → CardsPicker → CardsDealer → CardsPlanner
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from core.archive import ArchiveManager
from core.config import EngineConfig
from core.state_manager import RemoteStateManager, StateManager
from engine.dealer import CardsDealer
from engine.picker import CardsPicker
from engine.planner import CardsPlanner


@dataclass
class AgentStack:
    """All components that belong to one running agent."""
    agent_id: str
    config: EngineConfig
    state: StateManager      # may be RemoteStateManager for peer agents
    picker: CardsPicker
    dealer: CardsDealer
    planner: CardsPlanner
    archive: ArchiveManager


def build_agent_stack(
    workspace: str,
    workflow: str,
    version: str,
    agent_id: str,
    hook_manager: Any,                # core.hook_manager.HookManager or None
    server_url: Optional[str] = None, # None → local state; URL → remote
    workflows_path: Optional[str] = None,
) -> AgentStack:
    """
    Create a complete agent stack.

    Parameters
    ----------
    workspace :
        Target directory where ``current_task.md`` and ``archive/`` live.
    workflow :
        Workflow name (directory under ``workflows/``).
    version :
        Workflow version string (e.g. ``"v1"``).
    agent_id :
        Unique identifier for this agent instance.
    hook_manager :
        Shared HookManager (used for the local StateManager only).
    server_url :
        If given, create a ``RemoteStateManager`` that forwards state to
        this URL instead of managing state locally.
    workflows_path :
        Override path to the workflows root directory.
    """
    from pathlib import Path as _Path
    PROJECT_ROOT = _Path(__file__).resolve().parent.parent
    wf_path = workflows_path or str(PROJECT_ROOT / "workflows")

    config = EngineConfig(
        workspace_path=workspace,
        workflows_path=wf_path,
    )
    archive = ArchiveManager(config.resolved_workspace)

    if server_url:
        state: StateManager = RemoteStateManager(
            server_url=server_url,
            agent_id=agent_id,
        )
    else:
        persist_path = config.resolved_workspace / ".carddealer" / "state.json"
        state = StateManager(
            hook_manager=hook_manager,
            persist_path=persist_path,
            agent_id=agent_id,
        )

    picker = CardsPicker(config)
    dealer = CardsDealer(config, state, archive=archive, agent_id=agent_id)
    planner = CardsPlanner(config, state, picker, dealer, agent_id=agent_id)

    return AgentStack(
        agent_id=agent_id,
        config=config,
        state=state,
        picker=picker,
        dealer=dealer,
        planner=planner,
        archive=archive,
    )
