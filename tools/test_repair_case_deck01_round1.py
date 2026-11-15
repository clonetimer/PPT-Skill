import json
import shutil
import tempfile
import unittest
from pathlib import Path

from pptx import Presentation

from repair_case_deck01_round1 import run_case


class Deck01RepairRoundOneTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("libreoffice") and shutil.which("pdftoppm"),
                         "LibreOffice and Poppler are required for repair render evidence")
    def test_evidence_boundary_repair_is_immutable_audited_and_rendered(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            case = root / "case"
            accepted = root / "accepted" / "DECK01_c01_defense_v76.pptx"
            final = root / "final" / "DECK01_c01_defense_v76.pptx"
            result = run_case(case, accepted, final, publish=False)

            first_pass = case / "rounds" / "first_pass.pptx"
            round_01 = case / "rounds" / "round_01.pptx"
            self.assertTrue(first_pass.is_file())
            self.assertTrue(round_01.is_file())
            self.assertTrue(accepted.is_file())
            self.assertTrue(final.is_file())
            self.assertEqual(result["status"], "ROUND_01_REPAIR_EXECUTED_AND_AUDITED")
            self.assertEqual(result["accepted_rounds"], 1)
            self.assertEqual(result["rejected_rounds"], 0)
            self.assertEqual(result["quality"]["status"], "PASS")
            self.assertGreater(result["pptx_object_changes"], 0)
            self.assertGreater(result["deck_spec_changes"], 0)

            history = json.loads((case / "repair_history.json").read_text(encoding="utf-8"))
            self.assertTrue(history["first_pass"]["immutable"])
            self.assertEqual(len(history["rounds"]), 1)
            self.assertTrue(history["rounds"][0]["accepted"])
            self.assertEqual(history["human_final_review"], "PENDING")
            self.assertEqual(history["office_2016_host_round_trip"], "PENDING")

            diff = json.loads((case / "round_01_object_diff.json").read_text(encoding="utf-8"))
            self.assertGreater(diff["added"], 0)
            spec_diff = json.loads((case / "round_01_deck_spec_diff.json").read_text(encoding="utf-8"))
            self.assertTrue(spec_diff["changes"])

            deck = Presentation(round_01)
            self.assertEqual(len(deck.slides), 3)
            slide3 = deck.slides[2]
            card_names = {s.name for s in slide3.shapes}
            self.assertTrue({"s03_card_1", "s03_card_2", "s03_card_3"} <= card_names)
            visible = "\\n".join(s.text for s in slide3.shapes if s.has_text_frame)
            for term in ("18", "SOURCE-VISIBLE ROUTES", "SCHEMATIC SUBSTITUTIONS",
                         "HUMAN REVIEW STILL REQUIRED", "PowerPoint 2016 host round trip"):
                self.assertIn(term, visible)

            renders = case / "renders"
            for name in ("first_pass.pdf", "round_01.pdf",
                         "first_pass-1.png", "first_pass-2.png", "first_pass-3.png",
                         "round_01-1.png", "round_01-2.png", "round_01-3.png",
                         "first_pass_vs_round_01_slide_3.png"):
                self.assertTrue((renders / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
