"""Tests for the core module: BaseCard, BaseWorkflow, InstructionWrapper."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.base_card import BaseCard, BaseWorkflow
from core.config import EngineConfig
from core.exceptions import CardNotFoundError, WorkflowValidationError
from core.state_manager import StateManager
from core.wrappers import InstructionWrapper


class TestBaseCard(unittest.TestCase):
    """Test BaseCard creation, serialization, and JSON loading."""

    def test_create_card(self):
        card = BaseCard(
            id="card_01", workflow="test", version="v1",
            instruction="Do something.",
            metadata={"priority": "high", "tags": ["setup"]},
            next_card="card_02",
        )
        self.assertEqual(card.id, "card_01")
        self.assertEqual(card.priority, "high")
        self.assertEqual(card.tags, ["setup"])
        self.assertEqual(card.next_card, "card_02")

    def test_to_dict_round_trip(self):
        card = BaseCard(
            id="c1", workflow="w", version="v1",
            instruction="Test", metadata={"priority": "normal"},
        )
        d = card.to_dict()
        self.assertEqual(d["id"], "c1")
        self.assertIsNone(d["next_card"])

    def test_from_json_valid(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump({
                "id": "card_01", "workflow": "test", "version": "v1",
                "instruction": "Hello", "next_card": None,
            }, f)
            f.flush()
            card = BaseCard.from_json(Path(f.name))
            self.assertEqual(card.id, "card_01")
            self.assertEqual(card.instruction, "Hello")

    def test_from_json_missing_field(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump({"id": "card_01"}, f)  # missing required fields
            f.flush()
            with self.assertRaises(WorkflowValidationError):
                BaseCard.from_json(Path(f.name))

    def test_max_time_seconds(self):
        card = BaseCard(
            id="c", workflow="w", version="v",
            instruction="Do it",
            metadata={"max_time_seconds": 120},
        )
        self.assertEqual(card.max_time_seconds, 120)

    def test_max_time_seconds_default(self):
        card = BaseCard(id="c", workflow="w", version="v", instruction="Do")
        self.assertIsNone(card.max_time_seconds)


class TestBaseWorkflow(unittest.TestCase):
    """Test BaseWorkflow loading and card lookup."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.wf_dir = Path(self.tmp) / "my_workflow" / "v1"
        self.wf_dir.mkdir(parents=True)
        # Write guidance
        (self.wf_dir / "guidance.md").write_text("# Guide\n", encoding="utf-8")
        # Write cards
        for i, next_id in [(1, "card_02"), (2, None)]:
            (self.wf_dir / f"card_{i:02d}.json").write_text(
                json.dumps({
                    "id": f"card_{i:02d}",
                    "workflow": "my_workflow",
                    "version": "v1",
                    "instruction": f"Step {i}",
                    "next_card": next_id,
                }),
                encoding="utf-8",
            )

    def test_load(self):
        wf = BaseWorkflow.load(self.wf_dir)
        self.assertEqual(wf.name, "my_workflow")
        self.assertEqual(wf.version, "v1")
        self.assertEqual(wf.total_cards, 2)
        self.assertIsNotNone(wf.guidance_path)

    def test_get_card(self):
        wf = BaseWorkflow.load(self.wf_dir)
        card = wf.get_card("card_01")
        self.assertEqual(card.instruction, "Step 1")

    def test_get_card_not_found(self):
        wf = BaseWorkflow.load(self.wf_dir)
        with self.assertRaises(CardNotFoundError):
            wf.get_card("nonexistent")

    def test_first_card(self):
        wf = BaseWorkflow.load(self.wf_dir)
        self.assertEqual(wf.first_card.id, "card_01")

    def test_card_index(self):
        wf = BaseWorkflow.load(self.wf_dir)
        self.assertEqual(wf.card_index("card_02"), 1)


class TestInstructionWrapper(unittest.TestCase):
    """Test the builder-pattern InstructionWrapper."""

    def test_empty_wrap(self):
        w = InstructionWrapper()
        self.assertEqual(w.wrap("Hello"), "Hello")

    def test_step_by_step(self):
        w = InstructionWrapper().add_step_by_step()
        result = w.wrap("Do the thing.")
        self.assertIn("step by step", result)
        self.assertIn("Do the thing.", result)

    def test_stop_token_footer(self):
        w = InstructionWrapper().add_stop_token_footer()
        result = w.wrap("Task here.")
        self.assertIn("completion marker", result)  # descriptive, not literal token

    def test_chaining(self):
        w = InstructionWrapper()
        result = (w
            .add_step_by_step()
            .add_stop_token_footer()
            .add_custom("Be precise.")
            .wrap("Build it."))
        self.assertIn("step by step", result)
        self.assertIn("completion marker", result)
        self.assertIn("Be precise.", result)
        self.assertIn("Build it.", result)

    def test_reset(self):
        w = InstructionWrapper().add_step_by_step()
        w.reset()
        self.assertEqual(w.wrap("plain"), "plain")

    def test_custom_transform(self):
        w = InstructionWrapper().add_transform(str.upper)
        self.assertEqual(w.wrap("hello"), "HELLO")


