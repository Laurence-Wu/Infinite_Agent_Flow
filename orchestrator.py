"""
AgentOrchestrator — Main entry point for the Card Dealer engine.

Ties together: EngineConfig, StateManager, CardsPicker, CardsDealer,
CardsPlanner, and the Flask web dashboard.

Usage:
    python orchestrator.py --workspace ./output --workflow sample_workflow --version v1
"""

from __future__ import annotations

import argparse
import logging
import sys
import threading
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.config import EngineConfig
from core.state_manager import StateManager
from engine.dealer import CardsDealer
from engine.picker import CardsPicker
from engine.planner import CardsPlanner
from web.app import create_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("orchestrator")


class _StateLogHandler(logging.Handler):
    """Captures log records into the StateManager's ring buffer for the dashboard."""

    def __init__(self, state: "StateManager"):
        super().__init__()
        self._state = state
        self.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        ))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._state.push_log(self.format(record))
        except Exception:
            pass


class AgentOrchestrator:
    """
    Public API for the Card Dealer engine.

    Accepts the target workspace directory, spins up all components,
    starts the Flask dashboard in a daemon thread, then runs the
    Planner's watchdog-based main loop.
    """

    def __init__(
        self,
        workspace_path: str,
        workflow_name: str,
        version: str,
        workflows_path: str | None = None,
        flask_port: int = 5000,
    ):
        # ---- Config ----
        wf_path = workflows_path or str(PROJECT_ROOT / "workflows")
        self.config = EngineConfig(
            workspace_path=workspace_path,
            workflows_path=wf_path,
            flask_port=flask_port,
        )

        # ---- Shared state ----
        self.state = StateManager()

        # ---- Log capture → dashboard ring buffer ----
        _log_handler = _StateLogHandler(self.state)
        logging.getLogger().addHandler(_log_handler)

        # ---- Engine components ----
        self.picker = CardsPicker(self.config)
        self.dealer = CardsDealer(self.config, self.state)
        self.planner = CardsPlanner(self.config, self.state, self.picker, self.dealer)

        # ---- Web dashboard ----
        self.app = create_app(self.config, self.state, self.picker)

        # ---- Workflow identity ----
        self._workflow_name = workflow_name
        self._version = version

    # ------------------------------------------------------------------ #
    #  Public methods
    # ------------------------------------------------------------------ #

    def run(self) -> None:
        """
        Start the dashboard (background thread), then run the planner
        in the foreground (blocks until workflow completes).
        """
        self._start_web()
        logger.info(
            "Dashboard running at http://%s:%d",
            self.config.flask_host,
            self.config.flask_port,
        )
        logger.info(
            "Starting workflow: %s/%s → workspace: %s",
            self._workflow_name,
            self._version,
            self.config.resolved_workspace,
        )

        try:
            self.planner.run(self._workflow_name, self._version)
        except KeyboardInterrupt:
            logger.info("Interrupted by user.")
            self.planner.stop()

    def deal_next(self) -> None:
        """Manually advance one card (useful for interactive/debug mode)."""
        snapshot = self.state.get_snapshot()
        current_id = snapshot.get("current_card_id")

        if current_id is None:
            # No card dealt yet — deal the first one
            card = self.picker.get_first_card(self._workflow_name, self._version)
        else:
            card = self.picker.get_next_card(
                self._workflow_name, self._version, current_id
            )
            if card is None:
                logger.info("Workflow already finished.")
                return

        total = self.picker.get_total_cards(self._workflow_name, self._version)
        idx = self.picker.get_card_index(
            self._workflow_name, self._version, card.id
        )
        self.dealer.deal_card(card, card_index=idx, total_cards=total)
        logger.info("Manually dealt card: %s", card.id)

    # ------------------------------------------------------------------ #
    #  Internal
    # ------------------------------------------------------------------ #

    def _start_web(self) -> None:
        """Start Flask in a daemon thread (non-blocking)."""
        thread = threading.Thread(
            target=self.app.run,
            kwargs={
                "host": self.config.flask_host,
                "port": self.config.flask_port,
                "debug": False,
                "use_reloader": False,
            },
            daemon=True,
            name="flask-dashboard",
        )
        thread.start()


# ---------------------------------------------------------------------- #
#  CLI
# ---------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(
        description="CardDealer — Agent Instruction Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example:\n"
            "  python orchestrator.py --workspace ./output "
            "--workflow sample_workflow --version v1"
        ),
    )
    parser.add_argument(
        "--workspace", "-w",
        required=True,
        help="Target directory where current_task.md and archive are managed.",
    )
    parser.add_argument(
        "--workflow", "-f",
        required=True,
        help="Name of the workflow to run (directory name under workflows/).",
    )
    parser.add_argument(
        "--version", "-v",
        default="v1",
        help="Workflow version (default: v1).",
    )
    parser.add_argument(
        "--workflows-path",
        default=None,
        help="Custom path to the workflows root directory.",
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=5000,
        help="Flask dashboard port (default: 5000).",
    )

    args = parser.parse_args()

    orchestrator = AgentOrchestrator(
        workspace_path=args.workspace,
        workflow_name=args.workflow,
        version=args.version,
        workflows_path=args.workflows_path,
        flask_port=args.port,
    )
    orchestrator.run()


if __name__ == "__main__":
    main()
