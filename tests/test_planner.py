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
    """Test that _reshuffle_card_names only affects the specified loop."""

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
        """Reshuffling 'feature' loop must leave 'ops' loop files untouched."""
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

            # Feature loop: feature_01 → feature_02 → feature_01
            self._write_card(wf_dir, "feature_01", "feature", "feature_02")
            self._write_card(wf_dir, "feature_02", "feature", "feature_01")
            # Ops loop: ops_01 → ops_01 (single-card loop)
            self._write_card(wf_dir, "ops_01", "ops", "ops_01")

            cfg = EngineConfig(workspace_path=str(workspace), workflows_path=str(Path(tmp) / "workflows"))
            state = StateManager()
            picker = CardsPicker(cfg)
            dealer = CardsDealer(cfg, state)
            planner = CardsPlanner(cfg, state, picker, dealer)

            # Reshuffle only the 'feature' loop
            planner._reshuffle_card_names.__func__  # ensure method exists
            new_first = planner._reshuffle_card_names("test_wf", "v1", loop_id="feature")

            # ops_01.json must still exist
            self.assertTrue((wf_dir / "ops_01.json").exists(),
                            "ops_01.json should not be renamed by feature reshuffle")

            # feature_01.json and feature_02.json must be gone (renamed)
            self.assertFalse((wf_dir / "feature_01.json").exists(),
                             "feature_01.json should be renamed after reshuffle")
            self.assertFalse((wf_dir / "feature_02.json").exists(),
                             "feature_02.json should be renamed after reshuffle")

            # New fruit files should exist and have loop_id = "feature"
            new_file = wf_dir / f"{new_first}.json"
            self.assertTrue(new_file.exists(), f"{new_first}.json should exist")
            new_data = json.loads(new_file.read_text(encoding="utf-8"))
            self.assertEqual(new_data["loop_id"], "feature")


if __name__ == "__main__":
    unittest.main()
