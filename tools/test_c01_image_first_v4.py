#!/usr/bin/env python3
"""Scientific fidelity regression for C01 Image-first V4 after editorial Major Revision."""
from __future__ import annotations

import json
import unittest

from scientific_ir import ROOT, validate_expected_topology, validate_spec
from build_image2_slide_prompt import build_prompt, load_slide
from image_first_source_contract import load_source_figure_contract


FIGURE = ROOT / "figure_specs/c01/C01_composite_defense_slide_image_first_v4.json"
TOPOLOGY = ROOT / "specs/c01_composite_expected_topology_v4.json"


class C01ImageFirstV4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads(FIGURE.read_text(encoding="utf-8"))
        cls.topology = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
        cls.elements = cls.spec["elements"]
        cls.by_id = {e["id"]: e for e in cls.elements}

    def test_source_evidence_and_all_method_level_routes(self):
        validate_spec(self.spec)
        validate_expected_topology(self.spec, self.topology)
        self.assertEqual(len(self.topology["critical_edges"]), 18)
        self.assertEqual(len(self.elements), len(self.by_id))

    def test_fusion_operator_is_author_visible_plus_not_sigma(self):
        self.assertEqual(self.topology["critical_labels"]["sum"], "+")
        fusion = next(e for e in self.elements if e.get("semantic_id") == "sum")
        self.assertEqual(fusion["text"], "+")
        self.assertFalse(any(e.get("text") == "Σ" for e in self.elements))
        self.assertEqual(self.topology["geometry_contract"]["fusion"]["symbol"], "+")

    def test_variable_sensor_dimension_M_is_explicit(self):
        expected = {
            "sensor_1": "Sensor #1",
            "sensor_2": "Sensor #2",
            "sensor_m_minus_1": "Sensor #M−1",
            "sensor_m": "Sensor #M",
        }
        for semantic_id, label in expected.items():
            self.assertEqual(
                next(e["text"] for e in self.elements if e.get("semantic_id") == semantic_id),
                label,
            )
        self.assertTrue(self.topology["geometry_contract"]["sensor_count"]["variable"])
        self.assertIn("M variable", self.by_id["el_0200"]["text"])

    def test_variable_band_N_and_schematic_graphs(self):
        bands = [
            e for e in self.elements if e.get("type") == "graph"
            and e.get("semantic_id") in {"band_1","band_2","band_3","band_4","total_graph"}
        ]
        self.assertEqual(len(bands), 8)
        self.assertTrue(all(len(e["nodes"]) == 3 for e in bands))
        self.assertEqual(self.topology["geometry_contract"]["band_count"]["symbol"], "N")
        self.assertTrue(self.topology["geometry_contract"]["band_count"]["variable"])
        self.assertEqual(self.spec["image_first_v8_contract"]["inter_band_example"],
                         "dashed_schematic_only")

    def test_one_explicit_cross_band_example_and_legend_without_edge_count_claim(self):
        self.assertTrue(self.by_id["el_0208"]["dash"])
        self.assertEqual(self.by_id["el_0208"]["semantic_id"], "inter_band_example")
        self.assertEqual(self.by_id["el_0206"]["text"], "intra-band")
        self.assertEqual(self.by_id["el_0207"]["text"], "inter-band (schematic)")
        self.assertTrue(self.topology["geometry_contract"]["inter_band_legend"]["exact_edge_count_asserted"] is False)

    def test_ocf_before_after_is_illustrative_not_measured(self):
        self.assertEqual(self.by_id["el_0048"]["text"], "Before")
        self.assertEqual(self.by_id["el_0049"]["text"], "After (illustrative)")
        self.assertEqual(self.by_id["el_0201"]["type"], "polyline")
        self.assertEqual(self.by_id["el_0202"]["type"], "polyline")
        self.assertTrue(self.topology["geometry_contract"]["ocf_signal_example"]["not_measured"])

    def test_total_graph_to_input_routes_outside_lower_heading(self):
        outer = self.by_id["el_0063"]
        self.assertLess(outer["x1"], 0.42)
        self.assertAlmostEqual(outer["x1"], outer["x2"])
        self.assertEqual(self.by_id["el_0064"]["x1"], outer["x1"])
        self.assertEqual(self.by_id["el_0005"]["text"], "01  Frequency-band graph construction")
        self.assertEqual(self.by_id["el_0065"]["text"], "02  Graph-level fault diagnosis")

    def test_main_and_energy_assist_branches_and_output_boundary(self):
        edges = set(map(tuple, self.spec["semantic_edges"]))
        self.assertIn(("input","ea"), edges)
        self.assertIn(("ea","gcn_1"), edges)
        self.assertIn(("pooling_1","sr_ea"), edges)
        self.assertIn(("sr_main","sum"), edges)
        self.assertIn(("sr_ea","sum"), edges)
        self.assertIn(("sum","dense"), edges)
        squares = [
            e for e in self.elements
            if e.get("semantic_role") == "illustrative_class_output"
        ]
        self.assertEqual(len(squares), 5)
        self.assertEqual(
            [i for i, e in enumerate(squares,1) if e["fill"] == "#DCA16C"], [2]
        )
        readouts = [
            e["text"] for e in self.elements if e.get("semantic_id") in {"sr_main","sr_ea"}
        ]
        self.assertEqual(readouts, ["IR layer","IR layer"])

    def test_image2_prompt_includes_hard_symbol_sensor_and_legend_constraints(self):
        deck, slide = load_slide(ROOT / "specs/deck_spec_v8_v4.example.json", "s02")
        source = load_source_figure_contract(ROOT, slide)
        prompt = build_prompt(deck, slide, source_figure=source)
        self.assertIn("Sensor dimension M is variable", prompt)
        self.assertIn("Sensor #M−1", prompt)
        self.assertIn("circular + operator", prompt)
        self.assertIn("NEVER replace it with the Greek Sigma (Σ)", prompt)
        self.assertIn("distinct Before and After waveform sketches", prompt)
        self.assertIn("dashed line = inter-band connection", prompt)
        self.assertIn("left outer whitespace gutter", prompt)

    def test_review_status_remains_unapproved(self):
        self.assertIn("pending", self.spec["evidence_status"])
        self.assertIn("IR/SR terminology equivalence", " ".join(self.spec["figure_contract"]["unverified"]))


if __name__ == "__main__":
    unittest.main()
