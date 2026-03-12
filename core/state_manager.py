"""
Thread-safe StateManager shared between the Flask web layer and the Planner.

Supports multi-agent state tracking. Each agent is identified by a unique agent_id.
"""

from __future__ import annotations

import copy
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class TaskSnapshot:
    """Immutable snapshot of an agent's state at a point in time."""
    agent_id: str = "default"
    current_card_id: Optional[str] = None
    current_workflow: Optional[str] = None
    current_version: Optional[str] = None
    current_instruction: Optional[str] = None
    current_loop_id: str = "main"
    card_index: int = 0
    total_cards: int = 0
    status: str = "idle"            # idle | running | completed | error | workflow_finished
    started_at: Optional[str] = None
    last_updated: Optional[str] = None
    history: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    log_lines: List[str] = field(default_factory=list)
    engine_start_epoch: Optional[float] = None


class StateManager:
    """
    Central, thread-safe state container. Handles multiple agents.
    """

    LOG_BUFFER_SIZE = 300

    def __init__(self):
        self._lock = threading.Lock()
        # Maps agent_id -> TaskSnapshot
        self._agents: Dict[str, TaskSnapshot] = {}
        self._primary_agent_id: str = "default"
        self._ensure_agent(self._primary_agent_id)

    def _ensure_agent(self, agent_id: str) -> TaskSnapshot:
        if agent_id not in self._agents:
            s = TaskSnapshot(agent_id=agent_id)
            s.engine_start_epoch = time.time()
            self._agents[agent_id] = s
        return self._agents[agent_id]

    # ------------------------------------------------------------------ #
    #  Read (Dashboard side)
    # ------------------------------------------------------------------ #

    def get_snapshot(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Return a dict copy of an agent's state (default: primary agent)."""
        aid = agent_id or self._primary_agent_id
        with self._lock:
            if aid not in self._agents:
                return {"error": f"Agent '{aid}' not found"}
            
            s = self._agents[aid]
            total = s.total_cards
            completed = len(s.history)
            cycles = completed // total if total > 0 else 0
            
            return {
                "agent_id": s.agent_id,
                "current_card_id": s.current_card_id,
                "current_workflow": s.current_workflow,
                "current_version": s.current_version,
                "current_instruction": s.current_instruction,
                "card_index": s.card_index,
                "total_cards": s.total_cards,
                "progress_pct": self._progress_pct(aid),
                "completed_total": completed,
                "cycles_completed": cycles,
                "current_loop_id": s.current_loop_id,
                "status": s.status,
                "started_at": s.started_at,
                "last_updated": s.last_updated,
                "history": copy.deepcopy(s.history),
                "error": s.error,
                "log_lines": list(s.log_lines[-self.LOG_BUFFER_SIZE:]),
                "engine_start_epoch": s.engine_start_epoch,
                "uptime_seconds": self._uptime_seconds(aid),
            }

    def list_agents(self) -> List[str]:
        """Return IDs of all agents currently reporting state."""
        with self._lock:
            return sorted(self._agents.keys())

    def get_all_snapshots(self) -> Dict[str, Dict[str, Any]]:
        """Return snapshots for all registered agents."""
        with self._lock:
            ids = list(self._agents.keys())
        
        return {aid: self.get_snapshot(aid) for aid in ids}

    # ------------------------------------------------------------------ #
    #  Write (Worker / Planner side)
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
        agent_id: Optional[str] = None,
    ) -> None:
        aid = agent_id or self._primary_agent_id
        with self._lock:
            s = self._ensure_agent(aid)
            s.current_card_id = card_id
            s.current_workflow = workflow
            s.current_version = version
            s.current_instruction = instruction
            s.current_loop_id = loop_id
            s.card_index = card_index
            s.total_cards = total_cards
            s.status = "running"
            s.started_at = datetime.now().isoformat()
            s.last_updated = s.started_at
            s.error = None

    def push_log(self, line: str, agent_id: Optional[str] = None) -> None:
        aid = agent_id or self._primary_agent_id
        with self._lock:
            s = self._ensure_agent(aid)
            s.log_lines.append(line)
            if len(s.log_lines) > self.LOG_BUFFER_SIZE:
                del s.log_lines[:-self.LOG_BUFFER_SIZE]

    def mark_completed(self, summary: str, agent_id: Optional[str] = None) -> None:
        aid = agent_id or self._primary_agent_id
        with self._lock:
            s = self._ensure_agent(aid)
            now = datetime.now().isoformat()
            s.history.append({
                "card_id": s.current_card_id,
                "workflow": s.current_workflow,
                "version": s.current_version,
                "loop_id": s.current_loop_id,
                "summary": summary,
                "completed_at": now,
            })
            s.status = "completed"
            s.last_updated = now

    def mark_error(self, error_msg: str, agent_id: Optional[str] = None) -> None:
        aid = agent_id or self._primary_agent_id
        with self._lock:
            s = self._ensure_agent(aid)
            s.status = "error"
            s.error = error_msg
            s.last_updated = datetime.now().isoformat()

    def set_workflow_finished(self, agent_id: Optional[str] = None) -> None:
        aid = agent_id or self._primary_agent_id
        with self._lock:
            s = self._ensure_agent(aid)
            s.status = "workflow_finished"
            s.last_updated = datetime.now().isoformat()

    def update_from_snapshot(self, snapshot_data: Dict[str, Any]) -> None:
        """Bulk update an agent state (used by /api/report-state)."""
        aid = snapshot_data.get("agent_id", self._primary_agent_id)
        with self._lock:
            s = self._ensure_agent(aid)
            s.current_card_id = snapshot_data.get("current_card_id")
            s.current_workflow = snapshot_data.get("current_workflow")
            s.current_version = snapshot_data.get("current_version")
            s.current_instruction = snapshot_data.get("current_instruction")
            s.current_loop_id = snapshot_data.get("current_loop_id", "main")
            s.card_index = snapshot_data.get("card_index", 0)
            s.total_cards = snapshot_data.get("total_cards", 0)
            s.status = snapshot_data.get("status", "idle")
            s.started_at = snapshot_data.get("started_at")
            s.last_updated = snapshot_data.get("last_updated")
            s.history = snapshot_data.get("history", [])
            s.error = snapshot_data.get("error")
            s.log_lines = snapshot_data.get("log_lines", [])
            s.engine_start_epoch = snapshot_data.get("engine_start_epoch")

    # ------------------------------------------------------------------ #
    #  Internal helpers
    # ------------------------------------------------------------------ #

    def _uptime_seconds(self, agent_id: str) -> float:
        s = self._agents.get(agent_id)
        if not s or s.engine_start_epoch is None:
            return 0.0
        return time.time() - s.engine_start_epoch

    def _progress_pct(self, agent_id: str) -> float:
        s = self._agents.get(agent_id)
        if not s or s.total_cards == 0:
            return 0.0
        return round((s.card_index / s.total_cards) * 100, 1)


