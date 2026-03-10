"""
Cards Renderer — Flask application factory.

All route logic lives in web/routes.py (DashboardRouter).
This module is intentionally thin: it creates the Flask instance
and delegates route registration to DashboardRouter.

Endpoints (defined in routes.py):
    GET /                   Dashboard page
    GET /api/status         JSON: current card, progress, workflow info
    GET /api/workflows      JSON: available workflows
    GET /api/history        JSON: completed task summaries
    GET /api/current-task   Raw current_task.md content
    GET /api/logs           JSON: recent log lines
    GET /api/workspace-scan JSON: recently modified workspace files

    HTMX partials (return HTML fragments):
    GET /partials/status    Status panel HTML
    GET /partials/history   History feed HTML
    GET /partials/progress  Progress bar HTML
    GET /partials/logs      Logs panel HTML
"""

from __future__ import annotations

import sys
from pathlib import Path

from flask import Flask

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import EngineConfig
from core.state_manager import StateManager
from engine.picker import CardsPicker
from engine.scanner import WorkspaceScanner
from web.routes import DashboardRouter


def create_app(
    config:  EngineConfig,
    state:   StateManager,
    picker:  CardsPicker,
    scanner: WorkspaceScanner,
) -> Flask:
    """
    Factory function — creates and configures the Flask app.

    Accepts shared config, state, picker, and scanner instances
    and wires them into a DashboardRouter.
    """
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(Path(__file__).parent / "static"),
    )
    DashboardRouter(config, state, picker, scanner).register(app)
    return app
