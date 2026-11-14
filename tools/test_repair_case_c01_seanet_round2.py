import json
import tempfile
import unittest
from pathlib import Path

from pptx import Presentation

from repair_case_c01_seanet_round2 import run_case


class C01SeanetRoundTwoTests(unittest.TestCase):
    def test_structural_repair_is_immutable_audited_and_rendered(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            case = root / "case"
            accepted = root / "accepted" / "C01_SEANet_graph_level_v74.pptx"
            result = run_case(case, accepted)

            rounds = case / "rounds"
            first_pass = rounds / "first_pass.pptx"
            round_01 = rounds / "round_01.pptx"
            round_02 = rounds / "round_02.pptx"
            self.assertTrue(first_pass.is_file())
            self.assertTrue(round_01.is_file())
            self.assertTrue(round_02.is_file())
            self.assertTrue(accepted.is_file())
            self.assertEqual(result["status"], "ROUND_02_REPAIR_EXECUTED_AND_AUDITED")
            self.assertEqual(result["accepted_rounds"], 2)
            self.assertEqual(result["rejected_rounds"], 0)
            self.assertEqual(result["quality"]["status"], "PASS")

            history = json.loads((case / "repair_history.json").read_text(encoding="utf-8"))
            self.assertEqual(history["accepted_rounds"], 2)
            self.assertEqual(history["rounds"][1]["operation"],
                             "source-grounded structural rebuild from C01-SEANet FigureSpec v7.4")
            diff = json.loads((case / "round_02_object_diff.json").read_text(encoding="utf-8"))
            self.assertTrue(any(x["kind"] == "added" for x in diff))
            self.assertTrue(any(x["kind"] == "modified" for x in diff))

            deck = Presentation(round_02)
            self.assertEqual(len(deck.slides), 1)
            self.assertGreater(len(deck.slides[0].shapes), 90)
            self.assertTrue((case / "round_02_quality_audit.json").is_file())
            self.assertTrue((case / "renders" / "first_pass.png").is_file())
            self.assertTrue((case / "renders" / "round_01.png").is_file())
            self.assertTrue((case / "renders" / "round_02.png").is_file())
            self.assertTrue((case / "renders" / "round_01_vs_round_02.png").is_file())


if __name__ == "__main__":
    unittest.main()
