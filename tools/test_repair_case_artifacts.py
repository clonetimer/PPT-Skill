import shutil
import tempfile
import unittest
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

from repair_case_artifacts import (
    compare_pngs,
    pptx_object_diff,
    pptx_object_snapshot,
    render_pptx,
    sha256_file,
)


def make_deck(path: Path, label: str, x: float = 1.0):
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    shape = slide.shapes.add_textbox(Inches(x), Inches(1), Inches(4), Inches(.7))
    shape.name = "stable_claim"
    run = shape.text_frame.paragraphs[0].add_run()
    run.text = label
    run.font.name = "Times New Roman"
    run.font.size = Pt(20)
    run.font.color.rgb = RGBColor(40, 52, 60)
    prs.save(path)


class RepairCaseArtifactTests(unittest.TestCase):
    def test_snapshot_and_diff_capture_text_and_geometry_without_mutating_source(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            before, after = root / "before.pptx", root / "after.pptx"
            make_deck(before, "Initial claim", 1.0)
            make_deck(after, "Repaired claim", 1.2)
            before_hash = sha256_file(before)
            snap = pptx_object_snapshot(before)
            diff = pptx_object_diff(before, after)
            self.assertEqual(sha256_file(before), before_hash)
            self.assertEqual(len(snap), 1)
            self.assertEqual(diff["initial_objects"], 1)
            self.assertEqual(diff["final_objects"], 1)
            self.assertEqual(diff["modified"], 1)
            fields = diff["changes"][0]["fields"]
            self.assertIn("text", fields)
            self.assertIn("left", fields)

    @unittest.skipUnless(shutil.which("libreoffice") and shutil.which("pdftoppm"),
                         "LibreOffice and Poppler are required for render evidence")
    def test_render_and_side_by_side_evidence_use_clean_output_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            before, after = root / "before.pptx", root / "after.pptx"
            make_deck(before, "Initial claim")
            make_deck(after, "Repaired claim")
            renders = root / "renders"
            pdf0, pages0 = render_pptx(before, renders, "first_pass")
            pdf1, pages1 = render_pptx(after, renders, "round_01")
            comparison = compare_pngs(pages0[0], pages1[0], renders / "first_pass_vs_round_01.png")
            self.assertTrue(pdf0.is_file() and pdf1.is_file())
            self.assertEqual(len(pages0), 1)
            self.assertEqual(len(pages1), 1)
            self.assertTrue(comparison.is_file())
            self.assertFalse(any(p.name.startswith("lo-profile") for p in renders.iterdir()))


if __name__ == "__main__":
    unittest.main()