class TestStateManager(unittest.TestCase):
    """Test thread-safe StateManager."""

    def test_initial_state(self):
        sm = StateManager()
        snap = sm.get_snapshot()
        self.assertEqual(snap["status"], "idle")
        self.assertIsNone(snap["current_card_id"])

    def test_set_current_card(self):
        sm = StateManager()
        sm.set_current_card("c1", "wf", "v1", "Do it", 0, 3)
        snap = sm.get_snapshot()
        self.assertEqual(snap["current_card_id"], "c1")
        self.assertEqual(snap["status"], "running")
        self.assertEqual(snap["total_cards"], 3)

    def test_mark_completed(self):
        sm = StateManager()
        sm.set_current_card("c1", "wf", "v1", "Do it", 0, 3)
        sm.mark_completed("Done with c1")
        snap = sm.get_snapshot()
        self.assertEqual(snap["status"], "completed")
        self.assertEqual(len(snap["history"]), 1)
        self.assertEqual(snap["history"][0]["summary"], "Done with c1")

    def test_progress_pct(self):
        sm = StateManager()
        sm.set_current_card("c1", "wf", "v1", "Do", 0, 4)
        snap = sm.get_snapshot()
        self.assertEqual(snap["progress_pct"], 0.0)  # card_index=0 of 4
        sm.mark_completed("s1")
        sm.set_current_card("c2", "wf", "v1", "Do", 1, 4)
        snap = sm.get_snapshot()
        self.assertEqual(snap["progress_pct"], 25.0)  # card_index=1 of 4

    def test_circular_loop_progress_stays_bounded(self):
        """In a circular workflow, progress should cycle 0-100% not grow forever."""
        sm = StateManager()
        # First cycle
        sm.set_current_card("c1", "wf", "v1", "Do", 0, 2)
        sm.mark_completed("s1")
        sm.set_current_card("c2", "wf", "v1", "Do", 1, 2)
        sm.mark_completed("s2")
        # Second cycle - loops back
        sm.set_current_card("c1", "wf", "v1", "Do", 0, 2)
        snap = sm.get_snapshot()
        self.assertEqual(snap["progress_pct"], 0.0)  # back to 0%, not 100%+
        self.assertEqual(snap["cycles_completed"], 1)
        self.assertEqual(snap["completed_total"], 2)

    def test_mark_error(self):
        sm = StateManager()
        sm.set_current_card("c1", "wf", "v1", "Do", 0, 1)
        sm.mark_error("Timed out")
        snap = sm.get_snapshot()
        self.assertEqual(snap["status"], "error")
        self.assertEqual(snap["error"], "Timed out")


class TestEngineConfig(unittest.TestCase):
    """Test EngineConfig defaults and path resolution."""

    def test_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = EngineConfig(workspace_path=tmp, workflows_path=tmp)
            self.assertEqual(cfg.flask_port, 5000)
            self.assertTrue(cfg.task_file.name == "current_task.md")
            self.assertTrue(cfg.archive_path.exists())

    def test_stop_token_regex(self):
        import re
        cfg = EngineConfig()
        pattern = re.compile(cfg.stop_token_regex)
        self.assertTrue(pattern.search("![stop]!"))
        self.assertTrue(pattern.search("![Stop]!"))
        self.assertTrue(pattern.search("[stop]"))
        self.assertTrue(pattern.search("[Stop]!"))


class TestMultiLoopWorkflow(unittest.TestCase):
    """Test loop_id field and multi-loop grouping in BaseWorkflow."""

    def _make_card(self, card_id: str, loop_id: str, next_card=None) -> BaseCard:
        return BaseCard(
            id=card_id, loop_id=loop_id,
            workflow="test", version="v1",
            instruction=f"Do {card_id}.",
            next_card=next_card,
        )

    def _write_workflow(self, tmp: str, cards: list) -> Path:
        wf_dir = Path(tmp)
        for card in cards:
            (wf_dir / f"{card.id}.json").write_text(
                json.dumps(card.to_dict()), encoding="utf-8"
            )
        return wf_dir

    def test_loop_id_defaults_to_main(self):
        card = BaseCard(id="c1", workflow="w", version="v1", instruction="x")
        self.assertEqual(card.loop_id, "main")

    def test_loop_id_from_json(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump({
                "id": "ops_01", "loop_id": "ops",
                "workflow": "test", "version": "v1",
                "instruction": "Run scraper.",
            }, f)
            f.flush()
            card = BaseCard.from_json(Path(f.name))
            self.assertEqual(card.loop_id, "ops")

    def test_loop_id_in_to_dict(self):
        card = self._make_card("feature_01", "feature", next_card="feature_02")
        d = card.to_dict()
        self.assertEqual(d["loop_id"], "feature")

    def test_loops_property_groups_by_loop_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            cards = [
                self._make_card("feature_01", "feature", "feature_02"),
                self._make_card("feature_02", "feature", "feature_01"),
                self._make_card("ops_01", "ops", "ops_02"),
                self._make_card("ops_02", "ops", "ops_01"),
            ]
            wf_dir = self._write_workflow(tmp, cards)
            wf = BaseWorkflow.load(wf_dir)
            loops = wf.loops
            self.assertIn("feature", loops)
            self.assertIn("ops", loops)
            self.assertEqual(len(loops["feature"]), 2)
            self.assertEqual(len(loops["ops"]), 2)

    def test_get_loop_first_card(self):
        with tempfile.TemporaryDirectory() as tmp:
            cards = [
                self._make_card("feature_01", "feature", "feature_02"),
                self._make_card("feature_02", "feature", "feature_01"),
                self._make_card("ops_01", "ops", "ops_01"),
            ]
            wf_dir = self._write_workflow(tmp, cards)
            wf = BaseWorkflow.load(wf_dir)
            ops_first = wf.get_loop_first_card("ops")
            self.assertEqual(ops_first.id, "ops_01")

    def test_get_loop_first_card_missing_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            cards = [self._make_card("ops_01", "ops", None)]
            wf_dir = self._write_workflow(tmp, cards)
            wf = BaseWorkflow.load(wf_dir)
            with self.assertRaises(CardNotFoundError):
                wf.get_loop_first_card("nonexistent_loop")


if __name__ == "__main__":
    unittest.main()
