"""Tests for the CardsPlanner engine component (non-watchdog parts)."""

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import EngineConfig
from core.state_manager import StateManager


class TestStopTokenDetection(unittest.TestCase):
    """Test the forgiving next-card token regex used by the Planner."""

    def setUp(self):
        self.config = EngineConfig()
        self.pattern = re.compile(self.config.stop_token_regex)

    def test_exact_match(self):
        self.assertTrue(self.pattern.search("![next]!"))

    def test_capitalized(self):
        self.assertTrue(self.pattern.search("![Next]!"))

    def test_no_exclamation_prefix(self):
        self.assertTrue(self.pattern.search("[next]!"))

    def test_no_exclamation_suffix(self):
        self.assertTrue(self.pattern.search("![next]"))

    def test_bare_brackets(self):
        self.assertTrue(self.pattern.search("[Next]"))

    def test_embedded_in_text(self):
        text = "Here is the summary.\n\n![next]!\n"
        self.assertTrue(self.pattern.search(text))

    def test_no_match(self):
        self.assertFalse(self.pattern.search("No next token here."))


class TestPlannerArchival(unittest.TestCase):
    """Test the archival helper logic (summary extraction)."""

    def test_extract_summary_header(self):
        """Summary section between ## Summary and stop token should be extracted."""
        content = (
            "# Task\n\nSome work.\n\n"
            "## Summary\n\nThis was great work.\n\n![next]!\n"
        )
        match = re.search(
            r"##\s*[Ss]ummary\s*\n(.*?)(?=!\[|\Z)",
            content,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        self.assertIn("great work", match.group(1))

    def test_master_summary_append(self):
        """Verify we can append to master_summary.md."""
        with tempfile.TemporaryDirectory() as tmp:
            cfg = EngineConfig(workspace_path=tmp, workflows_path=tmp)
            master = cfg.master_summary_file

            # Simulate two appends
            with master.open("a", encoding="utf-8") as f:
                f.write("## card_01\nDone.\n---\n")
            with master.open("a", encoding="utf-8") as f:
                f.write("## card_02\nAlso done.\n---\n")

            content = master.read_text(encoding="utf-8")
            self.assertIn("card_01", content)
            self.assertIn("card_02", content)


class TestMultiLoopReshuffle(unittest.TestCase):
    """Test that _reshuffle_card_names only affects the specified loop in-memory."""

    def _write_card(self, directory: Path, card_id: str, loop_id: str, next_card: str) -> None:
        data = {
            "id": card_id, "loop_id": loop_id,
            "workflow": "test_wf", "version": "v1",
            "instruction": f"Do {card_id}.",
            "metadata": {}, "next_card": next_card,
        }
        (directory / f"{card_id}.json").write_text(
            json.dumps(data, indent=2), encoding="utf-8"
        )

    def test_reshuffle_does_not_touch_other_loop_files(self):
        """Reshuffling 'feature' loop must leave 'ops' loop aliases untouched and disk files intact."""
        from engine.picker import CardsPicker
        from engine.dealer import CardsDealer
        from engine.planner import CardsPlanner
        from core.config import EngineConfig
        from core.state_manager import StateManager

        with tempfile.TemporaryDirectory() as tmp:
            wf_dir = Path(tmp) / "workflows" / "test_wf" / "v1"
            wf_dir.mkdir(parents=True)
            workspace = Path(tmp) / "workspace"
            workspace.mkdir()

            # Feature loop: feature_01 \u2192 feature_02 \u2192 feature_01
            self._write_card(wf_dir, "feature_01", "feature", "feature_02")
            self._write_card(wf_dir, "feature_02", "feature", "feature_01")
            # Ops loop: ops_01 \u2192 ops_01 (single-card loop)
            self._write_card(wf_dir, "ops_01", "ops", "ops_01")

            cfg = EngineConfig(workspace_path=str(workspace), workflows_path=str(Path(tmp) / "workflows"))
            state = StateManager()
            picker = CardsPicker(cfg)
            dealer = CardsDealer(cfg, state)
            planner = CardsPlanner(cfg, state, picker, dealer)

            # Load workflow to initialize cache
            wf = picker.load_workflow("test_wf", "v1")

            # Reshuffle only the 'feature' loop
            new_first_id = planner._reshuffle_card_names("test_wf", "v1", loop_id="feature")

            # DISK CHECK: All files must still exist with original names
            self.assertTrue((wf_dir / "ops_01.json").exists())
            self.assertTrue((wf_dir / "feature_01.json").exists())
            self.assertTrue((wf_dir / "feature_02.json").exists())

            # ALIAS CHECK: feature_01 and feature_02 should have aliases
            self.assertIn("feature_01", wf.alias_map)
            self.assertIn("feature_02", wf.alias_map)
            # ops_01 should NOT have an alias (unless it's its own ID)
            self.assertNotIn("ops_01", wf.alias_map)

            # verify aliased card retrieval
            aliased = wf.get_aliased_card("feature_01")
            self.assertEqual(aliased.id, wf.alias_map["feature_01"])
            self.assertEqual(aliased.next_card, wf.alias_map["feature_02"])


if __name__ == "__main__":
    unittest.main()
