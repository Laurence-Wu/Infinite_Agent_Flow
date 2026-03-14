"""
Cards Renderer — Flask application factory.

All route logic lives in web/routes.py (DashboardRouter).
This module is intentionally thin: it creates the Flask instance
and delegates route registration to DashboardRouter.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from flask import Flask
from flask_cors import CORS

from core.config import EngineConfig
from core.state_manager import StateManager
from engine.picker import CardsPicker
from engine.scanner import WorkspaceScanner
from web.routes import DashboardRouter


def create_app(
    config:       EngineConfig,
    state:        StateManager,
    picker:       CardsPicker,
    scanner:      WorkspaceScanner,
    registry:     Optional[Any] = None,   # core.agent_manager.AgentRegistry
    archive:      Optional[Any] = None,   # core.archive.ArchiveManager
    tmux_manager: Optional[Any] = None,   # core.tmux_manager.TmuxManager
) -> Flask:
    """
    Factory function — creates and configures the Flask app.

    Pass ``registry`` to enable agent-control REST endpoints.
    Pass ``archive`` to enable archive browsing endpoints.
    Pass ``tmux_manager`` to enable /api/session/* endpoints.
    """
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(Path(__file__).parent / "static"),
    )

    # Allow the Next.js dev server (port 3000) to connect directly to the
    # SSE stream endpoint, bypassing the Next.js proxy.
    CORS(app, resources={r"/api/agent/stream": {"origins": "*"}})

    DashboardRouter(config, state, picker, scanner,
                    registry=registry, archive=archive,
                    tmux_manager=tmux_manager).register(app)
    return app
