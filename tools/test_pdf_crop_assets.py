"""Crop-aware PDF image/XRef regressions; synthetic copyright-free fixtures."""
from __future__ import annotations

import io
from pathlib import Path
import tempfile
import unittest

import fitz
from PIL import Image
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from pdf_source_assets import collect_image_events
from pdf_figure_import import convert_pdf_page


def create_source(path: Path, *, outside: bool = False, overlay: bool = True):
    document = fitz.open()
    page = document.new_page(width=600, height=480)
    image_bytes = io.BytesIO()
    Image.new("RGB", (120, 80), (230, 90, 35)).save(image_bytes, "PNG")
    page.insert_image(fitz.Rect(90, 110, 380, 280), stream=image_bytes.getvalue())
    if overlay:
        page.draw_rect(fitz.Rect(130, 140, 350, 250), color=(0, 0, 1), width=1.5)
    if outside:
        page.insert_image(fitz.Rect(470, 370, 590, 455), stream=image_bytes.getvalue())
    page.set_cropbox(fitz.Rect(100, 100, 400, 330))
    document.save(path)
    document.close()


class ImageRecoveryTests(unittest.TestCase):
    def test_recovers_xref_when_text_dict_returns_zero_image_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"crop.pdf"
            create_source(path, outside=True)
            with fitz.open(path) as document:
                page = document[0]
                events, diagnostics = collect_image_events(page, document, image_blocks=[])
                self.assertEqual(len(events), 1)
                self.assertGreater(events[0].xref, 0)
                self.assertEqual(events[0].source_kind, "xref-fallback")
                self.assertTrue(events[0].png)
                self.assertEqual(events[0].bbox & page.rect, events[0].visible_bbox)
                self.assertGreaterEqual(diagnostics["off_page_image_events"], 1)

    def test_import_preserves_image_then_vector_z_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)/"crop.pdf"
            output = Path(tmp)/"crop.pptx"
            create_source(source)
            report = convert_pdf_page(source, output)
            deck = Presentation(output)
            shapes = list(deck.slides[0].shapes)
            images = [s for s in shapes if s.shape_type == MSO_SHAPE_TYPE.PICTURE]
            self.assertEqual(report["picture_shapes"], 1)
            self.assertTrue(images)
            self.assertEqual(shapes[0].shape_type, MSO_SHAPE_TYPE.PICTURE)
            self.assertGreater(report["native_shapes"], 0)
            self.assertEqual(report["source_image_events"], 1)
            self.assertTrue(all(s.left >= 0 and s.top >= 0 and
                                s.left+s.width <= deck.slide_width and
                                s.top+s.height <= deck.slide_height for s in images))

    def test_import_partially_visible_image_does_not_exceed_slide(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp)/"crop.pdf"
            out = Path(tmp)/"crop.pptx"
            create_source(src, overlay=False)
            report = convert_pdf_page(src, out)
            slide = Presentation(out)
            pics = [s for s in slide.slides[0].shapes if s.shape_type == MSO_SHAPE_TYPE.PICTURE]
            self.assertEqual(len(pics), 1)
            self.assertEqual(report["picture_shapes"], 1)
            self.assertEqual(report["reconstruction_class"], "source_picture_only")
            self.assertTrue(all(0 <= s.left and 0 <= s.top and
                                s.left+s.width <= slide.slide_width and
                                s.top+s.height <= slide.slide_height for s in pics))

    def test_recovery_does_not_duplicate_source_image_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp)/"crop.pdf"
            create_source(src)
            with fitz.open(src) as document:
                p = document[0]
                original = [b for b in p.get_text("dict")["blocks"] if b["type"] == 1]
                events, _ = collect_image_events(p, document, image_blocks=original)
                self.assertEqual(len(events), 1)

    def test_empty_source_is_not_mislabeled_successful(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp)/"empty.pdf"
            out = Path(tmp)/"empty.pptx"
            d = fitz.open()
            d.new_page(width=320, height=200)
            d.save(src)
            d.close()
            with self.assertRaisesRegex(ValueError, "NO_VISIBLE_SOURCE_CONTENT"):
                convert_pdf_page(src, out)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
