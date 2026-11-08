#!/usr/bin/env python3
"""Check source-matched topology independently of the rendered declarations."""
from __future__ import annotations
import copy
import json
import sys
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/"tools"))
from scientific_ir import validate_drawn_routes  # noqa: E402

TOPO=json.loads((HERE/"source_matched_topology.json").read_text(encoding="utf-8"))
STYLE=json.loads((HERE/"source_style.json").read_text(encoding="utf-8"))

class SourceMatchedTests(unittest.TestCase):
    def test_source_style_anchors(self):
        self.assertEqual(len(STYLE["anchors"]),7)
        self.assertTrue(all(a["evidence"] and a["observation"] and a["decision"] for a in STYLE["anchors"]))
    def test_both_figures(self):
        for name,edges in TOPO.items():
            with self.subTest(name=name):
                spec=json.loads((HERE/(name+".json")).read_text(encoding="utf-8"))
                expected={tuple(e) for e in edges}
                self.assertEqual({tuple(e) for e in spec["semantic_edges"]},expected)
                validate_drawn_routes(spec,expected)
    def test_v_bypass_omission_fails(self):
        name="TR04_transformer_attention_source_matched"
        spec=json.loads((HERE/(name+".json")).read_text(encoding="utf-8"))
        expected={tuple(e) for e in TOPO[name]}
        changed=copy.deepcopy(spec)
        changed["semantic_edges"].remove(["v","context"])
        changed["elements"]=[e for e in changed["elements"] if e.get("semantic_link")!="v__context"]
        with self.assertRaises(AssertionError):validate_drawn_routes(changed,expected)
    def test_encoder_cross_attention_omission_fails(self):
        name="TR03_transformer_architecture_source_matched"
        spec=json.loads((HERE/(name+".json")).read_text(encoding="utf-8"))
        expected={tuple(e) for e in TOPO[name]}
        changed=copy.deepcopy(spec)
        changed["semantic_edges"].remove(["enc_norm2","dec_cross"])
        changed["elements"]=[e for e in changed["elements"] if e.get("semantic_link")!="enc_norm2__dec_cross"]
        with self.assertRaises(AssertionError):validate_drawn_routes(changed,expected)

if __name__=="__main__":unittest.main()
