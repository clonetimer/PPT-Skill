"""Regression tests for source-faithful PDF text geometry and glyph mapping."""
from __future__ import annotations

import math
from pathlib import Path
import tempfile
import unittest

import fitz
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from pdf_figure_import import convert_pdf_page, _source_font, _normalize_pdf_text, _span_visible_fraction, _add_text


def aabb(shape):
    angle = math.radians(shape.rotation)
    w = abs(math.cos(angle)) * shape.width + abs(math.sin(angle)) * shape.height
    h = abs(math.sin(angle)) * shape.width + abs(math.cos(angle)) * shape.height
    cx = shape.left + shape.width / 2
    cy = shape.top + shape.height / 2
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


def intersects(a, b, threshold=2.16 * 12700):
    iw = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    ih = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    return iw > threshold and ih > threshold


class TextGeometryImportTests(unittest.TestCase):
    def test_adjacent_source_spans_do_not_gain_false_overlap(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "adjacent.pdf"
            output = Path(tmp) / "adjacent.pptx"
            doc = fitz.open()
            page = doc.new_page(width=240, height=120)
            page.insert_text((40, 50), "A", fontsize=12, fontname="helv")
            page.insert_text((48, 50), "B", fontsize=12, fontname="tiro")
            source_spans = [s for b in page.get_text("dict")["blocks"]
                            for line in b.get("lines", []) for s in line["spans"]]
            self.assertEqual(len(source_spans), 2)
            source_rects = [fitz.Rect(s["bbox"]) for s in source_spans]
            self.assertLessEqual(source_rects[0].x1, source_rects[1].x0 + .01)
            doc.save(source)
            doc.close()
            convert_pdf_page(source, output)
            deck = Presentation(output)
            text_shapes = [s for s in deck.slides[0].shapes
                           if s.shape_type == MSO_SHAPE_TYPE.TEXT_BOX and s.text.strip()]
            self.assertEqual(len(text_shapes), 2)
            self.assertFalse(intersects(aabb(text_shapes[0]), aabb(text_shapes[1])),
                             "importer padding must not create a collision absent in source")

    def test_rotated_span_uses_oriented_quad_instead_of_rotating_axis_aligned_bbox_twice(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "rotated.pdf"
            output = Path(tmp) / "rotated.pptx"
            doc = fitz.open()
            page = doc.new_page(width=300, height=200)
            matrix = fitz.Matrix(1, 1).prerotate(30)
            page.insert_text(fitz.Point(100, 100), "Rotated Label", fontsize=12,
                             fontname="helv", morph=(fitz.Point(100, 100), matrix))
            line = next(line for block in page.get_text("dict")["blocks"]
                        for line in block.get("lines", []))
            span = line["spans"][0]
            source_rect = fitz.Rect(span["bbox"])
            doc.save(source)
            doc.close()
            convert_pdf_page(source, output)
            deck = Presentation(output)
            shape = next(s for s in deck.slides[0].shapes
                         if s.shape_type == MSO_SHAPE_TYPE.TEXT_BOX and s.text.strip())
            x0, y0, x1, y1 = aabb(shape)
            self.assertAlmostEqual(x0 / 12700, source_rect.x0, delta=2.0)
            self.assertAlmostEqual(y0 / 12700, source_rect.y0, delta=2.0)
            self.assertAlmostEqual(x1 / 12700, source_rect.x1, delta=2.0)
            self.assertAlmostEqual(y1 / 12700, source_rect.y1, delta=2.0)

    def test_known_pdf_font_families_map_to_office_available_fallbacks(self):
        self.assertEqual(_source_font("CalisMTBol"), "Calisto MT")
        self.assertEqual(_source_font("CalistoMT-Italic"), "Calisto MT")
        self.assertEqual(_source_font("TeXGyreTermesX-Regular"), "Times New Roman")
        self.assertEqual(_source_font("LinLibertineTB"), "Times New Roman")
        self.assertEqual(_source_font("Unnamed-T3"), "Arial")
        self.assertEqual(_source_font("STIXTwoMath-Regular"), "Cambria Math")
        self.assertEqual(_source_font("ArialMT"), "Arial")
        self.assertEqual(_source_font("ComicSansMS-Bold"), "Comic Sans MS")

    def test_pdf_null_glyph_uses_visible_placeholder_and_is_not_emitted_as_control(self):
        self.assertEqual(_normalize_pdf_text("Revenue\x00Operating Cost"), "Revenue□Operating Cost")

    def test_text_with_only_nine_percent_visible_at_crop_edge_is_omitted(self):
        span = {"bbox": (6.0, 283.2, 16.0, 293.2)}
        page_rect = fitz.Rect(0, 0, 505, 284.1)
        self.assertAlmostEqual(_span_visible_fraction(span, page_rect), .09, delta=.002)
        self.assertLess(_span_visible_fraction(span, page_rect), .2)
        deck = Presentation()
        slide = deck.slides.add_slide(deck.slide_layouts[6])
        source_span = {
            "bbox": span["bbox"], "text": "footer", "size": 10,
            "font": "Helvetica", "flags": 0, "color": 0
        }
        self.assertFalse(_add_text(slide, source_span, {"dir": (1, 0)}, page_rect))
        self.assertEqual(len(slide.shapes), 0)

    def test_math_glyphs_survive_pdf_to_editable_text_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "math.pdf"
            output = Path(tmp) / "math.pptx"
            doc = fitz.open()
            page = doc.new_page(width=300, height=120)
            fontfile = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            if not Path(fontfile).exists():
                self.skipTest("DejaVu Sans fixture font is unavailable")
            expected = "θₜ → β²"
            page.insert_text((30, 60), expected, fontsize=14,
                             fontfile=fontfile, fontname="DejaVuSans")
            source_text = page.get_text().strip()
            self.assertEqual(source_text, expected)
            doc.save(source)
            doc.close()
            convert_pdf_page(source, output)
            deck = Presentation(output)
            actual = "".join(s.text for s in deck.slides[0].shapes
                             if s.shape_type == MSO_SHAPE_TYPE.TEXT_BOX)
            self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
