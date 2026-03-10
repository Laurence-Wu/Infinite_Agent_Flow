"""Tests for the CardsDealer engine component."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.base_card import BaseCard
from core.config import EngineConfig
from core.state_manager import StateManager
from engine.dealer import CardsDealer


class TestCardsDealer(unittest.TestCase):
    """Test CardsDealer: dealing, wrapping, and markdown output."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.config = EngineConfig(
            workspace_path=self.tmp,
            workflows_path=self.tmp,
        )
        self.state = StateManager()
        self.dealer = CardsDealer(self.config, self.state)

    def _make_card(self, priority="normal"):
        return BaseCard(
            id="card_01", workflow="test", version="v1",
            instruction="Build the widget.",
            metadata={"priority": priority, "tags": ["test"]},
            next_card="card_02",
        )

    def test_deal_creates_file(self):
        card = self._make_card()
        path = self.dealer.deal_card(card, card_index=0, total_cards=2)
        self.assertTrue(path.exists())

    def test_deal_contains_instruction(self):
        card = self._make_card()
        self.dealer.deal_card(card, card_index=0, total_cards=2)
        content = self.config.task_file.read_text(encoding="utf-8")
        self.assertIn("Build the widget.", content)

    def test_deal_contains_stop_token_instruction(self):
        card = self._make_card()
        self.dealer.deal_card(card, card_index=0, total_cards=2)
        content = self.config.task_file.read_text(encoding="utf-8")
        self.assertIn("completion marker", content)  # descriptive, not literal

    def test_deal_high_priority_has_step_by_step(self):
        card = self._make_card(priority="high")
        self.dealer.deal_card(card, card_index=0, total_cards=2)
        content = self.config.task_file.read_text(encoding="utf-8")
        self.assertIn("step by step", content.lower())

    def test_deal_updates_state(self):
        card = self._make_card()
        self.dealer.deal_card(card, card_index=0, total_cards=2)
        snap = self.state.get_snapshot()
        self.assertEqual(snap["current_card_id"], "card_01")
        self.assertEqual(snap["status"], "running")
        self.assertEqual(snap["total_cards"], 2)

    def test_deal_contains_metadata_table(self):
        card = self._make_card()
        self.dealer.deal_card(card, card_index=0, total_cards=2)
        content = self.config.task_file.read_text(encoding="utf-8")
        self.assertIn("| **Workflow** |", content)
        self.assertIn("test", content)

    def test_read_current_task(self):
        self.assertIsNone(self.dealer.read_current_task())
        card = self._make_card()
        self.dealer.deal_card(card, card_index=0, total_cards=2)
        content = self.dealer.read_current_task()
        self.assertIsNotNone(content)
        self.assertIn("card_01", content)


if __name__ == "__main__":
    unittest.main()
