"""
Dealer stack factory — single source of truth for building Card Dealer components.

A "dealer" is the CardDealer workflow runner: it deals cards (tasks) from a
workflow JSON chain, writes current_task.md, watches for the AI agent's stop
token, archives the result, and loops.

The AI agent (Gemini, Claude, etc.) reads current_task.md and runs in a
separate tmux session — see core/tmux_manager.py.

Both orchestrator.py and DealerRegistry.start_dealer() call
build_dealer_stack() instead of duplicating the construction sequence.

Stack:
    EngineConfig → ArchiveManager → StateManager (local or remote)
    → CardsPicker → CardsDealer → CardsPlanner
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from core.archive import ArchiveManager
from core.config import EngineConfig
from core.state_manager import RemoteStateManager, StateManager
from engine.dealer import CardsDealer
from engine.picker import CardsPicker
from engine.planner import CardsPlanner


@dataclass
class DealerStack:
    """All components that belong to one running Card Dealer instance."""
    agent_id: str        # kept as agent_id internally for StateManager compat
    config: EngineConfig
    workflow: str
    version: str
    state: StateManager      # may be RemoteStateManager for peer dealers
    picker: CardsPicker
    dealer: CardsDealer
    planner: CardsPlanner
    archive: ArchiveManager


def build_dealer_stack(
    workspace: str,
    workflow: str,
    version: str,
    dealer_id: str,
    hook_manager: Any,                # core.hook_manager.HookManager or None
    server_url: Optional[str] = None, # None → local state; URL → remote
    workflows_path: Optional[str] = None,
) -> DealerStack:
    """
    Create a complete Card Dealer stack.

    Parameters
    ----------
    workspace :
        Target directory where ``current_task.md`` and ``archive/`` live.
    workflow :
        Workflow name (directory under ``workflows/``).
    version :
        Workflow version string (e.g. ``"v1"``).
    dealer_id :
        Unique identifier for this dealer instance.
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
            agent_id=dealer_id,
        )
    else:
        persist_path = config.resolved_workspace / ".carddealer" / "state.json"
        state = StateManager(
            hook_manager=hook_manager,
            persist_path=persist_path,
            agent_id=dealer_id,
        )

    picker = CardsPicker(config)
    dealer = CardsDealer(config, state, archive=archive, agent_id=dealer_id)
    planner = CardsPlanner(config, state, picker, dealer, agent_id=dealer_id)

    return DealerStack(
        agent_id=dealer_id,
        config=config,
        workflow=workflow,
        version=version,
        state=state,
        picker=picker,
        dealer=dealer,
        planner=planner,
        archive=archive,
    )


# ---------------------------------------------------------------------------
# Backward-compat aliases so old imports still work
# ---------------------------------------------------------------------------

AgentStack = DealerStack

def build_agent_stack(
    workspace: str,
    workflow: str,
    version: str,
    agent_id: str,
    hook_manager: Any,
    server_url: Optional[str] = None,
    workflows_path: Optional[str] = None,
) -> DealerStack:
    return build_dealer_stack(
        workspace=workspace,
        workflow=workflow,
        version=version,
        dealer_id=agent_id,
        hook_manager=hook_manager,
        server_url=server_url,
        workflows_path=workflows_path,
    )
