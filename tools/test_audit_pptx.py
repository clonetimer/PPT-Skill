import tempfile
import unittest
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches

from audit_pptx import audit


class AuditPptxOverlapTests(unittest.TestCase):
    def test_reports_exact_overlapping_text_box_pair(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"overlap.pptx"
            prs=Presentation()
            slide=prs.slides.add_slide(prs.slide_layouts[6])
            first=slide.shapes.add_textbox(Inches(1),Inches(1),Inches(3),Inches(1))
            first.name="first_label"
            first.text="Frequency band"
            second=slide.shapes.add_textbox(Inches(2),Inches(1.4),Inches(3),Inches(1))
            second.name="second_label"
            second.text="Total graph"
            prs.save(path)
            report=audit(path)
        self.assertEqual(report["slides"][0]["text_box_overlaps"],1)
        pair=report["slides"][0]["overlap_pairs"][0]
        self.assertEqual({pair["shape_a"],pair["shape_b"]},{"first_label","second_label"})
        self.assertIn("Frequency band",{pair["text_a"],pair["text_b"]})
        self.assertIn("Total graph",{pair["text_a"],pair["text_b"]})

    def test_non_overlapping_text_boxes_have_empty_pair_list(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"clear.pptx"
            prs=Presentation()
            slide=prs.slides.add_slide(prs.slide_layouts[6])
            slide.shapes.add_textbox(Inches(1),Inches(1),Inches(2),Inches(.3)).text="Title"
            slide.shapes.add_textbox(Inches(1),Inches(2),Inches(2),Inches(.3)).text="Caption"
            prs.save(path)
            report=audit(path)
        self.assertEqual(report["slides"][0]["text_box_overlaps"],0)
        self.assertEqual(report["slides"][0]["overlap_pairs"],[])


if __name__=="__main__":
    unittest.main()
