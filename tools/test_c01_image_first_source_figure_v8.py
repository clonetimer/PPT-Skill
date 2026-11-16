#!/usr/bin/env python3
"""Verify C01 Image-first V8 schematic consistency and evidence boundaries."""
from __future__ import annotations

import json
import unittest

from build_c01_image_first_source_figure_v8 import build_spec
from scientific_ir import ROOT, validate_expected_topology, validate_spec


class C01ImageFirstSourceFigureV8Tests(unittest.TestCase):
    def setUp(self):
        self.spec = build_spec()
        self.elements = self.spec["elements"]

    def test_each_band_subgraph_and_total_graph_row_uses_three_node_motif(self):
        graphs = [
            e for e in self.elements
            if e.get("type") == "graph"
            and e.get("semantic_id") in {"band_1", "band_2", "band_3", "band_4", "total_graph"}
        ]
        self.assertEqual(len(graphs), 8)
        self.assertTrue(all(len(e["nodes"]) == 3 for e in graphs))
        self.assertTrue(all(len(e["edges"]) == 2 for e in graphs))

    def test_frequency_band_count_is_variable(self):
        labels = {
            e["semantic_id"]: e["text"] for e in self.elements
            if e.get("type") == "text" and e.get("semantic_id", "").startswith("band_")
        }
        self.assertEqual(labels["band_1"], "B₁")
        self.assertEqual(labels["band_2"], "B₂")
        self.assertEqual(labels["band_3"], "B₃")
        self.assertEqual(labels["band_4"], "Bₙ")
        self.assertIn("B₁, B₂, B₃, …, Bₙ", [e.get("text") for e in self.elements])

    def test_input_graph_is_twelve_nodes_four_by_three_with_eight_solid_edges(self):
        graph = next(e for e in self.elements if e.get("semantic_id") == "input_graph_schematic")
        self.assertEqual(len(graph["nodes"]), 12)
        self.assertEqual(len(graph["edges"]), 8)

    def test_dashed_links_are_schematic_not_an_asserted_exact_count(self):
        contract = self.spec["image_first_v8_contract"]
        self.assertEqual(contract["cross_band_edges"], "schematic_unspecified")
        self.assertIn("Exact number of dashed inter-band or inter-row links",
                      self.spec["figure_contract"]["unverified"])
        self.assertTrue(any(e.get("dash") for e in self.elements))

    def test_five_class_outputs_are_explicitly_illustrative_and_c2_is_orange(self):
        squares = [e for e in self.elements if e.get("semantic_role") == "illustrative_class_output"]
        self.assertEqual(len(squares), 5)
        self.assertEqual([i for i, e in enumerate(squares, start=1) if e["fill"] == "#DCA16C"], [2])
        self.assertEqual(self.spec["image_first_v8_contract"]["class_outputs"],
                         "five_output_illustrative_example")

    def test_readout_label_boundary_is_preserved(self):
        labels = [e.get("text") for e in self.elements if e.get("semantic_id") in {"sr_main", "sr_ea"}]
        self.assertEqual(labels, ["IR layer", "IR layer"])

    def test_registered_evidence_and_all_18_directed_routes_validate(self):
        validate_spec(self.spec)
        topology = json.loads(
            (ROOT / "specs/c01_composite_expected_topology_v8.json").read_text(encoding="utf-8")
        )
        validate_expected_topology(self.spec, topology)
        self.assertEqual(len(topology["critical_edges"]), 18)
        routes = {e.get("semantic_link") for e in self.elements if e.get("semantic_link")}
        self.assertIn("dense__class_output", routes)

    def test_input_container_and_label_have_distinct_semantic_ids(self):
        container = next(e for e in self.elements if e.get("semantic_id") == "input")
        label = next(e for e in self.elements if e.get("semantic_id") == "input_label")
        self.assertEqual(container["type"], "rect")
        self.assertEqual(label["text"], "Input")


if __name__ == "__main__":
    unittest.main()
