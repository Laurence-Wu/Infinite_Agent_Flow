"""
DashboardRouter — registers all Flask routes as class methods.

All route logic lives here; web/app.py is a thin factory that
instantiates this class and calls register().

Card Dealer endpoints  (workflow runner control — require DealerRegistry):
    GET  /api/dealers                        — list all registered dealers
    POST /api/dealers                        — start new dealer (workspace/workflow/version)
    GET  /api/dealer/<id>                    — full snapshot for one dealer
    GET  /api/dealer/<id>/logs               — log lines for one dealer
    GET  /api/dealer/<id>/history            — completion history for one dealer
    POST /api/dealer/<id>/pause              — pause dealer
    POST /api/dealer/<id>/resume             — resume dealer
    POST /api/dealer/<id>/stop               — stop dealer
    POST /api/dealer/<id>/deal               — deal next card
    POST /api/dealer/<id>/restart            — stop then respawn dealer with same config
    GET  /api/dealer/<id>/workspace-scan     — scan this dealer's workspace directory
    POST /api/report-state                   — peer state report from remote dealers

Agent endpoints  (AI tmux process control — require TmuxManager):
    GET  /api/agent                          — tmux session status + pane output
    GET  /api/agent/stream                   — SSE stream of live pane output
    POST /api/agent/start                    — start AI agent (non-blocking)
    POST /api/agent/stop                     — stop AI agent
    POST /api/agent/pause                    — send Esc to pause mid-generation
    POST /api/agent/restart                  — restart AI agent (non-blocking)

Archive routes  (require ArchiveManager):
    GET  /api/archive                        — list recent archive entries
    GET  /api/archive/<loop>/<folder>        — single archive entry detail

Backward-compat aliases  (kept so existing scripts/UI code still works):
    GET  /api/agents                 → /api/dealers
    POST /api/agents                 → /api/dealers  (start dealer)
    GET  /api/agent/<id>             → /api/dealer/<id>
    GET  /api/agent/<id>/logs        → /api/dealer/<id>/logs
    GET  /api/agent/<id>/history     → /api/dealer/<id>/history
    POST /api/agent/<id>/pause       → /api/dealer/<id>/pause
    POST /api/agent/<id>/resume      → /api/dealer/<id>/resume
    POST /api/agent/<id>/stop        → /api/dealer/<id>/stop
    POST /api/agent/<id>/deal        → /api/dealer/<id>/deal
    POST /api/agent/<id>/restart     → /api/dealer/<id>/restart
    GET  /api/agent/<id>/workspace-scan → /api/dealer/<id>/workspace-scan
    GET  /api/session                → /api/agent
    POST /api/session/start          → /api/agent/start
    POST /api/session/stop           → /api/agent/stop
    POST /api/session/restart        → /api/agent/restart
    GET  /api/status                 — snapshot for queried dealer_id
    POST /api/workflow/pause         — pause (body: {agent_id})
    POST /api/workflow/resume        — resume (body: {agent_id})
    POST /api/workflow/stop          — stop   (body: {agent_id})
    POST /api/deal-next              — deal next (body: {agent_id})
"""

from __future__ import annotations

import functools
import threading
from pathlib import Path
from typing import Any, Optional

from flask import Flask, Response, jsonify, render_template, request

from core.config import EngineConfig
from core.state_manager import StateManager
from core.tmux_detector import AgentState
from engine.picker import CardsPicker
from engine.scanner import WorkspaceScanner


def _require_registry(fn):
    """Guard: return 503 when self.registry is None."""
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        if self.registry is None:
            return jsonify({"error": "DealerRegistry not available"}), 503
        return fn(self, *args, **kwargs)
    return wrapper


