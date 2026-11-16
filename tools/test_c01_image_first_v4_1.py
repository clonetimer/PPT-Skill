#!/usr/bin/env python3
"""Regression suite for C01 Image-first V4.1 after Minor Revision."""
from __future__ import annotations

import json
import unittest

from scientific_ir import ROOT, validate_expected_topology, validate_spec
from build_image2_slide_prompt import build_prompt, load_slide
from image_first_source_contract import load_source_figure_contract

FIGURE = ROOT / "figure_specs/c01/C01_composite_defense_slide_image_first_v4_1.json"
TOPOLOGY = ROOT / "specs/c01_composite_expected_topology_v4_1.json"
DECK = ROOT / "specs/deck_spec_v8_v4_1.example.json"


class C01ImageFirstV41Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads(FIGURE.read_text(encoding="utf-8"))
        cls.topology = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
        cls.deck = json.loads(DECK.read_text(encoding="utf-8"))
        cls.slide = next(s for s in cls.deck["slides"] if s["id"] == "s02")
        cls.elements = cls.spec["elements"]
        cls.by_id = {e["id"]: e for e in cls.elements}

    def test_registered_evidence_and_all_18_method_routes(self):
        validate_spec(self.spec)
        validate_expected_topology(self.spec, self.topology)
        self.assertEqual(len(self.topology["critical_edges"]), 18)
        self.assertEqual(len(self.elements), len(self.by_id))

    def test_BN_notation_is_consistent_and_uppercase(self):
        labels = [e.get("text", "") for e in self.elements if e["type"] == "text"]
        self.assertIn("B_N", labels)
        self.assertIn("B₁, B₂, B₃, …, B_N", labels)
        self.assertFalse(any("Bₙ" in label for label in labels))
        self.assertEqual(self.topology["critical_labels"]["band_4"], "B_N")
        self.assertEqual(self.topology["geometry_contract"]["band_count"]["index_notation"], "B_N")

    def test_author_source_says_Nth_subgraph_and_BN_is_redraw_normalization(self):
        note = self.topology["geometry_contract"]["total_graph"]["note"]
        self.assertIn("B_N", note)
        self.assertIn("Nth", self.topology["evidence_boundary"][0] + " " + " ".join(self.topology["evidence_boundary"]))
        self.assertIn("not a claim that the source figure prints the literal string B_N", self.spec["figure_contract"]["evidence_scope"])

    def test_filtering_and_graph_construction_are_separate_stages(self):
        visible = self.slide["on_slide"]
        self.assertIn("Filtering: obtain signals in each frequency band.", visible)
        self.assertIn(
            "Graph construction: build one subgraph per band, then connect the subgraphs into the total graph.",
            visible,
        )
        self.assertNotIn("Band-pass filters form frequency-band subgraphs", visible)

    def test_continuation_marker_is_positioned_between_B3_and_BN(self):
        b3 = next(e for e in self.elements if e.get("id") == "el_0037")
        bn = next(e for e in self.elements if e.get("id") == "el_0045")
        gap_top = b3["y"] + b3["h"]
        gap_bottom = bn["y"]
        upper = self.by_id["el_0209"]
        ellipsis = self.by_id["el_0210"]
        lower = self.by_id["el_0211"]
        self.assertLessEqual(gap_top - 0.04, upper["y1"])
        self.assertLessEqual(upper["y2"], gap_bottom)
        self.assertGreaterEqual(ellipsis["y"], gap_top - 0.01)
        self.assertLessEqual(ellipsis["y"] + ellipsis["h"], gap_bottom + 0.01)
        self.assertGreaterEqual(lower["y1"], gap_top)
        self.assertLessEqual(lower["y2"], gap_bottom + 0.04)
        self.assertTrue(all(rail["x1"] == rail["x2"] for rail in (upper, lower)))
        self.assertTrue(all("semantic_link" not in rail for rail in (upper, lower)))
        self.assertNotIn(("band_3", "band_4"), set(map(tuple, self.spec["semantic_edges"])))

    def test_total_graph_has_one_example_edge_and_non_attached_continuation(self):
        examples = [e for e in self.elements if e.get("semantic_id") == "inter_band_example"]
        rails = [e for e in self.elements if e.get("semantic_id", "").startswith("inter_band_continuation_rail_")]
        ellipses = [e for e in self.elements if e.get("semantic_id") == "inter_band_continuation_ellipsis"]
        self.assertEqual(len(examples), 1)
        self.assertTrue(examples[0]["dash"])
        self.assertEqual(len(rails), 2)
        self.assertEqual(len(ellipses), 1)
        self.assertTrue(all(e["x1"] == e["x2"] for e in rails))
        self.assertTrue(all("semantic_link" not in e for e in rails))
        self.assertIn("no node endpoints", self.topology["geometry_contract"]["total_graph"]["continuation_marker"])
        self.assertNotIn(("band_3", "band_4"), set(map(tuple, self.spec["semantic_edges"])))

    def test_M_sensor_labels_and_variable_dimension_are_preserved(self):
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

    def test_author_visible_fusion_operator_is_plus(self):
        fusion = next(e for e in self.elements if e.get("semantic_id") == "sum")
        self.assertEqual(fusion["text"], "+")
        self.assertEqual(self.topology["critical_labels"]["sum"], "+")
        self.assertFalse(any(e.get("text") == "Σ" for e in self.elements))

    def test_class_outputs_are_near_square_and_labelled(self):
        outputs = [e for e in self.elements if e.get("semantic_role") == "illustrative_class_output"]
        self.assertEqual(len(outputs), 5)
        self.assertTrue(all(abs(e["w"] - e["h"]) < 1e-9 for e in outputs))
        self.assertEqual(
            [i for i, e in enumerate(outputs, 1) if e["fill"] == "#DCA16C"], [2]
        )
        label = next(e for e in self.elements if e.get("semantic_id") == "class_output_label")
        self.assertEqual(label["text"], "Fault classification")
        self.assertEqual(self.topology["critical_labels"]["class_output_label"], "Fault classification")

    def test_IR_SR_difference_is_disclosed_once(self):
        visible = self.slide["on_slide"]
        notes = [x for x in visible if "published abstract: SR" in x]
        self.assertEqual(len(notes), 1)
        self.assertIn("single note", self.topology["geometry_contract"]["readout_note_placement"])
        evidence_text = next(e["text"] for e in self.elements if e.get("id") == "el_0117")
        self.assertEqual(evidence_text.count("published abstract: SR"), 1)

    def test_OCF_before_after_is_illustrative_not_measured(self):
        self.assertEqual(self.by_id["el_0048"]["text"], "Before")
        self.assertEqual(self.by_id["el_0049"]["text"], "After (illustrative)")
        self.assertTrue(self.topology["geometry_contract"]["ocf_signal_example"]["not_measured"])

    def test_outer_left_total_graph_to_input_route_and_panel_titles(self):
        outer = self.by_id["el_0063"]
        self.assertLess(outer["x1"], 0.42)
        self.assertAlmostEqual(outer["x1"], outer["x2"])
        self.assertEqual(self.by_id["el_0005"]["text"], "01  Frequency-band graph construction")
        self.assertEqual(self.by_id["el_0065"]["text"], "02  Graph-level fault diagnosis")

    def test_Image2_prompt_hardens_all_four_minor_revision_items(self):
        deck, slide = load_slide(DECK, "s02")
        source = load_source_figure_contract(ROOT, slide)
        prompt = build_prompt(deck, slide, source_figure=source)
        self.assertIn("B_N", prompt)
        self.assertIn("must not depict a specific B₃-to-B_N edge", prompt)
        self.assertIn("Band-pass filtering yields signals in each frequency band", prompt)
        self.assertIn("Fault classification", prompt)
        self.assertIn("Input graph: show 12 nodes in 4 rows of 3 nodes", prompt)
        self.assertNotIn("None rows", prompt)
        self.assertIn("exactly once in the Evidence boundary panel", prompt)
        self.assertIn("Do not add a second GCN₁ to the auxiliary branch", prompt)
        self.assertIn("lower IR readout branch leaves the output of pooling₁", prompt)

    def test_stage_A_is_not_approved_and_stage_B_is_not_started(self):
        self.assertIn("pending", self.spec["evidence_status"])
        self.assertEqual(self.slide["role"], "method")


if __name__ == "__main__":
    unittest.main()
