"""
Thread-safe StateManager shared between the Flask web layer and the Planner.

Supports multi-agent state tracking. Each agent is identified by a unique
agent_id.  All mutating methods are protected with @locked().

RemoteStateManager
------------------
A subclass that forwards every state mutation to a remote dashboard via
``POST /api/report-state``.  Uses explicit method delegation (no
``__getattribute__`` magic — that pattern is expensive and fragile).
"""

from __future__ import annotations

import base64
import copy
import json
import threading
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.decorators import locked, retry


@dataclass
class TaskSnapshot:
    """Mutable snapshot of one agent's runtime state."""
    agent_id: str = "default"
    current_card_id: Optional[str] = None
    current_workflow: Optional[str] = None
    current_version: Optional[str] = None
    current_instruction: Optional[str] = None
    current_loop_id: str = "main"
    card_index: int = 0
    total_cards: int = 0
    status: str = "idle"   # idle | running | completed | error | workflow_finished
    started_at: Optional[str] = None
    last_updated: Optional[str] = None
    history: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    log_lines: List[str] = field(default_factory=list)
    engine_start_epoch: Optional[float] = None


class StateManager:
    """Central, thread-safe state container for multiple agents."""

    LOG_BUFFER_SIZE = 300

    def __init__(
        self,
        hook_manager: Any = None,
        persist_path: Any = None,
        agent_id: str = "default",
    ):
        self._lock = threading.RLock()
        self._agents: Dict[str, TaskSnapshot] = {}
        self._primary_agent_id: str = agent_id
        self._hook_manager = hook_manager
        self._persist_path = Path(persist_path) if persist_path else None
        self._ensure_agent(agent_id)

    # ------------------------------------------------------------------ #
    #  Class methods
    # ------------------------------------------------------------------ #

    @classmethod
    def restore(
        cls,
        persist_path: Any,
        hook_manager: Any = None,
        agent_id: str = "default",
    ) -> "StateManager":
        """Restore state from a JSON snapshot file (crash recovery)."""
        inst = cls(hook_manager=hook_manager, persist_path=persist_path, agent_id=agent_id)
        try:
            data = json.loads(Path(persist_path).read_text(encoding="utf-8"))
            inst.update_from_snapshot(data)
        except Exception:
            pass
        return inst

    # ------------------------------------------------------------------ #
    #  Internal
    # ------------------------------------------------------------------ #

    def _ensure_agent(self, agent_id: str) -> TaskSnapshot:
        if agent_id not in self._agents:
            s = TaskSnapshot(agent_id=agent_id)
            s.engine_start_epoch = time.time()
            self._agents[agent_id] = s
        return self._agents[agent_id]

    @retry(n=3, exc=(OSError,), delay=0.1)
    def _persist(self) -> None:
        """Write primary agent snapshot to disk (best-effort)."""
        if self._persist_path is None:
            return
        try:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            snap = self.get_snapshot(self._primary_agent_id)
            self._persist_path.write_text(
                json.dumps(snap, indent=2, default=str), encoding="utf-8"
            )
        except OSError:
            raise   # let @retry handle it

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

    # ------------------------------------------------------------------ #
    #  Read API  (no locking needed — callers get a deep copy)
    # ------------------------------------------------------------------ #

    def get_snapshot(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Return a dict copy of one agent's state (default: primary agent)."""
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
        with self._lock:
            return sorted(self._agents.keys())

    def get_all_snapshots(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            ids = list(self._agents.keys())
        return {aid: self.get_snapshot(aid) for aid in ids}

    # ------------------------------------------------------------------ #
    #  Write API  (all protected with @locked)
    # ------------------------------------------------------------------ #

    @locked()
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
        self._persist()

    @locked()
    def push_log(self, line: str, agent_id: Optional[str] = None) -> None:
        aid = agent_id or self._primary_agent_id
        s = self._ensure_agent(aid)
        s.log_lines.append(line)
        if len(s.log_lines) > self.LOG_BUFFER_SIZE:
            del s.log_lines[:-self.LOG_BUFFER_SIZE]

    @locked()
    def mark_completed(self, summary: str, agent_id: Optional[str] = None) -> None:
        aid = agent_id or self._primary_agent_id
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
        self._persist()

    @locked()
    def mark_error(self, error_msg: str, agent_id: Optional[str] = None) -> None:
        aid = agent_id or self._primary_agent_id
        s = self._ensure_agent(aid)
        s.status = "error"
        s.error = error_msg
        s.last_updated = datetime.now().isoformat()
        self._persist()

    @locked()
    def set_idle(self, agent_id: Optional[str] = None) -> None:
        aid = agent_id or self._primary_agent_id
        s = self._ensure_agent(aid)
        s.status = "idle"
        s.last_updated = datetime.now().isoformat()
        self._persist()

    @locked()
    def set_workflow_finished(self, agent_id: Optional[str] = None) -> None:
        aid = agent_id or self._primary_agent_id
        s = self._ensure_agent(aid)
        s.status = "workflow_finished"
        s.last_updated = datetime.now().isoformat()
        self._persist()

    @locked()
    def update_from_snapshot(self, snapshot_data: Dict[str, Any]) -> None:
        """Bulk update from a remote agent's snapshot (used by /api/report-state)."""
        aid = snapshot_data.get("agent_id", self._primary_agent_id)
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
        # Merge history (append new entries, don't replace)
        incoming = snapshot_data.get("history", [])
        existing_ids = {(e.get("card_id"), e.get("completed_at")) for e in s.history}
        for entry in incoming:
            key = (entry.get("card_id"), entry.get("completed_at"))
            if key not in existing_ids:
                s.history.append(entry)
                existing_ids.add(key)
        s.error = snapshot_data.get("error")
        # Merge log lines (append new lines, avoid duplicates by timestamp prefix)
        new_logs = snapshot_data.get("log_lines", [])
        if new_logs:
            existing_set = set(s.log_lines[-50:])
            for line in new_logs:
                if line not in existing_set:
                    s.log_lines.append(line)
                    existing_set.add(line)
            if len(s.log_lines) > self.LOG_BUFFER_SIZE:
                del s.log_lines[:-self.LOG_BUFFER_SIZE]
        s.engine_start_epoch = snapshot_data.get("engine_start_epoch")


# ------------------------------------------------------------------ #
#  RemoteStateManager
# ------------------------------------------------------------------ #

class RemoteStateManager(StateManager):
    """
    StateManager that forwards every mutation to a remote dashboard
    via ``POST /api/report-state``.

    Uses explicit method overrides — NO ``__getattribute__`` magic.
    """

    def __init__(self, server_url: str, agent_id: str = "default"):
        super().__init__(agent_id=agent_id)

        # Extract Basic-Auth credentials embedded in the URL
        # e.g. https://user:pass@abc123.ngrok-free.app
        parsed = urllib.parse.urlparse(server_url)
        if parsed.username:
            creds = f"{parsed.username}:{parsed.password or ''}"
            self._auth_header: Optional[str] = (
                "Basic " + base64.b64encode(creds.encode()).decode()
            )
            # Rebuild URL without credentials
            netloc = parsed.hostname + (f":{parsed.port}" if parsed.port else "")
            clean = parsed._replace(netloc=netloc)
            self._server_url = urllib.parse.urlunparse(clean).rstrip("/")
        else:
            self._auth_header = None
            self._server_url = server_url.rstrip("/")

        self._report_endpoint = f"{self._server_url}/api/report-state"

    # ------------------------------------------------------------------ #
    #  Forwarding wrappers for all mutating methods
    # ------------------------------------------------------------------ #

    def set_current_card(self, **kwargs) -> None:
        super().set_current_card(**kwargs)
        self._forward()

    def mark_completed(self, summary: str, agent_id: Optional[str] = None) -> None:
        super().mark_completed(summary, agent_id=agent_id)
        self._forward()

    def mark_error(self, error_msg: str, agent_id: Optional[str] = None) -> None:
        super().mark_error(error_msg, agent_id=agent_id)
        self._forward()

    def set_idle(self, agent_id: Optional[str] = None) -> None:
        super().set_idle(agent_id=agent_id)
        self._forward()

    def set_workflow_finished(self, agent_id: Optional[str] = None) -> None:
        super().set_workflow_finished(agent_id=agent_id)
        self._forward()

    def push_log(self, line: str, agent_id: Optional[str] = None) -> None:
        super().push_log(line, agent_id=agent_id)
        # Don't forward every log line (very chatty); forward on major events only

    # ------------------------------------------------------------------ #
    #  Internal
    # ------------------------------------------------------------------ #

    def _forward(self) -> None:
        """POST the current snapshot to the remote dashboard (best-effort)."""
        try:
            snap = self.get_snapshot(self._primary_agent_id)
            snap["agent_id"] = self._primary_agent_id
            data = json.dumps(snap, default=str).encode("utf-8")
            headers: Dict[str, str] = {"Content-Type": "application/json"}
            if self._auth_header:
                headers["Authorization"] = self._auth_header
            req = urllib.request.Request(
                self._report_endpoint,
                data=data,
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=3):
                pass
        except Exception:
            pass   # best-effort: never crash the local planner
