"""Source-PDF to editable-PowerPoint behavioral regression tests."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
import zipfile

import fitz
from PIL import Image
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pdf_figure_import import convert_pdf_page, _source_font, _normalize_pdf_text


class NativeFigureImportTests(unittest.TestCase):
    def test_image_is_placed_at_its_original_paint_order(self):
        """Later paper thumbnails must not be hidden below earlier vector panels."""
        with TemporaryDirectory() as temp:
            root = Path(temp)
            pdf_path, pptx_path = root / "zorder.pdf", root / "zorder.pptx"
            doc = fitz.open()
            page = doc.new_page(width=240, height=140)
            page.draw_rect(fitz.Rect(20, 20, 190, 120), fill=(.9, .9, .9))
            buf = BytesIO()
            Image.new("RGB", (16, 16), (250, 100, 30)).save(buf, format="PNG")
            page.insert_image(fitz.Rect(30, 30, 130, 110), stream=buf.getvalue())
            page.draw_rect(fitz.Rect(120, 30, 180, 60), fill=(.1, .4, .2))
            doc.save(pdf_path)
            doc.close()
            convert_pdf_page(pdf_path, pptx_path)
            ordered_types = [shape.shape_type for shape in Presentation(pptx_path).slides[0].shapes]
            self.assertEqual(
                ordered_types,
                [MSO_SHAPE_TYPE.FREEFORM, MSO_SHAPE_TYPE.PICTURE, MSO_SHAPE_TYPE.FREEFORM],
            )

    def test_respects_rectangular_pdf_clipping_paths(self):
        """Charts with clipping regions must not spill across adjacent panels."""
        with TemporaryDirectory() as temp:
            root = Path(temp)
            pdf_path, pptx_path = root / "clipped.pdf", root / "clipped.pptx"
            drawing = canvas.Canvas(str(pdf_path), pagesize=(300, 180))
            clip = drawing.beginPath()
            clip.rect(80, 40, 60, 60)
            drawing.clipPath(clip, stroke=0, fill=0)
            drawing.setFillColorRGB(.9, .2, .1)
            drawing.rect(10, 10, 200, 140, fill=1, stroke=0)
            drawing.showPage()
            drawing.save()
            with fitz.open(pdf_path) as source:
                self.assertTrue(any(d["type"] == "clip" for d in source[0].get_drawings(extended=True)))
            convert_pdf_page(pdf_path, pptx_path)
            deck = Presentation(pptx_path)
            vectors = [s for s in deck.slides[0].shapes if s.shape_type == MSO_SHAPE_TYPE.FREEFORM]
            self.assertEqual(len(vectors), 1)
            self.assertAlmostEqual(vectors[0].left.pt, 80, delta=.1)
            self.assertAlmostEqual(vectors[0].top.pt, 80, delta=.1)
            self.assertAlmostEqual(vectors[0].width.pt, 60, delta=.1)
            self.assertAlmostEqual(vectors[0].height.pt, 60, delta=.1)

    def test_unrepresentable_pdf_strokes_are_audited_not_fatal(self):
        """Malformed stroke widths must not abort a complex scientific figure."""
        with TemporaryDirectory() as temp:
            root = Path(temp)
            pdf_path, pptx_path = root / "stroke.pdf", root / "stroke.pptx"
            doc = fitz.open()
            page = doc.new_page(width=300, height=150)
            page.draw_line((20, 30), (100, 50), color=(.2, .3, .4), width=9525)
            doc.save(pdf_path)
            doc.close()
            report = convert_pdf_page(pdf_path, pptx_path)
            self.assertTrue(pptx_path.exists())
            self.assertTrue(any("stroke width" in note for note in report["warnings"]))

    def test_compound_filled_paths_retain_cutouts(self):
        """PDF compound shapes must retain their holes rather than paint them solid."""
        with TemporaryDirectory() as temp:
            root = Path(temp)
            pdf_path, pptx_path = root / "compound.pdf", root / "compound.pptx"
            doc = fitz.open()
            page = doc.new_page(width=180, height=120)
            shape = page.new_shape()
            shape.draw_rect(fitz.Rect(20, 20, 140, 100))
            shape.draw_rect(fitz.Rect(50, 45, 110, 75))
            shape.finish(fill=(0.1, 0.1, 0.1), even_odd=True, closePath=True)
            shape.commit()
            doc.save(pdf_path)
            doc.close()
            with fitz.open(pdf_path) as source:
                self.assertEqual(len(source[0].get_drawings()), 1)
                self.assertEqual(len(source[0].get_drawings()[0]["items"]), 2)
            report = convert_pdf_page(pdf_path, pptx_path)
            self.assertEqual(report["native_shapes"], 1)
            with zipfile.ZipFile(pptx_path) as package:
                xml = package.read("ppt/slides/slide1.xml").decode("utf-8")
            self.assertEqual(xml.count("<a:moveTo>"), 2)

    def test_imports_inline_pdf_images_without_xref(self):
        """PDF inline images cannot be silently omitted as xref=0."""
        with TemporaryDirectory() as temp:
            root = Path(temp)
            pdf_path, pptx_path = root / "inline.pdf", root / "inline.pptx"
            drawing = canvas.Canvas(str(pdf_path), pagesize=(300, 150))
            drawing.drawInlineImage(Image.new("RGB", (16, 16), (230, 110, 30)), 30, 40, 50, 50)
            drawing.showPage()
            drawing.save()
            with fitz.open(pdf_path) as pdf:
                self.assertTrue(any(not x.get("xref") for x in pdf[0].get_image_info(xrefs=True)))
            report = convert_pdf_page(pdf_path, pptx_path)
            self.assertEqual(report["picture_shapes"], 1)
            self.assertNotIn("inline image without XREF not imported", report["warnings"])

    def test_soft_hyphens_are_visible_in_powerpoint(self):
        """PDF soft-hyphen mappings otherwise erase method names in PPTX."""
        self.assertEqual(
            _normalize_pdf_text("Zero\xadAPI\xa0MMKHG\xa0Construction"),
            "Zero-API MMKHG Construction",
        )

    def test_semitransparent_hyperedge_preserves_pdf_alpha(self):
        """Forgetting fill alpha changes every overlapping hyperedge color."""
        with TemporaryDirectory() as temp:
            root = Path(temp)
            pdf_path, pptx_path = root / "alpha.pdf", root / "alpha.pptx"
            doc = fitz.open()
            page = doc.new_page(width=300, height=180)
            page.draw_rect(
                fitz.Rect(15, 20, 200, 140),
                color=(0.2, 0.3, 0.4), fill=(0.8, 0.2, 0.2),
                fill_opacity=.5, stroke_opacity=.75,
            )
            doc.save(pdf_path)
            doc.close()
            convert_pdf_page(pdf_path, pptx_path)
            with zipfile.ZipFile(pptx_path) as package:
                xml = package.read("ppt/slides/slide1.xml").decode("utf-8")
            self.assertIn('val="50000"', xml)
            self.assertIn('val="75000"', xml)

    def test_pdf_math_font_maps_to_office_math_font(self):
        """Substituting an unknown PDF math font garbles scientific symbols."""
        self.assertEqual(_source_font("LatinModernMath-Regular"), "Cambria Math")

    def test_preserves_editable_vectors_text_photo_and_dimensions(self):
        """A vector path must not turn into a full-page picture or disappear."""
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.pdf"
            result = root / "redrawn.pptx"
            pdf = fitz.open()
            page = pdf.new_page(width=720, height=360)
            page.draw_rect(fitz.Rect(36, 40, 270, 180), color=(0.1, 0.2, 0.6), fill=(0.9, 0.95, 1.0), width=3)
            page.draw_line(fitz.Point(270, 110), fitz.Point(350, 110), color=(0.8, 0.2, 0.1), width=2)
            page.draw_bezier(
                fitz.Point(350, 110), fitz.Point(380, 50),
                fitz.Point(460, 190), fitz.Point(500, 110),
                color=(0.1, 0.5, 0.3), width=2,
            )
            page.insert_text((65, 100), "Cache Layer", fontsize=20, fontname="helv")
            pix = Image.new("RGBA", (20, 20), (250, 210, 20, 190))
            img_bytes = BytesIO()
            pix.save(img_bytes, format="PNG")
            page.insert_image(fitz.Rect(560, 60, 620, 120), stream=img_bytes.getvalue())
            pdf.save(source)
            pdf.close()

            report = convert_pdf_page(source, result)
            deck = Presentation(result)
            shapes = list(deck.slides[0].shapes)
            pics = [s for s in shapes if s.shape_type == MSO_SHAPE_TYPE.PICTURE]
            editable_text = [s.text for s in shapes if s.has_text_frame]

            self.assertEqual(report["page_size_pt"], [720.0, 360.0])
            self.assertAlmostEqual(deck.slide_width / deck.slide_height, 2.0, places=4)
            self.assertEqual(report["picture_shapes"], 1)
            self.assertGreaterEqual(report["native_shapes"], 3)
            self.assertGreaterEqual(report["text_shapes"], 1)
            self.assertEqual(len(pics), 1)
            self.assertTrue(any("Cache Layer" in s for s in editable_text))
            self.assertTrue(all(p.width < deck.slide_width / 2 for p in pics))
            self.assertEqual(len(report["source_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
