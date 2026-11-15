import json
import shutil
import tempfile
import unittest
from pathlib import Path

from pptx import Presentation

from repair_case_c01_fbg_round1 import run_case
from scientific_ir import ROOT


@unittest.skipUnless(shutil.which("libreoffice") and shutil.which("pdftoppm"),
                     "LibreOffice and Poppler are required for C01-FBG repair evidence")
class C01FbgRepairRoundOneTests(unittest.TestCase):
    def test_source_title_and_region_repair_has_immutable_round_and_render_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            case=root/"case"
            accepted=root/"accepted"/"C01_FBG_construction_v74.pptx"
            result=run_case(case,accepted,publish=False)
            first=case/"rounds/first_pass.pptx"
            final=case/"rounds/round_01.pptx"
            self.assertTrue(first.is_file() and final.is_file() and accepted.is_file())
            self.assertEqual(result["status"],"ROUND_01_REPAIR_EXECUTED_AND_AUDITED")
            self.assertEqual(result["quality"]["status"],"PASS")
            self.assertTrue(result["quality"]["source_title_preserved"])
            self.assertEqual(result["quality"]["band_subgraphs"],4)
            self.assertEqual(result["quality"]["fault_sensitivity_cues"],2)
            history=json.loads((case/"repair_history.json").read_text(encoding="utf-8"))
            self.assertTrue(history["first_pass"]["immutable"])
            self.assertEqual(history["human_final_review"],"PENDING")
            self.assertTrue((case/"round_01_object_diff.json").is_file())
            self.assertTrue((case/"round_01_figure_spec_diff.json").is_file())
            self.assertTrue((case/"round_01_quality_audit.json").is_file())
            self.assertTrue((case/"renders/first_pass.pdf").is_file())
            self.assertTrue((case/"renders/round_01.pdf").is_file())
            self.assertTrue((case/"renders/first_pass_vs_round_01.png").is_file())
            deck=Presentation(final)
            self.assertEqual(len(deck.slides),1)
            self.assertTrue(all(any(n.tag.endswith("}cNvPr") and n.get("descr") for n in s._element.iter())
                                for s in deck.slides[0].shapes))


if __name__=="__main__":
    unittest.main()
