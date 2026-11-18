"""Checks that a converted scientific diagram remains structurally editable."""

from pathlib import Path
from collections import Counter
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import fitz
from PIL import Image
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pdf_figure_import import convert_pdf_page
from audit_imported_pdf_figure import audit_figure
from audit_text_geometry import audit_text_geometry
from figure_first_pass_gate import source_profile
from pdf_text_visibility import TextVisibility


class FigureAuditTests(unittest.TestCase):
    def test_missing_or_nonzero_alpha_is_not_filtered_by_overlay_fix(self):
        visibility = TextVisibility(SimpleNamespace())
        for span in ({}, {"alpha": 1}, {"alpha": 127}, {"alpha": 255}):
            with self.subTest(span=span):
                self.assertEqual(visibility.classify(span), "visible")

    def test_type3_hidden_text_can_have_a_baseline_outside_its_bbox(self):
        span = {"alpha": 0, "font": "SyntheticType3", "size": 5,
                "text": ":", "origin": (10, 20), "bbox": (10, 12, 15, 17)}
        trace = {"font": "SyntheticType3", "size": 5, "type": 3, "opacity": 1,
                 "bbox": span["bbox"],
                 "chars": [(ord(":"), 1, span["origin"], span["bbox"])]}
        visibility = TextVisibility(SimpleNamespace(get_texttrace=lambda: [trace],
                                    read_contents=lambda: b"", get_xobjects=lambda: []))
        self.assertEqual(visibility.classify(span), "hidden")

    def test_partially_matched_zero_alpha_span_is_not_dropped(self):
        span = {"alpha": 0, "font": "Helvetica", "size": 10,
                "text": "AB", "origin": (10, 20), "bbox": (10, 10, 25, 22)}
        trace = {"font": "Helvetica", "size": 10, "type": 0, "opacity": 0,
                 "bbox": (10, 10, 17, 22),
                 "chars": [(ord("A"), 1, (10, 20), (10, 10, 17, 22))]}
        visibility = TextVisibility(SimpleNamespace(get_texttrace=lambda: [trace],
                                    read_contents=lambda: b"", get_xobjects=lambda: []))
        self.assertEqual(visibility.classify(span), "unsupported")

    def test_transparent_text_clipping_is_not_treated_as_an_inert_overlay(self):
        for mode in (4, 5, 6, 7):
            for nested in (False, True):
                with self.subTest(mode=mode, nested=nested):
                    source = Path(self.temp.name) / f"text-clip-{mode}-{nested}.pdf"
                    flat = source.with_suffix(".flat.pdf") if nested else source
                    pdf = canvas.Canvas(str(flat), pagesize=(300, 180))
                    pdf.setFillAlpha(0)
                    pdf.setStrokeAlpha(0)
                    text = pdf.beginText(20, 100)
                    text.setFont("Helvetica", 30)
                    text.setTextRenderMode(mode)
                    text.textOut("CLIP")
                    pdf.drawText(text)
                    pdf.setFillAlpha(1)
                    pdf.rect(10, 40, 250, 110, fill=1, stroke=0)
                    pdf.save()
                    if nested:
                        with fitz.open(flat) as original, fitz.open() as wrapper:
                            wrapper.new_page(width=300, height=180).show_pdf_page(
                                fitz.Rect(0, 0, 300, 180), original, 0)
                            wrapper.save(source)
                    with fitz.open(source) as original:
                        nonwhite = sum(c != 255 for c in original[0].get_pixmap().samples)
                        self.assertGreater(nonwhite, 100)
                        self.assertLess(nonwhite, 10000)
                    output = source.with_suffix(".pptx")
                    with self.assertRaisesRegex(ValueError, "UNSUPPORTED_SOURCE_TEXT_PAINT_MODE"):
                        convert_pdf_page(source, output)
                    self.assertFalse(output.exists())
                    profile = source_profile(source)
                    self.assertTrue(any(r["code"] == "UNSUPPORTED_TEXT_PAINT_MODE"
                                        for r in profile["risk_flags"]))

    def _zero_fill_stroked_text_source(self, mode):
        root = Path(self.temp.name)
        source = root / f"stroked-text-{mode}.pdf"
        pdf = canvas.Canvas(str(source), pagesize=(300, 180))
        pdf.setFillAlpha(0)
        pdf.setStrokeAlpha(1)
        text = pdf.beginText(20, 80)
        text.setTextRenderMode(mode)
        text.textLine("VISIBLE STROKED LABEL")
        pdf.drawText(text)
        pdf.save()
        return source

    def test_zero_fill_alpha_does_not_hide_visible_stroke_text(self):
        for mode in (2, 6):
            with self.subTest(mode=mode):
                source = self._zero_fill_stroked_text_source(mode)
                with fitz.open(source) as doc:
                    page = doc[0]
                    span = page.get_text("dict")["blocks"][0]["lines"][0]["spans"][0]
                    self.assertEqual(span["alpha"], 0)
                    pixels = page.get_pixmap(clip=fitz.Rect(span["bbox"]))
                    self.assertTrue(any(channel != 255 for channel in pixels.samples))
                output = source.with_suffix(".pptx")
                with self.assertRaisesRegex(ValueError, "UNSUPPORTED_SOURCE_TEXT_PAINT_MODE"):
                    convert_pdf_page(source, output)
                self.assertFalse(output.exists())

    def test_missing_zero_fill_visible_strokes_cannot_pass_source_audits(self):
        for mode in (2, 6):
            with self.subTest(mode=mode):
                source = self._zero_fill_stroked_text_source(mode)
                # MuPDF 2.x may expose fill and stroke as separate dictionary
                # spans for mode 6. Every observed source run must remain
                # required; do not assume one extraction span per text call.
                with fitz.open(source) as original:
                    expected_labels = Counter(s["text"]
                        for b in original[0].get_text("dict")["blocks"]
                        for line in b.get("lines", []) for s in line["spans"]
                        if s["text"].strip())
                self.assertEqual(set(expected_labels), {"VISIBLE STROKED LABEL"})
                expected_count = sum(expected_labels.values())
                self.assertGreaterEqual(expected_count, 1)
                missing = source.with_suffix(".missing.pptx")
                deck = Presentation()
                from pptx.util import Pt
                deck.slide_width, deck.slide_height = Pt(300), Pt(180)
                deck.slides.add_slide(deck.slide_layouts[6])
                deck.save(missing)
                report = audit_figure(source, missing)
                self.assertEqual(report["source_text_spans"], expected_count)
                self.assertEqual(report["status"], "FAIL")
                self.assertEqual(report["missing_text"], dict(expected_labels))
                geometry = audit_text_geometry(source, missing)
                self.assertEqual(geometry["source_text_span_count"], expected_count)
                self.assertEqual(geometry["status"], "FAIL")
                profile = source_profile(source)
                self.assertEqual(profile["source_text_spans"], expected_count)
                self.assertTrue(any(r["code"] == "UNSUPPORTED_TEXT_PAINT_MODE"
                                    for r in profile["risk_flags"]))

    def test_zero_alpha_with_missing_paint_trace_fails_closed(self):
        source, output = self._transparent_text_source()
        with patch.object(fitz.Page, "get_texttrace", return_value=[]):
            with self.assertRaisesRegex(ValueError, "UNSUPPORTED_SOURCE_TEXT_PAINT_MODE"):
                convert_pdf_page(source, output)
            self.assertEqual(source_profile(source)["source_text_spans"], 2)

    def _transparent_text_source(self):
        root = Path(self.temp.name)
        source, result = root / "transparent-text.pdf", root / "transparent-text.pptx"
        pdf = canvas.Canvas(str(source), pagesize=(300, 180))
        pdf.setFillAlpha(0)
        pdf.drawString(20, 80, "Invisible Unicode overlay")
        pdf.setFillAlpha(1)
        pdf.setFillColorRGB(0, 0, 0)
        pdf.rect(15, 105, 150, 25, fill=1, stroke=0)
        pdf.setFillColorRGB(1, 1, 1)
        pdf.drawString(20, 115, "Visible white label")
        pdf.save()
        return source, result

    def test_zero_alpha_overlay_is_not_made_visible_by_import(self):
        source, result = self._transparent_text_source()
        with fitz.open(source) as doc:
            spans = [s for b in doc[0].get_text("dict")["blocks"]
                     for line in b.get("lines", []) for s in line["spans"]]
            invisible = next(s for s in spans if s["text"] == "Invisible Unicode overlay")
            self.assertEqual(invisible["alpha"], 0)
            pixels = doc[0].get_pixmap(clip=fitz.Rect(invisible["bbox"]), alpha=False)
            self.assertTrue(all(channel == 255 for channel in pixels.samples))
        convert_pdf_page(source, result)
        labels = [s.text for s in Presentation(result).slides[0].shapes
                  if s.has_text_frame and s.text.strip()]
        self.assertEqual(labels, ["Visible white label"])

    def test_source_visible_audits_ignore_zero_alpha_overlay(self):
        source, result = self._transparent_text_source()
        convert_pdf_page(source, result)
        deck = Presentation(result)
        for shape in list(deck.slides[0].shapes):
            if shape.has_text_frame and shape.text == "Invisible Unicode overlay":
                deck.slides[0].shapes._spTree.remove(shape._element)
        deck.save(result)
        self.assertEqual(audit_figure(source, result)["status"], "PASS")
        report = audit_text_geometry(source, result)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["source_text_span_count"], 1)

    def _image_source(self, boxes):
        root = Path(self.temp.name)
        source, result = root / "images.pdf", root / "images.pptx"
        image_path = root / "source-image.png"
        Image.new("RGB", (20, 20), (20, 80, 160)).save(image_path)
        with fitz.open() as doc:
            page = doc.new_page(width=360, height=180)
            xref = 0
            for box in boxes:
                xref = page.insert_image(fitz.Rect(box), filename=str(image_path), xref=xref)
            doc.save(source)
        return source, result

    def test_images_outside_selected_crop_do_not_count_as_missing(self):
        source, result = self._image_source([(20, 20, 50, 50), (280, 20, 310, 50)])
        region = (0, 0, 200, 180)
        convert_pdf_page(source, result, figure_region=region)
        with fitz.open(source) as doc:
            full_page_blocks = doc[0].get_text("dict")
        # Some source PDFs / MuPDF versions retain off-crop image metadata in
        # the text dictionary. Paint occurrences remain the crop-aware truth.
        with patch("audit_imported_pdf_figure.fitz.Page.get_text",
                   return_value=full_page_blocks):
            report = audit_figure(source, result, figure_region=region)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["source_pictures"], 1)
        self.assertEqual(report["picture_shapes"], 1)

    def test_repeated_visible_image_occurrences_are_each_required(self):
        source, result = self._image_source([
            (20, 20, 50, 50), (80, 20, 110, 50), (280, 20, 310, 50),
        ])
        region = (0, 0, 200, 180)
        convert_pdf_page(source, result, figure_region=region)
        report = audit_figure(source, result, figure_region=region)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["source_pictures"], 2)
        deck = Presentation(result)
        pictures = [shape for shape in deck.slides[0].shapes
                    if shape.shape_type == MSO_SHAPE_TYPE.PICTURE]
        deck.slides[0].shapes._spTree.remove(pictures[0]._element)
        deck.save(result)
        report = audit_figure(source, result, figure_region=region)
        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["checks"]["source_pictures_retained"])

    def test_unresolved_visible_source_images_fail_closed(self):
        source, result = self._image_source([(20, 20, 50, 50)])
        convert_pdf_page(source, result)
        # A matching number of candidate pictures cannot prove retention when
        # a source paint event could not be resolved to an extractable asset.
        stats = {"source_paint_events": 1, "off_page_image_events": 0,
                 "unresolved_visible_events": 1,
                 "warnings": ["synthetic unresolved visible paint event"]}
        with patch("audit_imported_pdf_figure.collect_image_events", create=True,
                   return_value=([], stats)):
            report = audit_figure(source, result)
        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["checks"]["source_pictures_retained"])
        self.assertEqual(report["source_pictures"], 1)
        self.assertEqual(report["image_extraction"]["unresolved_visible_events"], 1)

    def test_invisible_source_marks_do_not_count_as_missing_vectors(self):
        """Graphics deliberately excluded by a PDF clip region are not losses."""
        with TemporaryDirectory() as root_name:
            root = Path(root_name)
            source, result = root / "hidden.pdf", root / "hidden.pptx"
            pdf = canvas.Canvas(str(source), pagesize=(300, 180))
            clip = pdf.beginPath()
            clip.rect(80, 40, 60, 60)
            pdf.clipPath(clip, stroke=0, fill=0)
            pdf.setFillColorRGB(.2, .4, .7)
            pdf.rect(200, 120, 40, 40, fill=1, stroke=0)
            pdf.rect(85, 45, 20, 20, fill=1, stroke=0)
            pdf.showPage()
            pdf.save()
            convert_pdf_page(source, result)
            report = audit_figure(source, result)
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["visible_source_drawings"], 1)
            self.assertEqual(report["native_vectors"], 1)

    def setUp(self):
        self.temp = TemporaryDirectory()
        root = Path(self.temp.name)
        self.source, self.output = root / "diagram.pdf", root / "diagram.pptx"
        doc = fitz.open()
        page = doc.new_page(width=360, height=180)
        page.draw_rect(fitz.Rect(20, 20, 130, 110), fill=(.7, .9, .8))
        page.draw_line((130, 65), (250, 65), color=(0, .2, .8), width=3)
        page.insert_text((35, 75), "Cache Layer", fontsize=14)
        doc.save(self.source)
        doc.close()
        convert_pdf_page(self.source, self.output)

    def tearDown(self):
        self.temp.cleanup()

    def test_valid_editable_diagram_passes(self):
        report = audit_figure(self.source, self.output)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["missing_text"], {})
        self.assertEqual(report["full_page_pictures"], 0)
        self.assertGreaterEqual(report["vector_retention_ratio"], .95)

    def test_changed_label_is_reported(self):
        deck = Presentation(self.output)
        for shape in deck.slides[0].shapes:
            if shape.has_text_frame and "Cache Layer" in shape.text:
                shape.text = "Cache Other"
        deck.save(self.output)
        report = audit_figure(self.source, self.output)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("Cache Layer", report["missing_text"])

    def test_flattened_figure_is_rejected(self):
        deck = Presentation(self.output)
        for shape in list(deck.slides[0].shapes):
            deck.slides[0].shapes._spTree.remove(shape._element)
        background = Path(self.temp.name) / "flattened.png"
        Image.new("RGB", (720, 360), "white").save(background)
        deck.slides[0].shapes.add_picture(str(background), 0, 0, deck.slide_width, deck.slide_height)
        deck.save(self.output)
        report = audit_figure(self.source, self.output)
        self.assertEqual(report["full_page_pictures"], 1)
        self.assertEqual(report["status"], "FAIL")

    def test_missing_vectors_are_reported(self):
        deck = Presentation(self.output)
        for shape in list(deck.slides[0].shapes):
            if shape.shape_type in (MSO_SHAPE_TYPE.FREEFORM, MSO_SHAPE_TYPE.LINE):
                deck.slides[0].shapes._spTree.remove(shape._element)
        deck.save(self.output)
        report = audit_figure(self.source, self.output)
        self.assertEqual(report["status"], "FAIL")
        self.assertLess(report["vector_retention_ratio"], .1)


if __name__ == "__main__":
    unittest.main()
