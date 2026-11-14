"""Source-PDF to editable-PowerPoint behavioral regression tests."""

from __future__ import annotations

from io import BytesIO
import hashlib
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import zipfile

import fitz
from PIL import Image
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pdf_figure_import import convert_pdf_page, _source_font, _normalize_pdf_text
import pdf_figure_import


class NativeFigureImportTests(unittest.TestCase):
    def test_large_off_crop_path_is_not_expanded_after_budget_preflight(self):
        """A source path excluded from crop budget cannot consume render work."""
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source, target = root / "busy.pdf", root / "selected.pptx"
            doc = fitz.open()
            page = doc.new_page(width=400, height=250)
            shape = page.new_shape()
            for n in range(90):
                y = 10 + n % 40
                shape.draw_bezier((10, y), (30, y+5), (35, y+10), (45, y+12))
            shape.finish(color=(1, 0, 0))
            shape.commit()
            page.draw_rect(fitz.Rect(240, 120, 310, 180), color=(0, 0, 1))
            doc.save(source)
            doc.close()
            original = pdf_figure_import._subpaths

            def bounded_expansion(items):
                if len(items) > 10:
                    raise RuntimeError("OFF_CROP_PATH_EXPANSION")
                return original(items)

            with patch("pdf_figure_import._subpaths", side_effect=bounded_expansion):
                report = convert_pdf_page(
                    source, target, figure_region=(200, 100, 360, 220),
                    max_source_segments=2,
                )
            self.assertEqual(report["resource_profile"]["drawings"], 1)
            self.assertEqual(report["native_shapes"], 1)

    def test_source_pdf_and_hardlink_cannot_be_overwritten_by_pptx(self):
        """Direct API output aliasing may never corrupt the original PDF."""
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source, alias = root / "paper.pdf", root / "linked.pptx"
            doc = fitz.open()
            page = doc.new_page(width=120, height=100)
            page.draw_rect(fitz.Rect(20, 20, 50, 50))
            doc.save(source)
            doc.close()
            before = source.read_bytes()
            with self.assertRaisesRegex(ValueError, "REFUSE_TO_OVERWRITE_SOURCE_PDF"):
                convert_pdf_page(source, source)
            os.link(source, alias)
            with self.assertRaisesRegex(ValueError, "REFUSE_TO_OVERWRITE_SOURCE_PDF"):
                convert_pdf_page(source, alias)
            self.assertEqual(source.read_bytes(), before)

    def test_rotated_crop_image_fails_closed_before_pptx_render(self):
        """Bounding-box placement would distort a rotated source image."""
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source, target = root / "rotated-image.pdf", root / "candidate.pptx"
            doc = fitz.open()
            page = doc.new_page(width=300, height=250)
            image = BytesIO()
            Image.new("RGB", (30, 50), "blue").save(image, "PNG")
            page.insert_image(fitz.Rect(80, 60, 220, 180),
                              stream=image.getvalue(), rotate=90)
            doc.save(source)
            doc.close()
            with self.assertRaisesRegex(ValueError, "UNSUPPORTED_SOURCE_IMAGE_TRANSFORM"):
                convert_pdf_page(source, target, figure_region=(100, 80, 200, 160))
            self.assertFalse(target.exists())

    def test_partially_visible_source_text_requires_explicit_reconstruction(self):
        """Editable full glyphs cannot impersonate cropped paper glyphs."""
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source, target = root / "edge-text.pdf", root / "candidate.pptx"
            doc = fitz.open()
            page = doc.new_page(width=300, height=180)
            page.insert_text((20, 50), "MMMM", fontsize=30)
            doc.save(source)
            doc.close()
            with self.assertRaisesRegex(ValueError, "UNSUPPORTED_SOURCE_CROP_EDGE_TEXT"):
                convert_pdf_page(source, target, figure_region=(22, 0, 122, 100))
            self.assertFalse(target.exists())

    def test_wide_stroke_entering_crop_without_centerline_fails_closed(self):
        """A visible ink fringe must not vanish while conversion claims success."""
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source, target = root / "edge-stroke.pdf", root / "candidate.pptx"
            doc = fitz.open()
            page = doc.new_page(width=250, height=180)
            page.draw_line((49, 30), (49, 120), width=6, color=(0, 0, 0))
            page.draw_rect(fitz.Rect(80, 30, 120, 60), color=(0, 0, 1))
            doc.save(source)
            doc.close()
            with self.assertRaisesRegex(ValueError, "UNSUPPORTED_SOURCE_CROP_EDGE_STROKE"):
                convert_pdf_page(source, target, figure_region=(50, 0, 170, 140))
            self.assertFalse(target.exists())

    def test_horizontal_strokes_in_selected_crop_count_as_visible_drawings(self):
        """Zero-height PDF line bboxes are still real editable source strokes."""
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source, target = root / "lines.pdf", root / "selected.pptx"
            doc = fitz.open()
            page = doc.new_page(width=360, height=240)
            page.draw_line((20, 30), (100, 30), color=(1, 0, 0), width=2)
            page.draw_line((220, 140), (290, 140), color=(0, 0, 1), width=2)
            doc.save(source)
            doc.close()
            report = convert_pdf_page(
                source, target, figure_region=(200, 100, 320, 200), max_drawings=1
            )
            self.assertEqual(report["resource_profile"]["drawings"], 1)
            self.assertEqual(report["native_shapes"], 1)

    def test_selected_figure_crop_excludes_page_neighbor_content_and_keeps_native_objects(self):
        """Regression: --region cannot import the paper's surrounding figures."""
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source, target = root / "paper.pdf", root / "figure.pptx"
            doc = fitz.open()
            page = doc.new_page(width=420, height=300)
            for x in (10, 40, 70, 100):
                page.draw_rect(fitz.Rect(x, 12, x + 18, 32), color=(1, 0, 0))
            page.insert_text((30, 82), "OUTSIDE", fontsize=11)
            image = BytesIO()
            Image.new("RGB", (24, 20), "red").save(image, "PNG")
            page.insert_image(fitz.Rect(30, 130, 80, 180), stream=image.getvalue())
            page.draw_rect(fitz.Rect(180, 115, 230, 155), color=(.2, .3, .5))
            page.draw_rect(fitz.Rect(250, 160, 320, 210), color=(.2, .3, .5))
            page.insert_text((260, 235), "INSIDE", fontsize=11)
            page.insert_image(fitz.Rect(280, 120, 350, 150), stream=image.getvalue())
            doc.save(source)
            doc.close()
            before = hashlib.sha256(source.read_bytes()).hexdigest()

            report = convert_pdf_page(
                source, target, figure_region=(200, 100, 380, 260),
                max_drawings=2,
            )
            deck = Presentation(target)
            shapes = list(deck.slides[0].shapes)
            self.assertEqual([deck.slide_width.pt, deck.slide_height.pt], [180, 160])
            self.assertEqual(report["page_size_pt"], [180.0, 160.0])
            self.assertEqual(report["figure_region_pt"], [200.0, 100.0, 380.0, 260.0])
            self.assertEqual(report["resource_profile"]["drawings"], 2)
            self.assertEqual(report["native_shapes"], 2)
            self.assertEqual(report["picture_shapes"], 1)
            self.assertEqual([s.text for s in shapes if s.has_text_frame and s.text.strip()], ["INSIDE"])
            self.assertTrue(any(s.left.pt <= .1 and s.top.pt <= 15.1 for s in shapes
                                if s.shape_type == MSO_SHAPE_TYPE.FREEFORM))
            self.assertTrue(all(s.left.pt >= -.1 and s.top.pt >= -.1 and
                                s.left.pt+s.width.pt <= 180.1 and
                                s.top.pt+s.height.pt <= 160.1 for s in shapes))
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), before)

    def test_selected_crop_clips_partly_visible_image_without_flattening_slide(self):
        """Image intersection must be an independently editable clipped picture."""
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source, target = root / "paper.pdf", root / "figure.pptx"
            doc = fitz.open()
            page = doc.new_page(width=360, height=240)
            image = BytesIO()
            Image.new("RGB", (80, 80), "green").save(image, "PNG")
            page.insert_image(fitz.Rect(180, 110, 260, 190), stream=image.getvalue())
            doc.save(source)
            doc.close()
            report = convert_pdf_page(source, target, figure_region=(200, 100, 300, 210))
            deck = Presentation(target)
            pictures = [s for s in deck.slides[0].shapes
                        if s.shape_type == MSO_SHAPE_TYPE.PICTURE]
            self.assertEqual(len(pictures), 1)
            self.assertAlmostEqual(pictures[0].left.pt, 0, delta=.1)
            self.assertAlmostEqual(pictures[0].top.pt, 10, delta=.1)
            self.assertAlmostEqual(pictures[0].width.pt, 60, delta=.1)
            self.assertAlmostEqual(pictures[0].height.pt, 80, delta=.1)
            self.assertEqual(report["reconstruction_class"], "source_picture_only")

    def test_invalid_or_rotated_selected_crop_fails_without_writing_candidate(self):
        """A wrong crop must not silently fall back to a full-page reconstruction."""
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source, target = root / "paper.pdf", root / "figure.pptx"
            doc = fitz.open()
            page = doc.new_page(width=360, height=240)
            page.draw_rect(fitz.Rect(30, 30, 70, 80))
            doc.save(source)
            doc.close()
            for region in ((0, 0, 400, 200), (200, 30, 180, 100),
                           (0, 0, 0, 100), (float("nan"), 0, 200, 100)):
                with self.subTest(region=region):
                    with self.assertRaisesRegex(ValueError, "INVALID_FIGURE_REGION"):
                        convert_pdf_page(source, target, figure_region=region)
                    self.assertFalse(target.exists())
            with fitz.open(source) as doc:
                doc[0].set_rotation(90)
                doc.save(root / "rotated.pdf")
            with self.assertRaisesRegex(ValueError, "UNSUPPORTED_ROTATED_SOURCE_CROP"):
                convert_pdf_page(root / "rotated.pdf", target, figure_region=(20, 20, 100, 100))
            self.assertFalse(target.exists())

    def test_radar_circle_imports_as_editable_native_oval(self):
        """Prevent missing outer rings in a previously unseen radar diagram."""
        with TemporaryDirectory() as temp:
            root = Path(temp)
            pdf_path, pptx_path = root / "polar.pdf", root / "polar.pptx"
            doc = fitz.open()
            page = doc.new_page(width=300, height=200)
            shape = page.new_shape()
            shape.draw_circle(fitz.Point(120, 100), 45)
            shape.finish(color=(0.3, 0.4, 0.6), width=0.5)
            shape.commit()
            doc.save(pdf_path)
            doc.close()
            with fitz.open(pdf_path) as source:
                source_drawings = source[0].get_drawings()
                self.assertEqual([p[0] for p in source_drawings[0]["items"]], ["c"] * 4)
            report = convert_pdf_page(pdf_path, pptx_path)
            self.assertEqual(report["native_shapes"], 1)
            slide = Presentation(pptx_path).slides[0]
            ovals = [s for s in slide.shapes if s.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE]
            self.assertEqual(len(ovals), 1)
            self.assertEqual(len([s for s in slide.shapes if s.shape_type == MSO_SHAPE_TYPE.PICTURE]), 0)


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
            page.draw_rect(fitz.Rect(30, 40, 90, 100), color=(0.1, 0.4, 0.6))
            page.draw_line((20, 30), (100, 50), color=(.2, .3, .4), width=9525)
            doc.save(pdf_path)
            doc.close()
            report = convert_pdf_page(pdf_path, pptx_path)
            self.assertTrue(pptx_path.exists())
            self.assertGreater(report["native_shapes"], 0)
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

    def test_comic_sans_pdf_alias_maps_to_windows_family_name(self):
        """PDF subset names omit spaces, while Windows exposes the spaced family."""
        self.assertEqual(_source_font("ComicSansMS"), "Comic Sans MS")

    def test_anonymous_pdf_font_resource_uses_deterministic_office_fallback(self):
        """Opaque PDF resource IDs must not leak into PowerPoint font metadata."""
        self.assertEqual(_source_font("font000000002fa1185d"), "Arial")

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
