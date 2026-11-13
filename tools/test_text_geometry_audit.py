"""Source-aware audit for text overlap, clipping, font and glyph fidelity."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import fitz
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from pdf_figure_import import convert_pdf_page
from audit_text_geometry import audit_text_geometry


def make_two_spans(path: Path, *, overlap: bool = False):
    doc = fitz.open()
    page = doc.new_page(width=240, height=120)
    page.insert_text((40, 50), "A", fontsize=12, fontname="helv")
    page.insert_text((40 if overlap else 48, 50), "B", fontsize=12, fontname="tiro")
    doc.save(path)
    doc.close()


class TextGeometryAuditTests(unittest.TestCase):
    def test_source_intentional_overlap_is_not_reported_as_introduced(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp)/"source.pdf", Path(tmp)/"source.pptx"
            make_two_spans(source, overlap=True)
            convert_pdf_page(source, output)
            report = audit_text_geometry(source, output)
            self.assertGreaterEqual(report["source_overlap_count"], 1)
            self.assertEqual(report["introduced_overlap_count"], 0)
            self.assertEqual(report["status"], "PASS")

    def test_candidate_only_overlap_is_a_hard_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp)/"source.pdf", Path(tmp)/"candidate.pptx"
            make_two_spans(source)
            convert_pdf_page(source, output)
            deck = Presentation(output)
            text_shapes = [s for s in deck.slides[0].shapes
                           if s.shape_type == MSO_SHAPE_TYPE.TEXT_BOX and s.text.strip()]
            text_shapes[1].left = text_shapes[0].left
            deck.save(output)
            report = audit_text_geometry(source, output)
            self.assertGreater(report["introduced_overlap_count"], 0)
            self.assertEqual(report["status"], "FAIL")

    def test_candidate_text_corruption_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp)/"math.pdf", Path(tmp)/"math.pptx"
            doc = fitz.open()
            page = doc.new_page(width=240, height=120)
            fontfile = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            if not Path(fontfile).exists():
                self.skipTest("DejaVu Sans fixture font is unavailable")
            page.insert_text((30, 60), "θₜ → β²", fontsize=14,
                             fontfile=fontfile, fontname="DejaVuSans")
            doc.save(source)
            doc.close()
            convert_pdf_page(source, output)
            deck = Presentation(output)
            shape = next(s for s in deck.slides[0].shapes
                         if s.shape_type == MSO_SHAPE_TYPE.TEXT_BOX and s.text.strip())
            shape.text = "theta_t -> beta2"
            deck.save(output)
            report = audit_text_geometry(source, output)
            self.assertEqual(report["text_mismatch_count"], 1)
            self.assertEqual(report["status"], "FAIL")

    def test_candidate_only_out_of_bounds_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp)/"source.pdf", Path(tmp)/"source.pptx"
            doc = fitz.open()
            page = doc.new_page(width=240, height=120)
            page.insert_text((30, 50), "Inside", fontsize=12)
            doc.save(source)
            doc.close()
            convert_pdf_page(source, output)
            deck = Presentation(output)
            shape = next(s for s in deck.slides[0].shapes
                         if s.shape_type == MSO_SHAPE_TYPE.TEXT_BOX and s.text.strip())
            shape.left = deck.slide_width + 10000
            deck.save(output)
            report = audit_text_geometry(source, output)
            self.assertEqual(report["introduced_out_of_bounds_count"], 1)
            self.assertEqual(report["status"], "FAIL")

    def test_source_clipped_text_is_not_misreported_as_new_overflow(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp)/"cropped.pdf", Path(tmp)/"cropped.pptx"
            doc = fitz.open()
            page = doc.new_page(width=120, height=80)
            page.insert_text((108, 40), "clipped", fontsize=12)
            doc.save(source)
            doc.close()
            convert_pdf_page(source, output)
            report = audit_text_geometry(source, output)
            self.assertGreaterEqual(report["source_out_of_bounds_count"], 1)
            self.assertEqual(report["introduced_out_of_bounds_count"], 0)
            self.assertEqual(report["status"], "PASS")

    def test_report_records_font_substitution_and_math_codepoints(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp)/"math.pdf", Path(tmp)/"math.pptx"
            doc = fitz.open()
            page = doc.new_page(width=240, height=120)
            fontfile = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            if not Path(fontfile).exists():
                self.skipTest("DejaVu Sans fixture font is unavailable")
            page.insert_text((30, 60), "θₜ → β²", fontsize=14,
                             fontfile=fontfile, fontname="DejaVuSans")
            doc.save(source)
            doc.close()
            convert_pdf_page(source, output)
            report = audit_text_geometry(source, output)
            self.assertEqual(report["text_mismatch_count"], 0)
            self.assertGreaterEqual(report["math_glyph_count"], 4)
            self.assertTrue(report["font_mappings"])


if __name__ == "__main__":
    unittest.main()
