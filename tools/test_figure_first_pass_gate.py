"""Frozen first-attempt probes across unfamiliar figure families.

No geometry is fitted to a specific cited paper. Negative examples test false
PASS cases, including localized chart loss and raster-only sources.
"""
from __future__ import annotations

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

import fitz
from PIL import Image
from pptx import Presentation
from pptx.util import Pt
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pdf_ellipse_recognition import ellipse_bounds
from figure_first_pass_gate import (
    candidate_profile, compare_rendered_pages, source_profile
)


class FirstPassFidelityTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_native_ellipse_recognition_is_strict(self):
        pdf = self.root / "unseen_polar_panel.pdf"
        c = canvas.Canvas(str(pdf), pagesize=(360,240))
        c.circle(130,115,48,stroke=1,fill=0)
        c.ellipse(180,38,270,78,stroke=1,fill=0)
        c.showPage(); c.save()
        with fitz.open(pdf) as f:
            paths=f[0].get_drawings()
            self.assertEqual(len(paths), 2)
            self.assertTrue(all(ellipse_bounds(p) is not None for p in paths))
        self.assertEqual(source_profile(pdf)["recognizable_source_ellipses"], 2)

    def test_nonellipse_four_bezier_loop_does_not_invent_circle(self):
        pdf=self.root/"unseen_hyperedge.pdf"
        d=fitz.open(); p=d.new_page(width=320,height=200)
        s=p.new_shape()
        s.draw_bezier((40,80),(50,10),(130,20),(180,70))
        s.draw_bezier((180,70),(245,65),(260,105),(200,140))
        s.draw_bezier((200,140),(160,185),(80,160),(50,135))
        s.draw_bezier((50,135),(20,120),(15,95),(40,80))
        s.finish(color=(0,.2,.6),width=1,closePath=True)
        s.commit(); d.save(pdf); d.close()
        with fitz.open(pdf) as f:
            self.assertIsNone(ellipse_bounds(f[0].get_drawings()[0]))

    def test_source_preflight_flags_clipping_and_extreme_stroke(self):
        pdf=self.root/"unseen_clipped_plot.pdf"
        c=canvas.Canvas(str(pdf),pagesize=(320,180))
        c.setLineWidth(2)
        clip=c.beginPath(); clip.rect(50,35,75,75)
        c.clipPath(clip,stroke=0,fill=0)
        c.line(0,0,300,140)
        c.showPage(); c.save()
        p=source_profile(pdf)
        self.assertTrue(any(r["code"]=="CLIPPED_PLOTS" for r in p["risk_flags"]))
        pdf2=self.root/"unseen_stroke.pdf"
        d=fitz.open(); pg=d.new_page(width=200,height=150)
        pg.draw_line((20,70),(170,70),color=(.2,.2,.8),width=9000)
        d.save(pdf2); d.close()
        p=source_profile(pdf2)
        self.assertTrue(any(r["code"]=="UNREPRESENTABLE_STROKE" for r in p["risk_flags"]))

    def test_raster_only_source_is_explicitly_flagged(self):
        pdf=self.root/"unseen_image_only.pdf"
        d=fitz.open(); page=d.new_page(width=200,height=100)
        import io
        b=io.BytesIO()
        Image.new("RGB",(12,12),(100,170,220)).save(b,format="PNG")
        page.insert_image(fitz.Rect(0,0,200,100),stream=b.getvalue())
        d.save(pdf); d.close()
        p=source_profile(pdf)
        self.assertTrue(any(r["code"]=="RASTER_ONLY" for r in p["risk_flags"]))

    def test_visual_gate_finds_localized_missing_chart_panel(self):
        pdf=self.root/"source.pdf"
        d=fitz.open(); page=d.new_page(width=480,height=270)
        page.draw_rect(fitz.Rect(10,10,225,245),fill=(.9,.9,.95))
        for i in range(16):
            page.draw_line((20,30+12*i),(210,210-11*i),color=(.1,.25,.7),width=.9)
        page.draw_rect(fitz.Rect(260,20,465,245),fill=(.7,.82,.95))
        d.save(pdf); d.close()
        perfect=compare_rendered_pages(pdf,pdf,dpi=72,grid=4)
        self.assertGreater(perfect["global_similarity"],.99)
        self.assertFalse(perfect["requires_visual_review"])
        damaged=self.root/"altered.pdf"
        d=fitz.open(pdf); page=d[0]
        page.draw_rect(fitz.Rect(245,0,480,270),color=(1,1,1),fill=(1,1,1))
        d.save(damaged); d.close()
        diff=compare_rendered_pages(pdf,damaged,dpi=72,grid=4,preview=self.root/"diff.png")
        self.assertTrue(diff["requires_visual_review"])
        self.assertLess(diff["global_similarity"],.88)
        self.assertTrue((self.root/"diff.png").exists())

    def test_candidate_counts_native_ellipse_as_vector_not_picture(self):
        ppt=self.root/"native.pptx"
        d=Presentation(); sl=d.slides.add_slide(d.slide_layouts[6])
        from pptx.enum.shapes import MSO_SHAPE
        sl.shapes.add_shape(MSO_SHAPE.OVAL,Pt(50),Pt(50),Pt(120),Pt(120))
        box=sl.shapes.add_textbox(Pt(5),Pt(5),Pt(200),Pt(30))
        box.text="first pass"
        d.save(ppt)
        p=candidate_profile(ppt)
        self.assertEqual(p["native_vectors"],1)
        self.assertEqual(p["picture_objects"],0)
        self.assertEqual(p["text_objects"],1)

    def test_gate_reports_source_without_faking_host_certification(self):
        p=self.root/"lowrisk.pdf"
        d=fitz.open(); pg=d.new_page(width=200,height=100)
        pg.draw_rect(fitz.Rect(20,20,120,80),color=(.2,.3,.4),width=1)
        d.save(p); d.close()
        profile=source_profile(p)
        self.assertTrue(profile["requires_human_scientific_review"])
        self.assertFalse(profile["risk_flags"])
        self.assertEqual(len(profile["sha256"]),64)

    def test_holdout_import_if_pipeline_is_present(self):
        try:
            from pdf_figure_import import convert_pdf_page
            from audit_imported_pdf_figure import audit_figure
        except ImportError:
            self.skipTest("integration imports available only inside PPT-Skill repository")
        src=self.root/"holdout.pdf"; out=self.root/"holdout.pptx"
        c=canvas.Canvas(str(src),pagesize=(380,240))
        c.setLineWidth(.6)
        c.circle(80,120,34,stroke=1,fill=0)
        c.rect(165,85,110,70,stroke=1,fill=0)
        c.line(114,120,165,120)
        c.drawString(180,122,"Cache Agent")
        c.showPage(); c.save()
        convert_pdf_page(src,out)
        audit=audit_figure(src,out)
        self.assertEqual(audit["status"],"PASS")
        deck=Presentation(out)
        self.assertGreater(sum(s.shape_type==1 for s in deck.slides[0].shapes),0)


if __name__=="__main__":
    unittest.main()
