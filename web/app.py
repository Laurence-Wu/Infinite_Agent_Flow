"""
Cards Renderer — Flask web dashboard with HTMX-powered auto-refresh.

Endpoints:
    GET /                   Dashboard page
    GET /api/status         JSON: current card, progress, workflow info
    GET /api/workflows      JSON: available workflows
    GET /api/history        JSON: completed task summaries
    GET /api/current-task   Raw current_task.md content

    HTMX partials (return HTML fragments):
    GET /partials/status    Status panel HTML
    GET /partials/history   History feed HTML
    GET /partials/progress  Progress bar HTML
"""

from __future__ import annotations

import sys
from pathlib import Path

from flask import Flask, jsonify, render_template, Response

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import EngineConfig
from core.state_manager import StateManager
from engine.picker import CardsPicker


def create_app(
    config: EngineConfig,
    state: StateManager,
    picker: CardsPicker,
) -> Flask:
    """
    Factory function — creates and configures the Flask app.
    Injected with shared config, state, and picker instances.
    """
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(Path(__file__).parent / "static"),
    )

    # ------------------------------------------------------------------ #
    #  Pages
    # ------------------------------------------------------------------ #

    @app.route("/")
    def index():
        snapshot = state.get_snapshot()
        workflows = picker.list_workflows()
        return render_template(
            "index.html",
            snapshot=snapshot,
            workflows=workflows,
        )

    # ------------------------------------------------------------------ #
    #  JSON API endpoints
    # ------------------------------------------------------------------ #

    @app.route("/api/status")
    def api_status():
        return jsonify(state.get_snapshot())

    @app.route("/api/workflows")
    def api_workflows():
        return jsonify(picker.list_workflows())

    @app.route("/api/history")
    def api_history():
        snapshot = state.get_snapshot()
        return jsonify(snapshot.get("history", []))

    @app.route("/api/current-task")
    def api_current_task():
        task_file = config.task_file
        if task_file.exists():
            content = task_file.read_text(encoding="utf-8")
            return Response(content, mimetype="text/markdown")
        return Response("No active task.", mimetype="text/plain", status=404)

    # ------------------------------------------------------------------ #
    #  HTMX partial endpoints (return HTML fragments)
    # ------------------------------------------------------------------ #

    @app.route("/partials/status")
    def partial_status():
        snapshot = state.get_snapshot()
        return render_template("_status.html", s=snapshot)

    @app.route("/partials/progress")
    def partial_progress():
        snapshot = state.get_snapshot()
        return render_template("_progress.html", s=snapshot)

    @app.route("/partials/history")
    def partial_history():
        snapshot = state.get_snapshot()
        return render_template("_history.html", s=snapshot)

    return app
