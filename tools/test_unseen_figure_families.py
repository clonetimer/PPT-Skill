"""Three synthetic cross-family PDF import fixtures; not independent-paper scores."""
from __future__ import annotations

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

import fitz
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pdf_figure_import import convert_pdf_page
from audit_imported_pdf_figure import audit_figure
from figure_first_pass_gate import source_profile, candidate_profile


def multi_panel_experiment(path: Path):
    doc = fitz.open()
    page = doc.new_page(width=720, height=360)
    for i, heading in enumerate(("(a) Ablation", "(b) Learning curve", "(c) Error bars")):
        left = 20 + i*235
        page.draw_rect(fitz.Rect(left, 35, left+218, 310), color=(.18,.23,.33), width=1)
        page.insert_text((left+13,57), heading, fontsize=12)
        page.draw_line((left+34,270),(left+194,270),color=(0,0,0),width=1)
        page.draw_line((left+34,270),(left+34,85),color=(0,0,0),width=1)
        if i == 0:
            for j, height in enumerate((65,103,141,120)):
                page.draw_rect(
                    fitz.Rect(left+44+j*37,270-height,left+70+j*37,270),
                    color=(.14,.38,.7),fill=(.76,.86,.96),width=1
                )
        elif i == 1:
            points = [(left+35+j*16,238-(j%3)*9-j*11) for j in range(10)]
            for a,b in zip(points,points[1:]):
                page.draw_line(a,b,color=(.1,.55,.45),width=2)
        else:
            for j,(yy,error) in enumerate(((175,33),(150,27),(119,20),(105,16))):
                x = left+55+j*35
                page.draw_line((x,yy-error),(x,yy+error),color=(.65,.15,.3),width=1)
                page.draw_line((x-5,yy-error),(x+5,yy-error),color=(.65,.15,.3),width=1)
                page.draw_line((x-5,yy+error),(x+5,yy+error),color=(.65,.15,.3),width=1)
                page.draw_circle((x,yy),3,color=(.65,.15,.3),fill=(.65,.15,.3))
    doc.save(path)
    doc.close()


def complex_hypergraph(path: Path):
    doc = fitz.open()
    page = doc.new_page(width=720,height=360)
    nodes = [(110,110),(180,65),(250,125),(155,180),(315,190),
             (395,90),(470,145),(540,80),(600,180),(490,245)]
    page.draw_bezier((70,160),(40,30),(250,20),(320,140),color=(.85,.32,.12),width=2)
    page.draw_bezier((320,140),(350,285),(110,295),(70,160),color=(.85,.32,.12),width=2)
    page.draw_bezier((365,140),(390,15),(655,30),(655,160),color=(.4,.25,.73),width=2)
    page.draw_bezier((655,160),(640,315),(380,290),(365,140),color=(.4,.25,.73),width=2)
    for a,b in [(0,1),(0,2),(1,2),(2,3),(2,4),(4,5),(5,6),(6,7),(6,8),(8,9),(4,9)]:
        page.draw_line(nodes[a],nodes[b],color=(.1,.3,.55),width=1)
    for i,(x,y) in enumerate(nodes):
        page.draw_circle((x,y),13,color=(.1,.2,.33),fill=(.69,.81,.94),width=1)
        page.insert_text((x-7,y+4),str(i+1),fontsize=10)
    page.insert_text((270,325),"Hyperedges + graph connectivity",fontsize=14)
    doc.save(path)
    doc.close()


def statistical_panel(path: Path):
    doc = fitz.open()
    page = doc.new_page(width=720,height=360)
    page.insert_text((30,35),"Cross-domain confidence intervals",fontsize=15)
    page.draw_line((80,300),(670,300),color=(0,0,0),width=1)
    page.draw_line((80,300),(80,65),color=(0,0,0),width=1)
    for j,(median,half,q1,q3) in enumerate(((240,56,90,140),(225,45,80,133),
                                             (187,48,112,165),(165,33,104,151))):
        x = 135+j*135
        page.draw_line((x,median-half),(x,median+half),color=(.13,.4,.73),width=2)
        page.draw_line((x-25,median-half),(x+25,median-half),color=(.13,.4,.73),width=1)
        page.draw_line((x-25,median+half),(x+25,median+half),color=(.13,.4,.73),width=1)
        page.draw_rect(fitz.Rect(x-25,q1,x+25,q3),
                       color=(.2,.3,.55),fill=(.82,.87,.96),width=1)
        page.draw_line((x-25,median),(x+25,median),color=(.8,.16,.25),width=2)
        for k in range(7):
            px = x-19+((k*31)%43)
            py = (q1+q3)/2+((k*27)%56)-25
            page.draw_circle((px,py),2,color=(.18,.36,.57),fill=(.18,.36,.57))
    page.insert_text((255,338),"Original observations + box / whiskers",fontsize=12)
    doc.save(path)
    doc.close()


BUILDERS = (multi_panel_experiment,complex_hypergraph,statistical_panel)


class IndependentGrammarFixtureTests(unittest.TestCase):
    def test_three_families_keep_source_objects(self):
        with TemporaryDirectory() as dirname:
            root = Path(dirname)
            for builder in BUILDERS:
                with self.subTest(figure_family=builder.__name__):
                    source = root/(builder.__name__+".pdf")
                    candidate = root/(builder.__name__+".pptx")
                    builder(source)
                    profile = source_profile(source)
                    convert_pdf_page(source,candidate)
                    audit = audit_figure(source,candidate)
                    self.assertEqual(audit["status"],"PASS",audit)
                    self.assertTrue(audit["checks"]["not_flattened"])
                    self.assertGreater(profile["source_drawings"],20)
                    self.assertEqual(candidate_profile(candidate)["full_page_pictures"],0)

    def test_hypergraph_retains_enclosures_and_nonraster_nodes(self):
        with TemporaryDirectory() as dirname:
            root = Path(dirname)
            source = root/"graph.pdf"
            candidate = root/"graph.pptx"
            complex_hypergraph(source)
            convert_pdf_page(source,candidate)
            shapes = Presentation(candidate).slides[0].shapes
            self.assertGreaterEqual(sum(x.shape_type==MSO_SHAPE_TYPE.FREEFORM for x in shapes),14)
            self.assertEqual(sum(x.shape_type==MSO_SHAPE_TYPE.PICTURE for x in shapes),0)


if __name__=="__main__":
    unittest.main()
