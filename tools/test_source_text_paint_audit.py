"""Real-PDF regressions for text paint occurrence, order and outline audits."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import fitz
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Pt
from unittest.mock import patch

from audit_imported_pdf_figure import audit_figure
from audit_text_geometry import audit_text_geometry
from pdf_figure_import import _add_drawing, _add_text, convert_pdf_page


def legacy_raw_candidate(source, target):
    """Reproduce the old behavior independently of the current importer."""
    deck = Presentation()
    with fitz.open(source) as document:
        page = document[0]
        deck.slide_width, deck.slide_height = Pt(page.rect.width), Pt(page.rect.height)
        slide = deck.slides.add_slide(deck.slide_layouts[6])
        for drawing in page.get_drawings():
            _add_drawing(slide, drawing, page.rect, [])
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    _add_text(slide, span, line, page.rect)
    deck.save(target)


class SourceTextPaintAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "source.pdf"
        self.target = self.root / "candidate.pptx"

    def tearDown(self):
        self.temp.cleanup()

    def assert_rejected_by_both(self):
        for audit in (audit_figure, audit_text_geometry):
            with self.subTest(audit=audit.__name__):
                self.assertEqual(audit(self.source, self.target)["status"], "FAIL")

    def make_layered_source(self):
        with fitz.open() as document:
            page = document.new_page(width=240, height=140)
            page.draw_rect((20, 30, 150, 95), color=None, fill=(.1, .3, .6))
            page.insert_text((35, 65), "Layer", fontsize=16, color=(1, 1, 1))
            document.save(self.source)
        convert_pdf_page(self.source, self.target)

    def make_fill_stroke_source(self):
        with fitz.open() as document:
            page = document.new_page(width=240, height=140)
            page.insert_text((40, 70), "I", fontsize=16, color=(1, 0, 0),
                             fill=(0, 0, 1), render_mode=2)
            document.save(self.source)
        convert_pdf_page(self.source, self.target)

    def test_source_built_fill_and_stroke_outlines_pass_both_audits(self):
        self.make_fill_stroke_source()
        for audit in (audit_figure, audit_text_geometry):
            with self.subTest(audit=audit.__name__):
                report = audit(self.source, self.target)
                self.assertEqual(report["status"], "PASS")
                self.assertEqual(report["source_text_event_count"], 1)
                self.assertEqual(report["candidate_text_outline_shape_count"], 2)

    def test_missing_stroke_path_is_not_rescued_by_remaining_shape_metadata(self):
        self.make_fill_stroke_source()
        deck = Presentation(self.target)
        slide = deck.slides[0]
        self.assertEqual(len(slide.shapes), 2)
        slide.shapes._spTree.remove(slide.shapes[-1]._element)
        fill = slide.shapes[0]
        node = next(node for node in fill._element.iter() if node.tag.endswith("}cNvPr"))
        data = json.loads(node.get("descr"))
        data.update(source_text="I", source_seqnos=[0, 1], source_order=0)
        node.set("descr", json.dumps(data))
        deck.save(self.target)
        self.assert_rejected_by_both()

    def test_outline_vertex_change_is_detected_without_trusting_bounds_or_metadata(self):
        self.make_fill_stroke_source()
        deck = Presentation(self.target)
        shape = deck.slides[0].shapes[0]
        point = next(node for node in shape._element.iter() if node.tag.endswith("}pt") and "x" in node.attrib)
        point.set("x", str(int(point.get("x")) + 10000))
        deck.save(self.target)
        self.assert_rejected_by_both()

    def test_outline_color_change_is_detected_without_trusting_provenance(self):
        self.make_fill_stroke_source()
        deck = Presentation(self.target)
        deck.slides[0].shapes[0].fill.fore_color.rgb = RGBColor(0, 255, 0)
        deck.save(self.target)
        self.assert_rejected_by_both()

    def test_nonzero_source_opacity_cannot_be_replaced_by_opaque_text(self):
        with fitz.open() as document:
            page = document.new_page(width=240, height=140)
            page.insert_text((40, 70), "Faded", fontsize=16, fill_opacity=.5)
            document.save(self.source)
        convert_pdf_page(self.source, self.target)
        deck = Presentation(self.target)
        for node in list(deck.slides[0].shapes[0]._element.iter()):
            if node.tag.endswith("}alpha"):
                node.getparent().remove(node)
        deck.save(self.target)
        self.assert_rejected_by_both()

    def test_unknown_added_nontext_shape_requires_review(self):
        self.make_layered_source()
        deck = Presentation(self.target)
        deck.slides[0].shapes.add_shape(MSO_SHAPE.RECTANGLE, Pt(40), Pt(55), Pt(10), Pt(10))
        deck.save(self.target)
        for audit in (audit_figure, audit_text_geometry):
            with self.subTest(audit=audit.__name__):
                report = audit(self.source, self.target)
                self.assertEqual(report["status"], "NEEDS_REVIEW")
                self.assertEqual(report["paint_order_status"], "NEEDS_REVIEW")
                self.assertTrue(report["unverified_nontext_shapes"][0]["overlaps_source_text"])

    def test_unsupported_event_collection_reports_failure_and_keeps_diagnostic_denominator(self):
        self.make_layered_source()
        with patch("pdf_text_events.collect_text_events", side_effect=ValueError("UNSUPPORTED_SOURCE_TEXT_TEST")):
            for audit in (audit_figure, audit_text_geometry):
                with self.subTest(audit=audit.__name__):
                    report = audit(self.source, self.target)
                    self.assertEqual(report["status"], "FAIL")
                    self.assertFalse(report["source_text_collection_complete"])
                    self.assertEqual(report["source_text_event_count"], 1)
                    self.assertTrue(report["source_text_event_errors"])

    def test_reordering_actual_text_and_vector_shapes_is_rejected(self):
        self.make_layered_source()
        deck = Presentation(self.target)
        slide = deck.slides[0]
        text = next(s for s in slide.shapes if s.has_text_frame and s.text.strip())
        first = slide.shapes[0]
        first._element.addprevious(text._element)
        deck.save(self.target)
        self.assert_rejected_by_both()

    def test_empty_path_drift_does_not_authorize_mask_before_text(self):
        with fitz.open() as document:
            page = document.new_page(width=240, height=140)
            page.insert_text((40, 70), "HIDDEN", fontsize=16, color=(1, 0, 0))
            xref = page.get_contents()[0]
            document.update_stream(xref, b"q S Q\n" + document.xref_stream(xref))
            page.draw_rect((35, 50, 120, 80), color=None, fill=(1, 1, 1))
            document.save(self.source)
        convert_pdf_page(self.source, self.target)
        for audit in (audit_figure, audit_text_geometry):
            self.assertEqual(audit(self.source, self.target)["status"], "PASS")
        deck = Presentation(self.target)
        slide = deck.slides[0]
        text = next(s for s in slide.shapes if s.has_text_frame and s.text.strip())
        mask = next(s for s in slide.shapes if not (s.has_text_frame and s.text.strip()))
        # Restore the old bug: the legacy vector seq collides with the real
        # text seq, putting the white mask before the red text.
        text._element.addprevious(mask._element)
        node = next(n for n in mask._element.iter() if n.tag.endswith("}cNvPr"))
        data = json.loads(node.get("descr"))
        data["source_order"] = 1
        node.set("descr", json.dumps(data))
        deck.save(self.target)
        self.assert_rejected_by_both()

        # Candidate metadata is neither necessary nor authoritative for the
        # source-derived order check. Keep the physical wrong order and strip
        # every description, preserving only the source-bound shape names.
        for shape in slide.shapes:
            for node in shape._element.iter():
                if node.tag.endswith("}cNvPr"):
                    node.attrib.pop("descr", None)
        deck.save(self.target)
        self.assert_rejected_by_both()

    def test_merged_vector_paint_across_text_is_reported_as_unsupported(self):
        with fitz.open() as document:
            page = document.new_page(width=240, height=140)
            page.draw_rect((20, 30, 100, 90), color=None, fill=(1, 0, 0))
            page.insert_text((40, 70), "Between", fontsize=12)
            page.draw_rect((20, 30, 100, 90), color=(0, 0, 0), fill=None)
            document.save(self.source)
        with self.assertRaisesRegex(ValueError, "MERGED_PAINT_ORDER"):
            convert_pdf_page(self.source, self.target)
        legacy_raw_candidate(self.source, self.target)
        self.assert_rejected_by_both()

    def test_forged_sorted_source_order_cannot_hide_actual_reordering(self):
        self.make_layered_source()
        deck = Presentation(self.target)
        slide = deck.slides[0]
        text = next(s for s in slide.shapes if s.has_text_frame and s.text.strip())
        slide.shapes[0]._element.addprevious(text._element)
        for index, shape in enumerate(slide.shapes):
            node = next(node for node in shape._element.iter() if node.tag.endswith("}cNvPr"))
            metadata = json.loads(node.get("descr", "{}"))
            metadata["source_order"] = index
            metadata["source_seqnos"] = [index]
            node.set("descr", json.dumps(metadata))
        deck.save(self.target)
        self.assert_rejected_by_both()

    def test_old_horizontal_csv_fails_trace_event_audits(self):
        with fitz.open() as document:
            page = document.new_page(width=240, height=140)
            for character, y in zip("CSV", (70, 75.3, 80.6)):
                page.insert_text((40, y), character, fontsize=6.8383889)
            document.save(self.source)
        legacy_raw_candidate(self.source, self.target)
        self.assert_rejected_by_both()

    def test_fill_only_textbox_cannot_stand_in_for_fill_and_stroke(self):
        with fitz.open() as document:
            page = document.new_page(width=240, height=140)
            page.insert_text((40, 70), "I", fontsize=16, color=(1, 0, 0),
                             fill=(0, 0, 1), render_mode=2)
            document.save(self.source)
        legacy_raw_candidate(self.source, self.target)
        self.assert_rejected_by_both()

    def test_rawdict_omission_of_later_white_a_does_not_shrink_source_count(self):
        with fitz.open() as document:
            page = document.new_page(width=240, height=140)
            page.insert_text((40, 70), "A", fontsize=16, color=(0, 0, 0))
            page.draw_circle((45, 64), 12, color=None, fill=(0, 0, 1))
            page.insert_text((40, 70), "A", fontsize=16, color=(1, 1, 1))
            document.save(self.source)
        legacy_raw_candidate(self.source, self.target)
        self.assert_rejected_by_both()
        self.assertEqual(audit_figure(self.source, self.target)["source_text_spans"], 2)
        self.assertEqual(audit_text_geometry(self.source, self.target)["source_text_span_count"], 2)


if __name__ == "__main__":
    unittest.main()
