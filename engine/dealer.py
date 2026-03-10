"""
CardsDealer — Markdown file manager and instruction formatter.

Receives a Card from the Picker, dynamically builds the instruction
wrapper chain based on card metadata, and writes the formatted
markdown to the workspace's current_task.md.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.base_card import BaseCard
from core.config import EngineConfig
from core.exceptions import TaskFileError
from core.state_manager import StateManager
from core.wrappers import InstructionWrapper

logger = logging.getLogger(__name__)


class CardsDealer:
    """
    Formats card instructions into markdown task files.
    Updates the StateManager after writing.
    """

    def __init__(
        self,
        config: EngineConfig,
        state: StateManager,
        base_wrapper: Optional[InstructionWrapper] = None,
    ):
        self._config = config
        self._state = state
        self._base_wrapper = base_wrapper or InstructionWrapper()

    # ------------------------------------------------------------------ #
    #  Primary API
    # ------------------------------------------------------------------ #

    def deal_card(
        self,
        card: BaseCard,
        card_index: int,
        total_cards: int,
    ) -> Path:
        """
        Write a card's instruction into current_task.md.

        1. Build the wrapper chain based on card metadata.
        2. Format the full markdown document.
        3. Write to disk.
        4. Update StateManager.

        Returns the Path to the written file.
        """
        wrapper = self._build_wrapper(card, card_index=card_index)
        wrapped_instruction = wrapper.wrap(card.instruction)

        timestamp = datetime.now().isoformat()
        markdown = self._format_markdown(card, wrapped_instruction, timestamp)

        task_path = self._config.task_file
        try:
            task_path.write_text(markdown, encoding="utf-8")
        except OSError as exc:
            raise TaskFileError(f"Failed to write {task_path}: {exc}")

        # Update shared state
        self._state.set_current_card(
            card_id=card.id,
            workflow=card.workflow,
            version=card.version,
            instruction=wrapped_instruction,
            card_index=card_index,
            total_cards=total_cards,
            loop_id=card.loop_id,
        )

        logger.info(
            "Dealt card %s (%d/%d) for workflow %s/%s",
            card.id, card_index + 1, total_cards, card.workflow, card.version,
        )
        return task_path

    def read_current_task(self) -> Optional[str]:
        """Read the current task file, or return None if it doesn't exist."""
        path = self._config.task_file
        if not path.exists():
            return None
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            raise TaskFileError(f"Failed to read {path}: {exc}")

    # ------------------------------------------------------------------ #
    #  Private helpers
    # ------------------------------------------------------------------ #

    def _build_wrapper(self, card: BaseCard, *, card_index: int = 0) -> InstructionWrapper:
        """
        Dynamically compose the wrapper chain based on card metadata.

        Engine-level standards (always applied):
        - Follow-task-file instruction (prefix on every card)
        - DRY/tidy reminder (suffix every 2nd card)
        - Envelope header + stop-token footer

        Card-level wrappers (based on metadata):
        - High-priority cards get the step-by-step preamble.
        - Custom wrapper text from metadata is injected if present.
        """
        wrapper = InstructionWrapper()

        # === Engine standards (always applied) ===
        wrapper.add_follow_task_instruction()
        wrapper.add_envelope()
        wrapper.add_workspace_boundary(str(self._config.resolved_workspace))

        # DRY reminder every 2nd card (0-indexed: cards 1, 3, 5, ...)
        if (card_index + 1) % 2 == 0:
            wrapper.add_dry_reminder()

        # === Card-level wrappers ===
        if card.priority == "high":
            wrapper.add_step_by_step()
            wrapper.add_branch_policy()

        custom_prefix = card.metadata.get("custom_wrapper")
        if custom_prefix:
            wrapper.add_custom(custom_prefix, position="prefix")

        # Always add the stop-token footer
        wrapper.add_stop_token_footer()

        return wrapper

    def _format_markdown(
        self, card: BaseCard, wrapped_instruction: str, timestamp: str
    ) -> str:
        """Build the full markdown document."""
        lines = [
            f"# Task: {card.id}",
            f"",
            f"| Field | Value |",
            f"|---|---|",
            f"| **Workflow** | {card.workflow} |",
            f"| **Version** | {card.version} |",
            f"| **Card** | {card.id} |",
            f"| **Priority** | {card.priority} |",
            f"| **Timestamp** | {timestamp} |",
            f"| **Tags** | {', '.join(card.tags) if card.tags else '—'} |",
            f"",
            f"---",
            f"",
            wrapped_instruction,
            f"",
        ]
        return "\n".join(lines)
