"""
DashboardRouter — registers all Flask routes as class methods.

All route logic lives here; web/app.py is a thin factory that
instantiates this class and calls register().
"""

from __future__ import annotations

from pathlib import Path

from flask import Flask, Response, jsonify, render_template

from core.config import EngineConfig
from core.state_manager import StateManager
from engine.picker import CardsPicker
from engine.scanner import WorkspaceScanner


class DashboardRouter:
    """
    Encapsulates every HTTP route handler.

    Dependencies are injected once at construction so each method
    has access to config/state/picker/scanner without closures.

    Usage:
        router = DashboardRouter(config, state, picker, scanner)
        router.register(app)
    """

    def __init__(
        self,
        config:  EngineConfig,
        state:   StateManager,
        picker:  CardsPicker,
        scanner: WorkspaceScanner,
    ) -> None:
        self.config  = config
        self.state   = state
        self.picker  = picker
        self.scanner = scanner

    def register(self, app: Flask) -> None:
        """Bind all routes to the Flask application."""
        # ── JSON API ──────────────────────────────────────────────────────
        app.add_url_rule("/api/status",        "api_status",         self.api_status)
        app.add_url_rule("/api/workflows",      "api_workflows",      self.api_workflows)
        app.add_url_rule("/api/history",        "api_history",        self.api_history)
        app.add_url_rule("/api/current-task",   "api_current_task",   self.api_current_task)
        app.add_url_rule("/api/logs",           "api_logs",           self.api_logs)
        app.add_url_rule("/api/workspace-scan", "api_workspace_scan", self.api_workspace_scan)
        # ── HTMX partials ─────────────────────────────────────────────────
        app.add_url_rule("/partials/status",    "partial_status",     self.partial_status)
        app.add_url_rule("/partials/progress",  "partial_progress",   self.partial_progress)
        app.add_url_rule("/partials/history",   "partial_history",    self.partial_history)
        app.add_url_rule("/partials/logs",      "partial_logs",       self.partial_logs)
        # ── Page ──────────────────────────────────────────────────────────
        app.add_url_rule("/", "index", self.index)

    # ── JSON handlers ─────────────────────────────────────────────────────

    def api_status(self):
        return jsonify(self.state.get_snapshot())

    def api_workflows(self):
        return jsonify(self.picker.list_workflows())

    def api_history(self):
        return jsonify(self.state.get_snapshot().get("history", []))

    def api_current_task(self):
        task_file = self.config.task_file
        if task_file.exists():
            return Response(task_file.read_text(encoding="utf-8"), mimetype="text/markdown")
        return Response("No active task.", mimetype="text/plain", status=404)

    def api_logs(self):
        return jsonify({"logs": self.state.get_snapshot().get("log_lines", [])})

    def api_workspace_scan(self):
        return jsonify({"files": self.scanner.scan()})

    # ── HTMX partial handlers ─────────────────────────────────────────────

    def partial_status(self):
        return render_template("_status.html",   s=self.state.get_snapshot())

    def partial_progress(self):
        return render_template("_progress.html", s=self.state.get_snapshot())

    def partial_history(self):
        return render_template("_history.html",  s=self.state.get_snapshot())

    def partial_logs(self):
        return render_template("_logs.html",     s=self.state.get_snapshot())

    # ── Page ──────────────────────────────────────────────────────────────

    def index(self):
        return render_template(
            "index.html",
            snapshot=self.state.get_snapshot(),
            workflows=self.picker.list_workflows(),
        )
