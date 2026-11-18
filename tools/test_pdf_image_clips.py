"""Real synthetic PDF regressions for local-image source clip preservation."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import fitz
from PIL import Image, ImageDraw
from pptx import Presentation
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from pdf_source_assets import collect_image_events
from pdf_figure_import import convert_pdf_page
import pdf_image_clips
from lxml import etree


def source_pdf(path, *, kind="circle", repeated=False, alpha=255, large=False, image_size=60, opacity=1):
    size = 3000 if large else 160
    c = canvas.Canvas(str(path), pagesize=(size, size))
    im = Image.new("RGBA", (image_size, image_size), (220, 30, 20, alpha))
    for i in range(2 if repeated else 1):
        c.saveState()
        p = c.beginPath()
        if large:
            p.circle(1500, 1500, 1400)
        elif kind == "outside":
            p.rect(0, 0, 10, 10)
        elif kind == "hole":
            p.circle(60, 80, 40); p.circle(60, 80, 15)
        elif kind == "triangle" or i == 1:
            p.moveTo(20, 40); p.lineTo(100, 40); p.lineTo(60, 120); p.close()
        else:
            p.circle(60, 80, 40)
        c.clipPath(p, stroke=0, fill=0, fillMode=0 if kind == "hole" else 1)
        if kind == "nested":
            second = c.beginPath(); second.rect(60, 40, 40, 80)
            c.clipPath(second, stroke=0, fill=0)
        if opacity != 1:
            c.setFillAlpha(opacity)
        c.drawImage(ImageReader(im), 0 if large else 20, 0 if large else 40,
                    size if large else 80, size if large else 80, mask="auto")
        c.restoreState()
    c.setFillColorRGB(0, 0, 1)
    c.rect(size-20, 20, 10, 10, stroke=0, fill=1)
    c.drawString(110 if not large else 2800, 140, "native")
    c.save()


def alpha_at(event, x, y):
    im = Image.open(BytesIO(event.png)).convert("RGBA")
    box = event.visible_bbox
    px = max(0, min(im.width-1, int((x-box.x0)/box.width*im.width)))
    py = max(0, min(im.height-1, int((y-box.y0)/box.height*im.height)))
    return im.getpixel((px, py))[3]


class SourceImageClipTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_same_bounds_circle_has_transparent_corners(self):
        src = self.root/"circle.pdf"; source_pdf(src)
        with fitz.open(src) as doc:
            events, stats = collect_image_events(doc[0], doc)
            self.assertEqual(stats["unresolved_visible_events"], 0)
            self.assertEqual(len(events), 1)
            self.assertEqual(alpha_at(events[0], 23, 43), 0)
            self.assertEqual(alpha_at(events[0], 60, 80), 255)

    def test_evenodd_hole_preserves_unpainted_center(self):
        src = self.root/"hole.pdf"; source_pdf(src, kind="hole")
        with fitz.open(src) as doc:
            events, stats = collect_image_events(doc[0], doc)
            self.assertEqual(stats["unresolved_visible_events"], 0)
            self.assertEqual(alpha_at(events[0], 60, 80), 0)
            self.assertEqual(alpha_at(events[0], 60, 50), 255)

    def test_same_xref_same_bounds_repeated_uses_keep_distinct_clips(self):
        src = self.root/"repeated.pdf"; source_pdf(src, repeated=True)
        with fitz.open(src) as doc:
            events, stats = collect_image_events(doc[0], doc)
            self.assertEqual(stats["unresolved_visible_events"], 0)
            self.assertEqual(len(events), 2)
            self.assertLess(events[0].seqno, events[1].seqno)
            self.assertEqual(alpha_at(events[0], 35, 70), 255)
            self.assertEqual(alpha_at(events[1], 35, 70), 0)

    def test_soft_mask_combines_with_curve_before_partial_page_crop(self):
        src = self.root/"alpha.pdf"; source_pdf(src, alpha=128)
        with fitz.open(src) as doc:
            page = doc[0]
            page.set_cropbox(fitz.Rect(40, 40, 110, 130))
            events, stats = collect_image_events(page, doc)
            self.assertEqual(stats["unresolved_visible_events"], 0)
            self.assertEqual(len(events), 1)
            self.assertEqual(alpha_at(events[0], 1, 1), 0)
            self.assertLessEqual(abs(alpha_at(events[0], 20, 40)-128), 1)
            self.assertGreaterEqual(events[0].visible_bbox.x0, 0)
            self.assertLessEqual(events[0].visible_bbox.x1, page.rect.width)

    def test_native_import_retains_vector_and_text_beside_clipped_picture(self):
        src = self.root/"native.pdf"; source_pdf(src)
        output = self.root/"native.pptx"
        report = convert_pdf_page(src, output)
        deck = Presentation(output)
        shapes = list(deck.slides[0].shapes)
        pictures = [s for s in shapes if s.shape_type == 13]
        self.assertEqual(len(pictures), 1)
        im = Image.open(BytesIO(pictures[0].image.blob)).convert("RGBA")
        self.assertEqual(im.getpixel((2, 2))[3], 0)
        self.assertTrue(any(s.has_text_frame and s.text == "native" for s in shapes))
        self.assertGreater(report["native_shapes"], 0)
        self.assertEqual(report["reconstruction_class"], "mixed_native_picture")

    def test_clip_raster_budget_fails_before_large_allocation(self):
        src = self.root/"large.pdf"; source_pdf(src, large=True)
        with fitz.open(src) as doc:
            _, stats = collect_image_events(doc[0], doc)
            self.assertGreater(stats["unresolved_visible_events"], 0)
            self.assertTrue(any("IMAGE_CLIP_PIXEL_BUDGET" in w for w in stats["warnings"]))
        with self.assertRaisesRegex(ValueError, "UNRESOLVED_SOURCE_IMAGES"):
            convert_pdf_page(src, self.root/"large.pptx")

    def test_dense_local_image_is_not_downsampled_by_clip_render(self):
        src = self.root/"dense.pdf"; source_pdf(src, image_size=1000)
        with fitz.open(src) as doc:
            events, stats = collect_image_events(doc[0], doc)
            self.assertEqual(stats["unresolved_visible_events"], 0)
            image = Image.open(BytesIO(events[0].png))
            self.assertGreaterEqual(image.width, 1000)
            self.assertGreaterEqual(image.height, 1000)

    def test_path_budget_is_checked_before_parser_allocation(self):
        # Both explicit and implicit commands can exhaust the parser's token
        # list. A post-parse exception is too late to protect this allocation.
        for path_data in ("M0 0 "+"L1 1 "*1000+"Z", "M0 0 "+"1 1 "*1000+"Z"):
            clip = etree.fromstring(('<clipPath xmlns="http://www.w3.org/2000/svg" id="c">'
                                     '<path d="'+path_data+'"/></clipPath>').encode())
            with mock.patch.object(pdf_image_clips, "MAX_CLIP_COMMANDS", 10), \
                    mock.patch.object(pdf_image_clips, "parse_path", wraps=pdf_image_clips.parse_path) as parser:
                with self.assertRaisesRegex(ValueError, "IMAGE_CLIP_PATH_BUDGET"):
                    pdf_image_clips._clip_geometry("url(#c)", pdf_image_clips.IDENTITY, {"c":clip})
                parser.assert_not_called()

    def test_nested_clip_matches_source_render_at_interior_points(self):
        src = self.root/"nested.pdf"; source_pdf(src, kind="nested")
        with fitz.open(src) as doc:
            page = doc[0]; events, stats = collect_image_events(page, doc)
            self.assertEqual(stats["unresolved_visible_events"], 0)
            reference = Image.open(BytesIO(page.get_pixmap(alpha=True, matrix=fitz.Matrix(4,4)).tobytes("png")))
            for x,y in ((62,43),(65,70),(90,80),(96,117)):
                self.assertLessEqual(abs(alpha_at(events[0],x,y)-reference.getpixel((x*4,y*4))[3]), 2)
            self.assertGreaterEqual(events[0].visible_bbox.x0, 60)

    def test_fully_clipped_image_is_not_an_extra_visible_picture(self):
        src = self.root/"outside.pdf"; source_pdf(src, kind="outside")
        with fitz.open(src) as doc:
            events, stats = collect_image_events(doc[0], doc)
            self.assertEqual(stats["unresolved_visible_events"], 0)
            self.assertEqual(events, [])

    def test_group_opacity_is_not_mistaken_for_image_soft_mask(self):
        src = self.root/"group.pdf"; source_pdf(src, opacity=.5)
        with fitz.open(src) as doc:
            events, stats = collect_image_events(doc[0], doc)
            self.assertEqual(events, [])
            self.assertEqual(stats["unresolved_visible_events"], 1)
            self.assertTrue(any("UNSUPPORTED_IMAGE_CLIP_COMPOSITING" in x for x in stats["warnings"]))
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_IMAGE_CLIP_COMPOSITING"):
            convert_pdf_page(src, self.root/"group.pptx")
        self.assertFalse((self.root/"group.pptx").exists())

    def test_multiple_clip_children_fail_closed(self):
        src = self.root/"children.pdf"; source_pdf(src)
        with fitz.open(src) as doc:
            page=doc[0]; svg=etree.fromstring(page.get_svg_image(text_as_path=False).encode())
            clip=svg.find('.//{http://www.w3.org/2000/svg}clipPath')
            etree.SubElement(clip, '{http://www.w3.org/2000/svg}path', d='M0 0L1 0L1 1Z')
            with mock.patch.object(fitz.Page, 'get_svg_image', return_value=etree.tostring(svg).decode()):
                events, stats=collect_image_events(page, doc)
            self.assertEqual(events, [])
            self.assertEqual(stats['unresolved_visible_events'], 1)
            self.assertTrue(any('UNSUPPORTED_IMAGE_CLIP_GEOMETRY' in x for x in stats['warnings']))

    def test_subpoint_image_retains_three_separate_dots_and_aspect_ratio(self):
        src=self.root/'tiny.pdf'
        im=Image.new('RGB',(111,22),'white');draw=ImageDraw.Draw(im)
        for x in (10,45,80):draw.ellipse((x,3,x+15,18),fill='black')
        c=canvas.Canvas(str(src),pagesize=(160,160))
        p=c.beginPath();p.rect(20.01,40.01,5.18,.92)
        c.clipPath(p,stroke=0,fill=0)
        c.drawImage(ImageReader(im),20,40,5.2,.94);c.save()
        with fitz.open(src) as doc:
            events,stats=collect_image_events(doc[0],doc)
        self.assertEqual(stats['unresolved_visible_events'],0)
        output=Image.open(BytesIO(events[0].png)).convert('RGBA')
        self.assertGreater(output.width,100)
        self.assertGreater(output.width/output.height,5)
        dark=[output.getpixel((x,output.height//2))[0]<100 for x in range(output.width)]
        groups=sum(value and (i==0 or not dark[i-1]) for i,value in enumerate(dark))
        self.assertEqual(groups,3)


if __name__ == "__main__":
    unittest.main()
