#!/usr/bin/env python3
"""Regression mutations derived from Trials 01, 04-08, 13-15, 17-20.
Synthetic source and synthetic marks test enforcement, not expert visual quality.
"""
import copy
import tempfile
import unittest
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.util import Inches, Pt
from pptx.oxml.xmlchemy import OxmlElement

from academic_delivery_gate import (GateError, RULES, finalize, load, prepare,
                                    save, sha, verify_mapping, audit_render)


class DeliveryGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.pptx = cls.root/"draft.pptx"
        cls.contract = cls.root/"source.json"
        cls.mapping = cls.root/"mapping.json"
        cls.review_dir = cls.root/"review"
        deck = Presentation()
        deck.slide_width, deck.slide_height = Inches(12), Inches(6)
        slide = deck.slides.add_slide(deck.slide_layouts[6])
        def box(kind, x, y, w, h, label):
            s = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
            s.text = label
            for p in s.text_frame.paragraphs:
                for r in p.runs:
                    r.font.name = "DejaVu Sans"
                    r.font.size = Pt(24)
            return s
        a = box(MSO_SHAPE.TRAPEZOID, 1, 1, 2, 1, "Conv1D")
        b = box(MSO_SHAPE.RECTANGLE, 1, 4, 2, 1, "Gate")
        j = box(MSO_SHAPE.OVAL, 6, 2.5, 1, 1, "+")
        def line(x1,y1,x2,y2):
            s = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1),
                                           Inches(x2), Inches(y2))
            ln = s._element.spPr.get_or_add_ln()
            arrow = OxmlElement("a:tailEnd"); arrow.set("type", "triangle"); ln.append(arrow)
            return s
        l1 = line(3,1.5,6,2.75)
        l2 = line(3,4.5,6,3.25)
        deck.save(cls.pptx)
        # A rendered synthetic reference is source evidence for this fixture only.
        # It is not claimed to be a published figure.
        (cls.root/"reference.txt").write_text("Synthetic source: two inputs sum, distinct ports.", encoding="utf-8")
        (cls.root/"figure.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="120" height="60"><path d="M30 15L60 28 M30 45L60 33"/></svg>',
            encoding="utf-8")
        cls.c = {"version": 1, "claim": "Synthetic fixture only", "mode": "source_matched",
                 "placement": {"profile": "presentation", "width_in": 12, "height_in": 6},
                 "evidence": [{"id":"p","kind":"user_spec","path":"reference.txt","locator":"line 1",
                               "sha256":sha(cls.root/"reference.txt")},
                              {"id":"v","kind":"visual_reference","path":"figure.svg","locator":"whole diagram",
                               "sha256":sha(cls.root/"figure.svg")}],
                 "marks": [], "relations": []}
        cls.m = {"marks": {}, "relations": {}, "assets": {}}
        for key, s, form, kind, label in (
                ("a",a,"encoder","AUTO_SHAPE:TRAPEZOID","Conv1D"),
                ("b",b,"feature","AUTO_SHAPE:RECTANGLE","Gate"),
                ("j",j,"sum","AUTO_SHAPE:OVAL","+")):
            entry = {"id":key,"form":form,"native_kinds":[kind],"labels":[label],
                     "core":True,"evidence":"p","locator":"line 1","meaning":form}
            binding = {"form":form,"shape_ids":[s.shape_id]}
            if key == "j":
                entry.update(operator="add",operands=["e1","e2"])
                binding.update(operator="add",operands=["e1","e2"])
            cls.c["marks"].append(entry)
            cls.m["marks"][key] = binding
        for key, source, port, shape in (("e1","a","upper",l1),("e2","b","lower",l2)):
            e = {"id":key,"source":source,"target":"j","role":"data","target_port":port,
                 "directed":True,"meaning":"operand","evidence":"p","locator":"line 1"}
            cls.c["relations"].append(e)
            cls.m["relations"][key] = {**e,"shape_ids":[shape.shape_id]}
        save(cls.contract, cls.c); save(cls.mapping, cls.m)
        cls.receipt = prepare(cls.pptx, cls.contract, cls.mapping, cls.review_dir)
        cls.review = cls.root/"checked.json"
        save(cls.review, {"receipt_sha256":sha(cls.review_dir/"receipt.json"),
             "reviewer_role":"author_agent",
             "checks": {r:{"status":"pass","locator":"synthetic fixture",
                           "observation":"Fixture-only expected result; no scientific acceptance claim."}
                        for r in RULES}})

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def mutate(self, c=None, m=None):
        contract, mapping = self.root/"mutated_source.json", self.root/"mutated_mapping.json"
        save(contract, self.c if c is None else c)
        save(mapping, self.m if m is None else m)
        return contract, mapping

    def test_positive_real_render_and_candidate(self):
        self.assertTrue(self.receipt["render_audit"]["passed"], self.receipt["render_audit"]["errors"])
        destination = self.root/"candidate.pptx"
        result = finalize(self.pptx,self.contract,self.mapping,self.review_dir,self.review,destination)
        self.assertEqual(result["status"], "reviewed_candidate")
        self.assertFalse(result["user_accepted"])
        self.assertEqual(sha(destination),sha(self.pptx))

    def test_missing_layer(self):
        m = copy.deepcopy(self.m); del m["marks"]["a"]
        with self.assertRaisesRegex(GateError,"inventory mismatch"):
            verify_mapping(self.pptx,*self.mutate(m=m))

    def test_required_label_not_present(self):
        c = copy.deepcopy(self.c); c["marks"][0]["labels"] = ["Conv1D, k=3"]
        with self.assertRaisesRegex(GateError,"required visible label"):
            verify_mapping(self.pptx,*self.mutate(c=c))

    def test_generic_box_instead_of_encoder(self):
        m = copy.deepcopy(self.m); m["marks"]["a"]["shape_ids"] = m["marks"]["b"]["shape_ids"]
        with self.assertRaisesRegex(GateError,"required geometry"):
            verify_mapping(self.pptx,*self.mutate(m=m))

    def test_wrong_aggregation(self):
        m = copy.deepcopy(self.m); m["marks"]["j"]["operator"] = "concat"
        with self.assertRaisesRegex(GateError,"aggregation"):
            verify_mapping(self.pptx,*self.mutate(m=m))

    def test_missing_edge_and_swapped_port(self):
        m = copy.deepcopy(self.m); del m["relations"]["e1"]
        with self.assertRaisesRegex(GateError,"inventory mismatch"):
            verify_mapping(self.pptx,*self.mutate(m=m))
        m = copy.deepcopy(self.m); m["relations"]["e1"]["target_port"] = "lower"
        with self.assertRaisesRegex(GateError,"role/port"):
            verify_mapping(self.pptx,*self.mutate(m=m))

    def test_wrong_endpoint_geometry(self):
        m = copy.deepcopy(self.m)
        m["relations"]["e1"]["shape_ids"] = m["relations"]["e2"]["shape_ids"]
        with self.assertRaisesRegex(GateError,"misses source"):
            verify_mapping(self.pptx,*self.mutate(m=m))

    def test_missing_arrow(self):
        deck = Presentation(self.pptx)
        sid = self.m["relations"]["e1"]["shape_ids"][0]
        for s in deck.slides[0].shapes:
            if s.shape_id == sid:
                ln = s._element.spPr.get_or_add_ln()
                for arrow in list(ln):
                    if arrow.tag.endswith("tailEnd"):
                        ln.remove(arrow)
        path = self.root/"missing_arrow.pptx"; deck.save(path)
        with self.assertRaisesRegex(GateError,"missing directed arrow"):
            verify_mapping(path,self.contract,self.mapping)

    def test_final_placement_shrink_fails_even_with_large_nominal_font(self):
        c = copy.deepcopy(self.c); c["placement"]["width_in"]=3; c["placement"]["height_in"]=1.5
        report = audit_render(self.pptx,self.review_dir/"render.pdf",c)
        self.assertFalse(report["passed"])
        self.assertTrue(any("undersize" in e for e in report["errors"]))

    def test_real_render_overlap_blocks(self):
        deck = Presentation(self.pptx); slide = deck.slides[0]
        for i, text in enumerate(("First layer", "Second layer")):
            s=slide.shapes.add_textbox(Inches(8),Inches(2+i*.03),Inches(3),Inches(.6))
            s.text=text
            s.text_frame.paragraphs[0].runs[0].font.size=Pt(24)
        path=self.root/"overlap.pptx"; deck.save(path)
        r=prepare(path,self.contract,self.mapping,self.root/"overlap_review")
        self.assertEqual(r["status"],"blocked")
        self.assertTrue(any("intersection" in e for e in r["render_audit"]["errors"]))

    def test_source_changed(self):
        c = copy.deepcopy(self.c); c["evidence"][0]["sha256"] = "0"*64
        with self.assertRaisesRegex(GateError,"changed source"):
            verify_mapping(self.pptx,*self.mutate(c=c))

    def test_stale_review_and_unreviewed_rule(self):
        for change in ("stale","pending"):
            review=load(self.review)
            if change=="stale": review["receipt_sha256"]="0"*64
            else: review["checks"]["R04"]["status"]="pending"
            path=self.root/(change+".json"); save(path,review)
            destination=self.root/(change+".pptx")
            with self.assertRaises(GateError):
                finalize(self.pptx,self.contract,self.mapping,self.review_dir,path,destination)
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
