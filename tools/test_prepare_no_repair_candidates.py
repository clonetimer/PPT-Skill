import json
import tempfile
import unittest
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches

from fifteen_figure_review_packet import TASK_FILENAMES, TASK_FINAL_FILENAMES, TASK_COMPANION_FILENAMES
from prepare_no_repair_candidates import prepare
from repair_case_artifacts import sha256_file
from scientific_ir import ROOT


def deck(path, label):
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.shapes.add_textbox(Inches(1), Inches(1), Inches(3), Inches(.5)).text = label
    prs.save(path)


class PrepareNoRepairCandidatesTests(unittest.TestCase):
    def test_all_diagnosed_no_repair_tasks_are_copied_byte_identically(self):
        ledger = json.loads((ROOT / "specs/15_figure_diagnostic_ledger_v76.json").read_text())
        no_repair = [task for task, row in ledger["tasks"].items()
                     if row["status"] == "NO_CONFIRMED_DEFECT"]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            initial, final = root / "initial", root / "final"
            initial.mkdir()
            for task in no_repair:
                deck(initial / TASK_FILENAMES[task], task)
            for task,names in TASK_COMPANION_FILENAMES.items():
                for name in names:deck(initial/name,task+" companion")
            result = prepare(initial, final)
            self.assertEqual(set(result["copied"]), set(no_repair))
            for task in no_repair:
                self.assertEqual(
                    sha256_file(initial / TASK_FILENAMES[task]),
                    sha256_file(final / TASK_FINAL_FILENAMES[task]),
                )
            self.assertTrue((final/"Q08_wine_strip.pptx").is_file())
            self.assertIn("Q07:Q08_wine_strip.pptx",result["copied"])
            manifest = json.loads((final / "no_repair_candidate_manifest.json").read_text())
            self.assertEqual(set(manifest["no_confirmed_defect_tasks"]), set(no_repair))

    def test_existing_repair_artifact_is_never_overwritten(self):
        ledger = json.loads((ROOT / "specs/15_figure_diagnostic_ledger_v76.json").read_text())
        task = next(task for task, row in ledger["tasks"].items()
                    if row["status"] == "NO_CONFIRMED_DEFECT")
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            initial, final = root / "initial", root / "final"
            initial.mkdir(); final.mkdir()
            deck(initial / TASK_FILENAMES[task], "initial")
            target = final / TASK_FINAL_FILENAMES[task]
            deck(target, "different existing repair")
            before = sha256_file(target)
            with self.assertRaisesRegex(ValueError, "REFUSE_TO_OVERWRITE_EXISTING_REPAIR"):
                prepare(initial, final)
            self.assertEqual(sha256_file(target), before)


if __name__ == "__main__":
    unittest.main()
