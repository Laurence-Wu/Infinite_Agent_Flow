"""
Abstract base classes for Cards and Workflows.
Every card and workflow in the engine inherits from these.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .exceptions import CardNotFoundError, WorkflowValidationError


# ---------------------------------------------------------------------------
# BaseCard
# ---------------------------------------------------------------------------

@dataclass
class BaseCard:
    """
    Represents a single instruction step inside a workflow.

    Attributes:
        id:          Unique card identifier (e.g. "card_01").
        workflow:    Name of the parent workflow.
        version:     Version tag (e.g. "v1").
        instruction: The raw instruction text for the AI agent.
        metadata:    Arbitrary key-value metadata (priority, tags, etc.).
        next_card:   ID of the next card, or None if this is the final step.
    """

    id: str
    workflow: str
    version: str
    instruction: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    next_card: Optional[str] = None
    loop_id: str = "main"

    # ---- serialization ----

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the card back to a JSON-compatible dict."""
        return {
            "id": self.id,
            "loop_id": self.loop_id,
            "workflow": self.workflow,
            "version": self.version,
            "instruction": self.instruction,
            "metadata": self.metadata,
            "next_card": self.next_card,
        }

    @classmethod
    def from_json(cls, path: Path) -> "BaseCard":
        """Load a card from a JSON file and validate required fields."""
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise WorkflowValidationError(
                workflow=str(path.parent),
                detail=f"Cannot read card file {path.name}: {exc}",
            )

        required = {"id", "workflow", "version", "instruction"}
        missing = required - set(data.keys())
        if missing:
            raise WorkflowValidationError(
                workflow=data.get("workflow", "unknown"),
                detail=f"Card {path.name} missing fields: {missing}",
            )

        return cls(
            id=data["id"],
            loop_id=data.get("loop_id", "main"),
            workflow=data["workflow"],
            version=data["version"],
            instruction=data["instruction"],
            metadata=data.get("metadata", {}),
            next_card=data.get("next_card"),
        )

    # ---- convenience ----

    @property
    def priority(self) -> str:
        return self.metadata.get("priority", "normal")

    @property
    def tags(self) -> List[str]:
        return self.metadata.get("tags", [])

    def __str__(self) -> str:
        return f"Card({self.id} @ {self.workflow}/{self.version})"


# ---------------------------------------------------------------------------
# BaseWorkflow
# ---------------------------------------------------------------------------

@dataclass
class BaseWorkflow:
    """
    Represents an ordered collection of cards under a named workflow.

    Attributes:
        name:           Workflow name (matches directory name).
        version:        Version tag.
        guidance_path:  Path to the guidance.md file.
        cards:          Ordered list of BaseCard objects.
    """

    name: str
    version: str
    guidance_path: Optional[Path] = None
    cards: List[BaseCard] = field(default_factory=list)
    # Maps internal card ID (e.g. "card_01") to active alias (e.g. "apple")
    alias_map: Dict[str, str] = field(default_factory=dict)
    # Reverse map: alias -> internal ID
    reverse_alias_map: Dict[str, str] = field(default_factory=dict)

    # ---- loading ----

    @classmethod
    def load(cls, workflow_dir: Path) -> "BaseWorkflow":
        """
        Load a workflow from a versioned directory.

        Expects structure:
            workflow_dir/
                guidance.md      (optional)
                card_01.json
                card_02.json
                ...
        """
        if not workflow_dir.is_dir():
            raise WorkflowValidationError(
                workflow=str(workflow_dir),
                detail="Directory does not exist",
            )

        # Derive name/version from path  (e.g. workflows/sample_workflow/v1)
        version = workflow_dir.name
        name = workflow_dir.parent.name

        guidance = workflow_dir / "guidance.md"
        guidance_path = guidance if guidance.exists() else None

        card_files = sorted(workflow_dir.glob("*.json"))
        if not card_files:
            raise WorkflowValidationError(
                workflow=name,
                detail=f"No *.json files found in {workflow_dir}",
            )

        cards = [BaseCard.from_json(f) for f in card_files]
        return cls(
            name=name,
            version=version,
            guidance_path=guidance_path,
            cards=cards,
        )

    # ---- queries ----

    def get_card(self, card_id: str) -> BaseCard:
        """Retrieve a card by ID or alias. Raises CardNotFoundError if missing."""
        # Try alias first
        internal_id = self.reverse_alias_map.get(card_id, card_id)
        for card in self.cards:
            if card.id == internal_id:
                return card
        raise CardNotFoundError(card_id, workflow=self.name)

    def get_aliased_card(self, card_id: str) -> BaseCard:
        """
        Retrieve a card by internal ID or alias, and return a copy with
        its 'id' and 'next_card' mapped to their active aliases.
        """
        card = self.get_card(card_id)
        # Create a shallow copy for aliasing
        import copy
        aliased = copy.copy(card)
        aliased.id = self.alias_map.get(card.id, card.id)
        if card.next_card:
            aliased.next_card = self.alias_map.get(card.next_card, card.next_card)
        return aliased

    def set_loop_aliases(self, loop_id: str, aliases: Dict[str, str]) -> None:
        """
        Set aliases for all cards in a loop. 
        'aliases' maps internal ID -> alias string.
        """
        # Remove old reverse mappings for this loop
        loop_cards = self.loops.get(loop_id, [])
        for c in loop_cards:
            old_alias = self.alias_map.get(c.id)
            if old_alias:
                self.reverse_alias_map.pop(old_alias, None)
        
        # Update mappings
        self.alias_map.update(aliases)
        for internal_id, alias in aliases.items():
            self.reverse_alias_map[alias] = internal_id

    @property
    def loops(self) -> Dict[str, List["BaseCard"]]:
        """Return cards grouped by loop_id, preserving load order within each group."""
        result: Dict[str, List[BaseCard]] = {}
        for card in self.cards:
            result.setdefault(card.loop_id, []).append(card)
        return result

    def get_loop_first_card(self, loop_id: str) -> "BaseCard":
        """Return the first card of the given loop. Raises CardNotFoundError if loop missing."""
        loop_cards = self.loops.get(loop_id, [])
        if not loop_cards:
            raise CardNotFoundError(f"loop:{loop_id}", workflow=self.name)
        return loop_cards[0]

    @property
    def first_card(self) -> BaseCard:
        """Return the first card in the workflow."""
        if not self.cards:
            raise WorkflowValidationError(
                self.name, detail="Workflow has no cards"
            )
        return self.cards[0]

    @property
    def total_cards(self) -> int:
        return len(self.cards)

    def card_index(self, card_id: str) -> int:
        """Return the 0-based index of a card. Raises CardNotFoundError."""
        for i, card in enumerate(self.cards):
            if card.id == card_id:
                return i
        raise CardNotFoundError(card_id, workflow=self.name)

    def __str__(self) -> str:
        return f"Workflow({self.name}/{self.version}, {self.total_cards} cards)"
