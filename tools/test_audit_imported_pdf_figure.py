"""Checks that a converted scientific diagram remains structurally editable."""

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

import fitz
from PIL import Image
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pdf_figure_import import convert_pdf_page
from audit_imported_pdf_figure import audit_figure


class FigureAuditTests(unittest.TestCase):
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
            pdf.showPage()
            pdf.save()
            convert_pdf_page(source, result)
            report = audit_figure(source, result)
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["visible_source_drawings"], 0)
            self.assertEqual(report["native_vectors"], 0)

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
