"""
CardsPicker — JSON parser and state-transition resolver.

Loads workflow directories, constructs Card objects, and resolves
the next card in the chain.  All path operations are guarded against
directory traversal attacks.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from core.base_card import BaseCard, BaseWorkflow
from core.config import EngineConfig
from core.exceptions import (
    CardNotFoundError,
    InvalidWorkflowPathError,
    WorkflowValidationError,
)


class CardsPicker:
    """
    Parses workflow JSON files into Card objects and provides
    state-transition logic (which card comes next).
    """

    def __init__(self, config: EngineConfig):
        self._config = config
        self._workflows: Dict[str, BaseWorkflow] = {}

    # ------------------------------------------------------------------ #
    #  Path safety
    # ------------------------------------------------------------------ #

    def _safe_workflow_path(self, workflow_name: str, version: str) -> Path:
        """
        Resolve a workflow directory path and verify it stays inside
        the workflows root.  Prevents ../../ traversal attacks.
        """
        base = self._config.resolved_workflows
        target = (base / workflow_name / version).resolve()
        if not target.is_relative_to(base):
            raise InvalidWorkflowPathError(f"{workflow_name}/{version}")
        return target

    # ------------------------------------------------------------------ #
    #  Loading
    # ------------------------------------------------------------------ #

    def load_workflow(self, workflow_name: str, version: str) -> BaseWorkflow:
        """
        Load (or return cached) a workflow from disk.

        Parameters
        ----------
        workflow_name : str   e.g. "sample_workflow"
        version       : str   e.g. "v1"

        Returns
        -------
        BaseWorkflow with all cards populated.
        """
        cache_key = f"{workflow_name}/{version}"
        if cache_key in self._workflows:
            return self._workflows[cache_key]

        workflow_dir = self._safe_workflow_path(workflow_name, version)
        workflow = BaseWorkflow.load(workflow_dir)
        self._workflows[cache_key] = workflow
        return workflow

    def list_workflows(self) -> List[Dict[str, str]]:
        """
        Scan the workflows directory and return a list of
        {name, version} dicts for every versioned workflow found.
        """
        results = []
        base = self._config.resolved_workflows
        if not base.exists():
            return results

        for wf_dir in sorted(base.iterdir()):
            if not wf_dir.is_dir() or wf_dir.name.startswith("."):
                continue
            for ver_dir in sorted(wf_dir.iterdir()):
                if not ver_dir.is_dir():
                    continue
                results.append({"name": wf_dir.name, "version": ver_dir.name})
        return results

    # ------------------------------------------------------------------ #
    #  Card resolution
    # ------------------------------------------------------------------ #

    def get_first_card(self, workflow_name: str, version: str) -> BaseCard:
        """Return the entry-point card of a workflow."""
        wf = self.load_workflow(workflow_name, version)
        return wf.first_card

    def get_loop_first_card(
        self, workflow_name: str, version: str, loop_id: str
    ) -> BaseCard:
        """Return the first card of the named loop within a workflow."""
        wf = self.load_workflow(workflow_name, version)
        return wf.get_loop_first_card(loop_id)

    def get_next_card(
        self, workflow_name: str, version: str, current_card_id: str
    ) -> Optional[BaseCard]:
        """
        Given the current card ID, return the next Card in the chain.
        Returns None if the workflow is finished (next_card is null).
        """
        wf = self.load_workflow(workflow_name, version)
        current = wf.get_card(current_card_id)

        if current.next_card is None:
            return None

        try:
            return wf.get_card(current.next_card)
        except CardNotFoundError:
            raise WorkflowValidationError(
                workflow=workflow_name,
                detail=(
                    f"Card '{current_card_id}' references next_card "
                    f"'{current.next_card}' which does not exist"
                ),
            )

    def get_card_index(self, workflow_name: str, version: str, card_id: str) -> int:
        """Return the 0-based index of a card within its workflow."""
        wf = self.load_workflow(workflow_name, version)
        return wf.card_index(card_id)

    def get_total_cards(self, workflow_name: str, version: str) -> int:
        """Return total number of cards in a workflow."""
        wf = self.load_workflow(workflow_name, version)
        return wf.total_cards
