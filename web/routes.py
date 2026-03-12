"""
DashboardRouter — registers all Flask routes as class methods.

All route logic lives here; web/app.py is a thin factory that
instantiates this class and calls register().

RESTful agent-control routes (require AgentRegistry):
    GET  /api/agents                    — list all registered agents
    GET  /api/agent/<id>                — full snapshot for one agent
    GET  /api/agent/<id>/logs           — log lines for one agent
    GET  /api/agent/<id>/history        — completion history for one agent
    POST /api/agent/<id>/pause          — pause agent
    POST /api/agent/<id>/resume         — resume agent
    POST /api/agent/<id>/stop           — stop agent
    POST /api/agent/<id>/deal           — deal next card
    POST /api/agent/<id>/restart        — stop then respawn agent with same config
    GET  /api/agent/<id>/workspace-scan — scan this agent's workspace directory
    POST /api/agents                    — start new agent (workspace/workflow/version)
    POST /api/report-state              — peer state report from remote agents

Archive routes (require ArchiveManager):
    GET  /api/archive                   — list recent archive entries
    GET  /api/archive/<loop>/<folder>   — single archive entry detail

Session routes (require TmuxManager):
    GET  /api/session                   — tmux session status + pane output
    POST /api/session/start             — start tmux session (non-blocking)
    POST /api/session/stop              — stop tmux session
    POST /api/session/restart           — restart tmux session (non-blocking)

Backward-compat aliases (kept for existing UI code):
    GET  /api/status                    — snapshot for queried agent_id
    POST /api/workflow/pause            — pause (body: {agent_id})
    POST /api/workflow/resume           — resume (body: {agent_id})
    POST /api/workflow/stop             — stop   (body: {agent_id})
    POST /api/deal-next                 — deal next (body: {agent_id})
    POST /api/agent/start               — start new agent
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Optional

from flask import Flask, Response, jsonify, render_template, request

from core.config import EngineConfig
from core.state_manager import StateManager
from engine.picker import CardsPicker
from engine.scanner import WorkspaceScanner


class DashboardRouter:
    """
    Encapsulates every HTTP route handler.

    Dependencies are injected once at construction so each method
    has access to config/state/picker/scanner/registry/archive/tmux without closures.
    """

    def __init__(
        self,
        config:       EngineConfig,
        state:        StateManager,
        picker:       CardsPicker,
        scanner:      WorkspaceScanner,
        registry:     Optional[Any] = None,   # AgentRegistry | None
        archive:      Optional[Any] = None,   # ArchiveManager | None
        tmux_manager: Optional[Any] = None,   # TmuxManager | None
    ) -> None:
        self.config       = config
        self.state        = state
        self.picker       = picker
        self.scanner      = scanner
        self.registry     = registry
        self.archive      = archive
        self.tmux_manager = tmux_manager

    def register(self, app: Flask) -> None:
        """Bind all routes to the Flask application."""

        # ── Agent list & control ──────────────────────────────────────────
        app.add_url_rule("/api/agents",              "api_agents",        self.api_agents)
        app.add_url_rule("/api/agents",              "api_agents_start",  self.api_agents_start, methods=["POST"])
        app.add_url_rule("/api/agent/<agent_id>",    "api_agent",         self.api_agent)
        app.add_url_rule("/api/agent/<agent_id>/logs",    "api_agent_logs",    self.api_agent_logs)
        app.add_url_rule("/api/agent/<agent_id>/history", "api_agent_history", self.api_agent_history)
        app.add_url_rule("/api/agent/<agent_id>/pause",   "api_agent_pause",   self.api_agent_pause,   methods=["POST"])
        app.add_url_rule("/api/agent/<agent_id>/resume",  "api_agent_resume",  self.api_agent_resume,  methods=["POST"])
        app.add_url_rule("/api/agent/<agent_id>/stop",    "api_agent_stop",    self.api_agent_stop,    methods=["POST"])
        app.add_url_rule("/api/agent/<agent_id>/deal",    "api_agent_deal",    self.api_agent_deal,    methods=["POST"])
        app.add_url_rule("/api/agent/<agent_id>/restart",  "api_agent_restart",  self.api_agent_restart,  methods=["POST"])
        app.add_url_rule("/api/agent/<agent_id>/workspace-scan", "api_agent_workspace_scan", self.api_agent_workspace_scan)

        # ── Peer state reporting ──────────────────────────────────────────
        app.add_url_rule("/api/report-state", "api_report_state", self.api_report_state, methods=["POST"])

        # ── Archive ───────────────────────────────────────────────────────
        app.add_url_rule("/api/archive",                  "api_archive",       self.api_archive)
        app.add_url_rule("/api/archive/<loop_id>/<folder>", "api_archive_entry", self.api_archive_entry)

        # ── General read endpoints ────────────────────────────────────────
        app.add_url_rule("/api/status",         "api_status",         self.api_status)
        app.add_url_rule("/api/workflows",      "api_workflows",      self.api_workflows)
        app.add_url_rule("/api/history",        "api_history",        self.api_history)
        app.add_url_rule("/api/current-task",   "api_current_task",   self.api_current_task)
        app.add_url_rule("/api/logs",           "api_logs",           self.api_logs)
        app.add_url_rule("/api/workspace-scan", "api_workspace_scan", self.api_workspace_scan)

        # ── Backward-compat control aliases ──────────────────────────────
        app.add_url_rule("/api/workflow/pause",  "compat_pause",  self.compat_pause,  methods=["POST"])
        app.add_url_rule("/api/workflow/resume", "compat_resume", self.compat_resume, methods=["POST"])
        app.add_url_rule("/api/workflow/stop",   "compat_stop",   self.compat_stop,   methods=["POST"])
        app.add_url_rule("/api/deal-next",       "compat_deal",   self.compat_deal,   methods=["POST"])
        app.add_url_rule("/api/agent/start",     "compat_start",  self.api_agents_start, methods=["POST"])

        # ── Session (tmux) ───────────────────────────────────────────────
        app.add_url_rule("/api/session",         "api_session",         self.api_session)
        app.add_url_rule("/api/session/start",   "api_session_start",   self.api_session_start,   methods=["POST"])
        app.add_url_rule("/api/session/stop",    "api_session_stop",    self.api_session_stop,    methods=["POST"])
        app.add_url_rule("/api/session/restart", "api_session_restart", self.api_session_restart, methods=["POST"])

        # ── HTMX partials ─────────────────────────────────────────────────
        app.add_url_rule("/partials/status",   "partial_status",   self.partial_status)
        app.add_url_rule("/partials/progress", "partial_progress", self.partial_progress)
        app.add_url_rule("/partials/history",  "partial_history",  self.partial_history)
        app.add_url_rule("/partials/logs",     "partial_logs",     self.partial_logs)

        # ── Page ──────────────────────────────────────────────────────────
        app.add_url_rule("/", "index", self.index)

    # ------------------------------------------------------------------ #
    #  Agent list + control
    # ------------------------------------------------------------------ #

    def api_agents(self):
        """GET /api/agents — list all registered agents as a JSON array."""
        if self.registry:
            return jsonify(self.registry.list_agents())
        # Fallback: synthesise from state snapshots
        snaps = self.state.get_all_snapshots()
        return jsonify(list(snaps.values()))

    def api_agents_start(self):
        """POST /api/agents — start a new agent."""
        if self.registry is None:
            return jsonify({"error": "AgentRegistry not available"}), 503
        body = request.get_json() or {}
        workspace = body.get("workspace")
        workflow  = body.get("workflow")
        version   = body.get("version", "v1")
        if not workspace or not workflow:
            return jsonify({"error": "workspace and workflow are required"}), 400
        agent_id = self.registry.start_agent(workspace, workflow, version)
        return jsonify({"ok": True, "agent_id": agent_id}), 201

    def api_agent(self, agent_id: str):
        """GET /api/agent/<id> — full snapshot for one agent."""
        if self.registry:
            snap = self.registry.get_agent_snapshot(agent_id)
            if snap is None:
                return jsonify({"error": f"Agent '{agent_id}' not found"}), 404
            return jsonify(snap)
        snap = self.state.get_snapshot(agent_id)
        return jsonify(snap)

    def api_agent_logs(self, agent_id: str):
        """GET /api/agent/<id>/logs — log lines for one agent."""
        snap = self.state.get_snapshot(agent_id)
        return jsonify({"agent_id": agent_id, "logs": snap.get("log_lines", [])})

    def api_agent_history(self, agent_id: str):
        """GET /api/agent/<id>/history — completion history for one agent."""
        snap = self.state.get_snapshot(agent_id)
        return jsonify({"agent_id": agent_id, "history": snap.get("history", [])})

    def api_agent_pause(self, agent_id: str):
        """POST /api/agent/<id>/pause."""
        if self.registry is None:
            return jsonify({"error": "AgentRegistry not available"}), 503
        ok = self.registry.pause_agent(agent_id)
        return jsonify({"ok": ok, "agent_id": agent_id})

    def api_agent_resume(self, agent_id: str):
        """POST /api/agent/<id>/resume."""
        if self.registry is None:
            return jsonify({"error": "AgentRegistry not available"}), 503
        ok = self.registry.resume_agent(agent_id)
        return jsonify({"ok": ok, "agent_id": agent_id})

    def api_agent_stop(self, agent_id: str):
        """POST /api/agent/<id>/stop."""
        if self.registry is None:
            return jsonify({"error": "AgentRegistry not available"}), 503
        ok = self.registry.stop_agent(agent_id)
        return jsonify({"ok": ok, "agent_id": agent_id})

    def api_agent_deal(self, agent_id: str):
        """POST /api/agent/<id>/deal — manually advance one card."""
        if self.registry is None:
            return jsonify({"error": "AgentRegistry not available"}), 503
        result = self.registry.deal_next(agent_id)
        code = 200 if result.get("ok") else 500
        return jsonify(result), code

    def api_agent_restart(self, agent_id: str):
        """POST /api/agent/<id>/restart — stop current run and start a fresh one."""
        if self.registry is None:
            return jsonify({"error": "AgentRegistry not available"}), 503
        # Capture config before stopping
        agents = self.registry.list_agents()
        entry = next((a for a in agents if a["agent_id"] == agent_id), None)
        if entry is None:
            return jsonify({"error": f"Agent '{agent_id}' not found"}), 404
        self.registry.stop_agent(agent_id)
        new_id = self.registry.start_agent(
            entry["workspace"], entry["workflow"], entry["version"]
        )
        return jsonify({"ok": True, "agent_id": new_id})

    def api_agent_workspace_scan(self, agent_id: str):
        """GET /api/agent/<id>/workspace-scan — scan this agent's workspace directory."""
        if not self.registry:
            return jsonify({"files": []})
        snap = self.registry.get_agent_snapshot(agent_id)
        ws_path = (snap or {}).get("workspace", "")
        if not ws_path:
            return jsonify({"files": []})
        cfg = EngineConfig(workspace_path=ws_path)
        return jsonify({"files": WorkspaceScanner(cfg).scan()})

    # ------------------------------------------------------------------ #
    #  Peer state reporting
    # ------------------------------------------------------------------ #

    def api_report_state(self):
        """POST /api/report-state — accept a state snapshot from a remote agent."""
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing JSON body"}), 400
        self.state.update_from_snapshot(data)
        return jsonify({"status": "ok"})

    # ------------------------------------------------------------------ #
    #  Archive
    # ------------------------------------------------------------------ #

    def api_archive(self):
        """GET /api/archive — list recent archive entries."""
        if self.archive is None:
            return jsonify({"error": "ArchiveManager not available"}), 503
        loop_id = request.args.get("loop_id")
        limit   = int(request.args.get("limit", 50))
        entries = self.archive.list_entries(loop_id=loop_id, limit=limit)
        return jsonify(entries)

    def api_archive_entry(self, loop_id: str, folder: str):
        """GET /api/archive/<loop_id>/<folder> — single archive entry detail."""
        if self.archive is None:
            return jsonify({"error": "ArchiveManager not available"}), 503
        entry = self.archive.get_entry(loop_id, folder)
        if entry is None:
            return jsonify({"error": "Entry not found"}), 404
        return jsonify(entry)

    # ------------------------------------------------------------------ #
    #  General read endpoints
    # ------------------------------------------------------------------ #

    def api_status(self):
        agent_id = request.args.get("agent_id")
        return jsonify(self.state.get_snapshot(agent_id))

    def api_workflows(self):
        return jsonify(self.picker.list_workflows())

    def api_history(self):
        agent_id = request.args.get("agent_id")
        snap = self.state.get_snapshot(agent_id)
        return jsonify(snap.get("history", []))

    def api_current_task(self):
        task_file = self.config.task_file
        if task_file.exists():
            return Response(task_file.read_text(encoding="utf-8"), mimetype="text/markdown")
        return Response("No active task.", mimetype="text/plain", status=404)

    def api_logs(self):
        agent_id = request.args.get("agent_id")
        snap = self.state.get_snapshot(agent_id)
        return jsonify({"logs": snap.get("log_lines", [])})

    def api_workspace_scan(self):
        return jsonify({"files": self.scanner.scan()})

    # ------------------------------------------------------------------ #
    #  Backward-compat control aliases
    # ------------------------------------------------------------------ #

    def _agent_id_from_body(self) -> str:
        body = request.get_json(silent=True) or {}
        return body.get("agent_id", "default")

    def compat_pause(self):
        agent_id = self._agent_id_from_body()
        if self.registry:
            ok = self.registry.pause_agent(agent_id)
            return jsonify({"ok": ok, "agent_id": agent_id})
        return jsonify({"error": "AgentRegistry not available"}), 503

    def compat_resume(self):
        agent_id = self._agent_id_from_body()
        if self.registry:
            ok = self.registry.resume_agent(agent_id)
            return jsonify({"ok": ok, "agent_id": agent_id})
        return jsonify({"error": "AgentRegistry not available"}), 503

    def compat_stop(self):
        agent_id = self._agent_id_from_body()
        if self.registry:
            ok = self.registry.stop_agent(agent_id)
            return jsonify({"ok": ok, "agent_id": agent_id})
        return jsonify({"error": "AgentRegistry not available"}), 503

    def compat_deal(self):
        agent_id = self._agent_id_from_body()
        if self.registry:
            result = self.registry.deal_next(agent_id)
            code = 200 if result.get("ok") else 500
            return jsonify(result), code
        return jsonify({"error": "AgentRegistry not available"}), 503

    # ------------------------------------------------------------------ #
    #  Session (tmux) endpoints
    # ------------------------------------------------------------------ #

    def _no_tmux(self):
        return jsonify({"ok": False, "error": "TmuxManager not configured"}), 503

    def api_session(self):
        """GET /api/session — tmux session status + pane output."""
        if not self.tmux_manager:
            return self._no_tmux()
        return jsonify(self.tmux_manager.status())

    def api_session_start(self):
        """POST /api/session/start — start tmux session (non-blocking; returns immediately)."""
        if not self.tmux_manager:
            return self._no_tmux()
        threading.Thread(target=self.tmux_manager.start, daemon=True, name="session-start").start()
        return jsonify({"ok": True, "starting": True, **self.tmux_manager.status()})

    def api_session_stop(self):
        """POST /api/session/stop — stop tmux session."""
        if not self.tmux_manager:
            return self._no_tmux()
        self.tmux_manager.stop()
        return jsonify({"ok": True, **self.tmux_manager.status()})

    def api_session_restart(self):
        """POST /api/session/restart — stop then start (non-blocking)."""
        if not self.tmux_manager:
            return self._no_tmux()
        threading.Thread(target=self.tmux_manager.restart, daemon=True, name="session-restart").start()
        return jsonify({"ok": True, "starting": True, **self.tmux_manager.status()})

    # ------------------------------------------------------------------ #
    #  HTMX partial handlers
    # ------------------------------------------------------------------ #

    def partial_status(self):
        return render_template("_status.html",   s=self.state.get_snapshot())

    def partial_progress(self):
        return render_template("_progress.html", s=self.state.get_snapshot())

    def partial_history(self):
        return render_template("_history.html",  s=self.state.get_snapshot())

    def partial_logs(self):
        return render_template("_logs.html",     s=self.state.get_snapshot())

    # ------------------------------------------------------------------ #
    #  Page
    # ------------------------------------------------------------------ #

    def index(self):
        return render_template(
            "index.html",
            snapshot=self.state.get_snapshot(),
            workflows=self.picker.list_workflows(),
        )
