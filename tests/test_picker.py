"""Tests for the CardsPicker engine component."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import EngineConfig
from core.exceptions import CardNotFoundError, InvalidWorkflowPathError, WorkflowValidationError
from engine.picker import CardsPicker


class TestCardsPicker(unittest.TestCase):
    """Test CardsPicker: loading, traversal, and security."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        # Create a sample workflow
        wf_dir = Path(self.tmp) / "workflows" / "test_wf" / "v1"
        wf_dir.mkdir(parents=True)

        for i, nxt in [(1, "card_02"), (2, "card_03"), (3, None)]:
            (wf_dir / f"card_{i:02d}.json").write_text(
                json.dumps({
                    "id": f"card_{i:02d}",
                    "workflow": "test_wf",
                    "version": "v1",
                    "instruction": f"Step {i}",
                    "next_card": nxt,
                }),
                encoding="utf-8",
            )

        self.config = EngineConfig(
            workspace_path=str(Path(self.tmp) / "workspace"),
            workflows_path=str(Path(self.tmp) / "workflows"),
        )
        self.picker = CardsPicker(self.config)

    def test_load_workflow(self):
        wf = self.picker.load_workflow("test_wf", "v1")
        self.assertEqual(wf.total_cards, 3)

    def test_get_first_card(self):
        card = self.picker.get_first_card("test_wf", "v1")
        self.assertEqual(card.id, "card_01")

    def test_get_next_card(self):
        card = self.picker.get_next_card("test_wf", "v1", "card_01")
        self.assertIsNotNone(card)
        self.assertEqual(card.id, "card_02")

    def test_get_next_card_end(self):
        card = self.picker.get_next_card("test_wf", "v1", "card_03")
        self.assertIsNone(card)

    def test_list_workflows(self):
        wfs = self.picker.list_workflows()
        self.assertEqual(len(wfs), 1)
        self.assertEqual(wfs[0]["name"], "test_wf")

    def test_path_traversal_blocked(self):
        with self.assertRaises(InvalidWorkflowPathError):
            self.picker.load_workflow("../../etc", "passwd")

    def test_total_cards(self):
        self.assertEqual(self.picker.get_total_cards("test_wf", "v1"), 3)

    def test_card_index(self):
        self.assertEqual(self.picker.get_card_index("test_wf", "v1", "card_02"), 1)


if __name__ == "__main__":
    unittest.main()