def _require_tmux(fn):
    """Guard: return 503 when self.tmux_manager is None."""
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        if not self.tmux_manager:
            return jsonify({"ok": False, "error": "TmuxManager not configured"}), 503
        return fn(self, *args, **kwargs)
    return wrapper


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
        registry:     Optional[Any] = None,   # DealerRegistry | None
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
        # Cache of metadata for remote (peer-attached) agents keyed by agent_id.
        # Populated by api_report_state; used to include remote agents in api_dealers.
        self._remote_agents: dict = {}

    def register(self, app: Flask) -> None:
        """Bind all routes to the Flask application."""

        # ── Card Dealer list & control (canonical) ────────────────────────
        app.add_url_rule("/api/dealers",                       "api_dealers",                self.api_dealers)
        app.add_url_rule("/api/dealers",                       "api_dealers_start",          self.api_dealers_start,          methods=["POST"])
        app.add_url_rule("/api/dealer/<dealer_id>",            "api_dealer",                 self.api_dealer)
        app.add_url_rule("/api/dealer/<dealer_id>/logs",       "api_dealer_logs",            self.api_dealer_logs)
        app.add_url_rule("/api/dealer/<dealer_id>/history",    "api_dealer_history",         self.api_dealer_history)
        app.add_url_rule("/api/dealer/<dealer_id>/pause",      "api_dealer_pause",           self.api_dealer_pause,           methods=["POST"])
        app.add_url_rule("/api/dealer/<dealer_id>/resume",     "api_dealer_resume",          self.api_dealer_resume,          methods=["POST"])
        app.add_url_rule("/api/dealer/<dealer_id>/stop",       "api_dealer_stop",            self.api_dealer_stop,            methods=["POST"])
        app.add_url_rule("/api/dealer/<dealer_id>/deal",       "api_dealer_deal",            self.api_dealer_deal,            methods=["POST"])
        app.add_url_rule("/api/dealer/<dealer_id>/restart",    "api_dealer_restart",         self.api_dealer_restart,         methods=["POST"])
        app.add_url_rule("/api/dealer/<dealer_id>/workspace-scan", "api_dealer_workspace_scan", self.api_dealer_workspace_scan)
        app.add_url_rule("/api/dealer/<dealer_id>/session",        "api_dealer_session",        self.api_dealer_session)
        app.add_url_rule("/api/dealer/<dealer_id>/stream",         "api_dealer_stream",         self.api_dealer_stream)
        app.add_url_rule("/api/dealer/<dealer_id>/pane-update",    "api_dealer_pane_update",    self.api_dealer_pane_update, methods=["POST"])

        # ── Peer state reporting ──────────────────────────────────────────
        app.add_url_rule("/api/report-state", "api_report_state", self.api_report_state, methods=["POST"])

        # ── Agent (AI tmux process) control (canonical) ───────────────────
        app.add_url_rule("/api/agent",          "api_agent",          self.api_agent)
        app.add_url_rule("/api/agent/start",   "api_agent_start",   self.api_agent_start,   methods=["POST"])
        app.add_url_rule("/api/agent/stop",    "api_agent_stop",    self.api_agent_stop,    methods=["POST"])
        app.add_url_rule("/api/agent/pause",   "api_agent_pause",   self.api_agent_pause,   methods=["POST"])
        app.add_url_rule("/api/agent/restart", "api_agent_restart", self.api_agent_restart, methods=["POST"])
        app.add_url_rule("/api/agent/stream",  "api_agent_stream",  self.api_agent_stream)

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

        # ── Backward-compat dealer aliases (old /api/agents, /api/agent/<id>) ──
        app.add_url_rule("/api/agents",                            "compat_dealers_get",             self.api_dealers)
        app.add_url_rule("/api/agents",                            "compat_dealers_post",            self.api_dealers_start,          methods=["POST"])
        app.add_url_rule("/api/agent/<dealer_id>",                 "compat_dealer",                  self.api_dealer)
        app.add_url_rule("/api/agent/<dealer_id>/logs",            "compat_dealer_logs",             self.api_dealer_logs)
        app.add_url_rule("/api/agent/<dealer_id>/history",         "compat_dealer_history",          self.api_dealer_history)
        app.add_url_rule("/api/agent/<dealer_id>/pause",           "compat_dealer_pause",            self.api_dealer_pause,           methods=["POST"])
        app.add_url_rule("/api/agent/<dealer_id>/resume",          "compat_dealer_resume",           self.api_dealer_resume,          methods=["POST"])
        app.add_url_rule("/api/agent/<dealer_id>/stop",            "compat_dealer_stop",             self.api_dealer_stop,            methods=["POST"])
        app.add_url_rule("/api/agent/<dealer_id>/deal",            "compat_dealer_deal",             self.api_dealer_deal,            methods=["POST"])
        app.add_url_rule("/api/agent/<dealer_id>/restart",         "compat_dealer_restart",          self.api_dealer_restart,         methods=["POST"])
        app.add_url_rule("/api/agent/<dealer_id>/workspace-scan",  "compat_dealer_workspace_scan",   self.api_dealer_workspace_scan)

        # ── Backward-compat session aliases (old /api/session) ───────────
        app.add_url_rule("/api/session",         "compat_session",         self.api_agent)
        app.add_url_rule("/api/session/start",   "compat_session_start",   self.api_agent_start,   methods=["POST"])
        app.add_url_rule("/api/session/stop",    "compat_session_stop",    self.api_agent_stop,    methods=["POST"])
        app.add_url_rule("/api/session/pause",   "compat_session_pause",   self.api_agent_pause,   methods=["POST"])
        app.add_url_rule("/api/session/restart", "compat_session_restart", self.api_agent_restart, methods=["POST"])

        # ── Backward-compat control aliases (old body-style endpoints) ────
        app.add_url_rule("/api/workflow/pause",  "compat_pause",  self.compat_pause,  methods=["POST"])
        app.add_url_rule("/api/workflow/resume", "compat_resume", self.compat_resume, methods=["POST"])
        app.add_url_rule("/api/workflow/stop",   "compat_stop",   self.compat_stop,   methods=["POST"])
        app.add_url_rule("/api/deal-next",       "compat_deal",   self.compat_deal,   methods=["POST"])

        # ── HTMX partials ─────────────────────────────────────────────────
        app.add_url_rule("/partials/status",   "partial_status",   self.partial_status)
        app.add_url_rule("/partials/progress", "partial_progress", self.partial_progress)
        app.add_url_rule("/partials/history",  "partial_history",  self.partial_history)
        app.add_url_rule("/partials/logs",     "partial_logs",     self.partial_logs)

        # ── Page ──────────────────────────────────────────────────────────
        app.add_url_rule("/", "index", self.index)

    # ------------------------------------------------------------------ #
    #  Card Dealer list + control
    # ------------------------------------------------------------------ #

    def api_dealers(self):
        """GET /api/dealers — list all registered dealers as a JSON array."""
        if self.registry:
            dealers = self.registry.list_dealers()
            # Merge remote (peer-attached) agents that reported via api_report_state
            registered_ids = {d["dealer_id"] for d in dealers}
            for aid, meta in list(self._remote_agents.items()):
                if aid in registered_ids:
                    continue
                snap = self.state.get_snapshot(aid)
                dealers.append({
                    "dealer_id":       aid,
                    "workspace":       meta.get("workspace", ""),
                    "workflow":        snap.get("current_workflow", meta.get("workflow", "")),
                    "version":         snap.get("current_version",  meta.get("version",  "")),
                    "status":          snap.get("status", "unknown"),
                    "current_card_id": snap.get("current_card_id"),
                    "started_at":      snap.get("started_at"),
                    "last_updated":    snap.get("last_updated"),
                    "is_paused":       False,
                    "cycles_completed": snap.get("cycles_completed", 0),
                    "completed_total": snap.get("completed_total", 0),
                    "progress_pct":    snap.get("progress_pct", 0),
                    "card_index":      snap.get("card_index", 0),
                    "total_cards":     snap.get("total_cards", 0),
                    "error":           snap.get("error"),
                })
            return jsonify(dealers)
        snaps = self.state.get_all_snapshots()
        return jsonify(list(snaps.values()))

    @_require_registry
    def api_dealers_start(self):
        """POST /api/dealers — start a new dealer."""
        body = request.get_json() or {}
        workspace = body.get("workspace")
        workflow  = body.get("workflow")
        version   = body.get("version", "v1")
        if not workspace or not workflow:
            return jsonify({"error": "workspace and workflow are required"}), 400
        dealer_id = self.registry.start_dealer(workspace, workflow, version)
        return jsonify({"ok": True, "dealer_id": dealer_id}), 201

    def api_dealer(self, dealer_id: str):
        """GET /api/dealer/<id> — full snapshot for one dealer."""
        if self.registry:
            snap = self.registry.get_dealer_snapshot(dealer_id)
            if snap is None:
                return jsonify({"error": f"Dealer '{dealer_id}' not found"}), 404
            return jsonify(snap)
        snap = self.state.get_snapshot(dealer_id)
        return jsonify(snap)

    def api_dealer_logs(self, dealer_id: str):
        """GET /api/dealer/<id>/logs — log lines for one dealer."""
        snap = self.state.get_snapshot(dealer_id)
        return jsonify({"dealer_id": dealer_id, "logs": snap.get("log_lines", [])})

    def api_dealer_history(self, dealer_id: str):
        """GET /api/dealer/<id>/history — completion history for one dealer."""
        snap = self.state.get_snapshot(dealer_id)
        return jsonify({"dealer_id": dealer_id, "history": snap.get("history", [])})

    @_require_registry
    def api_dealer_pause(self, dealer_id: str):
        """POST /api/dealer/<id>/pause."""
        ok = self.registry.pause_dealer(dealer_id)
        return jsonify({"ok": ok, "dealer_id": dealer_id})

    @_require_registry
    def api_dealer_resume(self, dealer_id: str):
        """POST /api/dealer/<id>/resume."""
        ok = self.registry.resume_dealer(dealer_id)
        return jsonify({"ok": ok, "dealer_id": dealer_id})

    @_require_registry
    def api_dealer_stop(self, dealer_id: str):
        """POST /api/dealer/<id>/stop."""
        ok = self.registry.stop_dealer(dealer_id)
        return jsonify({"ok": ok, "dealer_id": dealer_id})

    @_require_registry
    def api_dealer_deal(self, dealer_id: str):
        """POST /api/dealer/<id>/deal — manually advance one card."""
        result = self.registry.deal_next(dealer_id)
        code = 200 if result.get("ok") else 500
        return jsonify(result), code

    @_require_registry
    def api_dealer_restart(self, dealer_id: str):
        """POST /api/dealer/<id>/restart — stop current run and start a fresh one."""
        dealers = self.registry.list_dealers()
        entry = next((d for d in dealers if d["dealer_id"] == dealer_id), None)
        if entry is None:
            return jsonify({"error": f"Dealer '{dealer_id}' not found"}), 404
        self.registry.stop_dealer(dealer_id)
        new_id = self.registry.start_dealer(
            entry["workspace"], entry["workflow"], entry["version"],
            dealer_id=dealer_id,
        )
        return jsonify({"ok": True, "dealer_id": new_id})

    def api_dealer_workspace_scan(self, dealer_id: str):
        """GET /api/dealer/<id>/workspace-scan — scan this dealer's workspace directory."""
        if not self.registry:
            return jsonify({"files": []})
        snap = self.registry.get_dealer_snapshot(dealer_id)
        ws_path = (snap or {}).get("workspace", "")
        if not ws_path:
            return jsonify({"files": []})
        cfg = EngineConfig(workspace_path=ws_path)
        return jsonify({"files": WorkspaceScanner(cfg).scan()})

    # ------------------------------------------------------------------ #
    #  Peer state reporting
    # ------------------------------------------------------------------ #

    def api_report_state(self):
        """POST /api/report-state — accept a state snapshot from a remote dealer."""
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing JSON body"}), 400
        self.state.update_from_snapshot(data)
        # Cache metadata for remote agent so api_dealers can include it
        aid = data.get("agent_id")
        if aid:
            self._remote_agents.setdefault(aid, {})
            if data.get("workspace"):
                self._remote_agents[aid]["workspace"] = data["workspace"]
            if data.get("current_workflow"):
                self._remote_agents[aid]["workflow"] = data["current_workflow"]
            if data.get("current_version"):
                self._remote_agents[aid]["version"] = data["current_version"]
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
        dealer_id = request.args.get("agent_id") or request.args.get("dealer_id")
        return jsonify(self.state.get_snapshot(dealer_id))

    def api_workflows(self):
        return jsonify(self.picker.list_workflows())

    def api_history(self):
        dealer_id = request.args.get("agent_id") or request.args.get("dealer_id")
        snap = self.state.get_snapshot(dealer_id)
        return jsonify(snap.get("history", []))

    def api_current_task(self):
        task_file = self.config.task_file
        if task_file.exists():
            return Response(task_file.read_text(encoding="utf-8"), mimetype="text/markdown")
        return Response("No active task.", mimetype="text/plain", status=404)

    def api_logs(self):
        dealer_id = request.args.get("agent_id") or request.args.get("dealer_id")
        snap = self.state.get_snapshot(dealer_id)
        return jsonify({"logs": snap.get("log_lines", [])})

    def api_workspace_scan(self):
        return jsonify({"files": self.scanner.scan()})

    # ------------------------------------------------------------------ #
    #  Backward-compat body-style control aliases
    # ------------------------------------------------------------------ #

    def _dealer_id_from_body(self) -> str:
        body = request.get_json(silent=True) or {}
        return body.get("dealer_id") or body.get("agent_id", "default")

    @_require_registry
    def compat_pause(self):
        dealer_id = self._dealer_id_from_body()
        ok = self.registry.pause_dealer(dealer_id)
        return jsonify({"ok": ok, "dealer_id": dealer_id})

    @_require_registry
    def compat_resume(self):
        dealer_id = self._dealer_id_from_body()
        ok = self.registry.resume_dealer(dealer_id)
        return jsonify({"ok": ok, "dealer_id": dealer_id})

    @_require_registry
    def compat_stop(self):
        dealer_id = self._dealer_id_from_body()
        ok = self.registry.stop_dealer(dealer_id)
        return jsonify({"ok": ok, "dealer_id": dealer_id})

    @_require_registry
    def compat_deal(self):
        dealer_id = self._dealer_id_from_body()
        result = self.registry.deal_next(dealer_id)
        code = 200 if result.get("ok") else 500
        return jsonify(result), code

    # ------------------------------------------------------------------ #
    #  Agent (AI tmux process) endpoints
    # ------------------------------------------------------------------ #

    def _agent_preflight(
        self, *, block_intervention: bool = True
    ) -> "tuple[AgentState, tuple | None]":
        """
        Probe the current agent state.

        Returns (state, error_response) where error_response is non-None only
        when the state blocks the requested operation.  The caller should
        return early with error_response when it is not None.

        Parameters
        ----------
        block_intervention :
            When False, NEEDS_INTERVENTION is not treated as a blocker.
            Use this for restart — the user may have fixed the issue and
            wants a clean relaunch.
        """
        state = self.tmux_manager.probe_state()
        if state == AgentState.QUOTA_EXCEEDED:
            return state, (
                jsonify({
                    "ok":    False,
                    "error": "Agent quota exceeded — check your Gemini API quota.",
                    "agent_state": state.value,
                }),
                503,
            )
        if block_intervention and state == AgentState.NEEDS_INTERVENTION:
            pane = self.tmux_manager.capture(20)
            return state, (
                jsonify({
                    "ok":         False,
                    "error":      "Agent needs intervention (auth error or fatal crash).",
                    "agent_state": state.value,
                    "pane_tail":  pane[-10:] if pane else [],
                }),
                503,
            )
        return state, None

    @_require_tmux
    def api_agent(self):
        """GET /api/agent — AI agent (tmux session) status + pane output."""
        state = self.tmux_manager.probe_state()
        return jsonify({"agent_state": state.value, **self.tmux_manager.status()})

    @_require_tmux
    def api_agent_start(self):
        """POST /api/agent/start — start AI agent (non-blocking; returns immediately)."""
        state, err = self._agent_preflight()
        if err:
            return err
        threading.Thread(target=self.tmux_manager.start, daemon=True, name="agent-start").start()
        return jsonify({"ok": True, "starting": True, "agent_state": state.value,
                        **self.tmux_manager.status()})

    @_require_tmux
    def api_agent_stop(self):
        """POST /api/agent/stop — stop AI agent."""
        state, err = self._agent_preflight()
        if err:
            return err
        self.tmux_manager.stop()
        return jsonify({"ok": True, **self.tmux_manager.status()})

    @_require_tmux
    def api_agent_pause(self):
        """POST /api/agent/pause — send Esc to pause mid-generation."""
        state, err = self._agent_preflight()
        if err:
            return err
        if state == AgentState.DEAD:
            return jsonify({"ok": False, "error": "Agent is not running.", "agent_state": state.value}), 409
        self.tmux_manager.pause()
        return jsonify({"ok": True, **self.tmux_manager.status()})

    @_require_tmux
    def api_agent_restart(self):
        """POST /api/agent/restart — stop then start AI agent (non-blocking).
        NEEDS_INTERVENTION allows restart (user may have fixed the issue);
        QUOTA_EXCEEDED blocks it."""
        state, err = self._agent_preflight(block_intervention=False)
        if err:
            return err
        threading.Thread(target=self.tmux_manager.restart, daemon=True, name="agent-restart").start()
        return jsonify({"ok": True, "starting": True, "agent_state": state.value,
                        **self.tmux_manager.status()})

    @_require_tmux
    def api_agent_stream(self):
        """GET /api/agent/stream — SSE stream of live pane output lines."""
        def generate():
            try:
                for line in self.tmux_manager.stream_lines(timeout=30.0):
                    if line.startswith(":"):
                        # SSE keep-alive comment — pass through as-is
                        yield f"{line}\n\n"
                    else:
                        yield f"data: {line}\n\n"
            except GeneratorExit:
                pass

        return Response(
            generate(),
            mimetype="text/event-stream",
            headers={
                "Cache-Control":     "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    # ------------------------------------------------------------------ #
    #  Per-dealer tmux session endpoints
    # ------------------------------------------------------------------ #

    def api_dealer_session(self, dealer_id: str):
        """GET /api/dealer/<id>/session — tmux status for a specific dealer."""
        if self.registry is None:
            return jsonify({"error": "no registry"}), 503
        status = self.registry.get_tmux_status(dealer_id)
        if status is None:
            return jsonify({
                "alive": False, "starting": False,
                "session_name": "", "agent_command": "",
                "workspace": "", "pane_lines": [],
            })
        return jsonify(status)

    def api_dealer_stream(self, dealer_id: str):
        """GET /api/dealer/<id>/stream — SSE stream for a specific dealer's tmux pane."""
        if self.registry is None:
            return jsonify({"error": "no registry"}), 503
        mgr = self.registry.get_tmux_manager(dealer_id)
        if mgr is None:
            # No live TmuxManager — fall back to a keep-alive stream
            def _noop():
                try:
                    while True:
                        yield ": keep-alive\n\n"
                        import time; time.sleep(15)
                except GeneratorExit:
                    pass
            return Response(_noop(), mimetype="text/event-stream",
                            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

        def generate():
            try:
                for line in mgr.stream_lines(timeout=30.0):
                    if line.startswith(":"):
                        yield f"{line}\n\n"
                    else:
                        yield f"data: {line}\n\n"
            except GeneratorExit:
                pass

        return Response(generate(), mimetype="text/event-stream",
                        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    def api_dealer_pane_update(self, dealer_id: str):
        """POST /api/dealer/<id>/pane-update — attached agent pushes its tmux snapshot."""
        if self.registry is None:
            return jsonify({"ok": False}), 503
        data = request.get_json(silent=True) or {}
        self.registry.update_pane_cache(dealer_id, data)
        return jsonify({"ok": True})

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