class RemoteStateManager(StateManager):
    """
    A specialized StateManager that forwards all updates to a remote
    dashboard server instead of (or in addition to) local state.
    """

    def __init__(self, server_url: str, agent_id: str):
        super().__init__()
        self._server_url = server_url.rstrip("/")
        self._primary_agent_id = agent_id
        self._ensure_agent(agent_id)
        self._report_endpoint = f"{self._server_url}/api/report-state"

    def _report_to_server(self):
        """Send the current local snapshot to the remote server."""
        import json
        import urllib.request
        
        snapshot = self.get_snapshot(self._primary_agent_id)
        data = json.dumps(snapshot).encode("utf-8")
        
        try:
            req = urllib.request.Request(
                self._report_endpoint,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=2) as resp:
                pass
        except Exception:
            # Silently fail on network errors to avoid crashing the agent
            pass

    def set_current_card(self, *args, **kwargs) -> None:
        super().set_current_card(*args, **kwargs)
        self._report_to_server()

    def push_log(self, *args, **kwargs) -> None:
        super().push_log(*args, **kwargs)
        self._report_to_server()

    def mark_completed(self, *args, **kwargs) -> None:
        super().mark_completed(*args, **kwargs)
        self._report_to_server()

    def mark_error(self, *args, **kwargs) -> None:
        super().mark_error(*args, **kwargs)
        self._report_to_server()

    def set_workflow_finished(self, *args, **kwargs) -> None:
        super().set_workflow_finished(*args, **kwargs)
        self._report_to_server()
