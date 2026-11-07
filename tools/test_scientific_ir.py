#!/usr/bin/env python3
"""Mutation checks for defects that structural SVG/PPTX audits would miss."""
from __future__ import annotations

import copy
import json
import unittest

from scientific_ir import ROOT, validate_drawn_routes, validate_expected_topology, validate_spec

SPEC = json.loads((ROOT / "figure_specs/c01/C01_composite_defense_slide.json").read_text(encoding="utf-8"))
QUANT_SPEC = json.loads((ROOT / "figure_specs/quant/Q03_iris_mean_ci.json").read_text(encoding="utf-8"))
TOPOLOGY = json.loads((ROOT / "specs/c01_expected_topology_v76.json").read_text(encoding="utf-8"))
EDGES = {tuple(edge) for edge in TOPOLOGY["critical_edges"]}


class ScientificIRMutationTests(unittest.TestCase):
    def test_baseline(self):
        validate_spec(SPEC)
        validate_expected_topology(SPEC, TOPOLOGY)

    def test_missing_visible_edge_fails(self):
        changed = copy.deepcopy(SPEC)
        changed["elements"] = [e for e in changed["elements"]
                               if e.get("semantic_link") != "gcn_1__pooling_1"]
        with self.assertRaises(AssertionError):
            validate_drawn_routes(changed, EDGES)

    def test_reversed_arrow_geometry_fails(self):
        changed = copy.deepcopy(SPEC)
        line = next(e for e in changed["elements"] if e.get("semantic_link") == "gcn_1__pooling_1")
        line["x1"], line["x2"] = line["x2"], line["x1"]
        with self.assertRaises(AssertionError):
            validate_drawn_routes(changed, EDGES)

    def test_missing_upper_panel_route_fails(self):
        changed = copy.deepcopy(SPEC)
        changed["elements"] = [e for e in changed["elements"]
                               if e.get("semantic_link") != "band_3__total_graph"]
        with self.assertRaises(AssertionError):
            validate_drawn_routes(changed, EDGES)

    def test_swapped_band_label_fails(self):
        changed = copy.deepcopy(SPEC)
        label = next(e for e in changed["elements"] if e.get("semantic_id") == "band_2" and e["type"] == "text")
        label["text"] = "B₃"
        with self.assertRaises(AssertionError):
            validate_expected_topology(changed, TOPOLOGY)

    def test_wrong_label_fails(self):
        changed = copy.deepcopy(SPEC)
        label = next(e for e in changed["elements"] if e.get("semantic_id") == "sr_ea")
        label["text"] = "EA"
        with self.assertRaises(AssertionError):
            validate_expected_topology(changed, TOPOLOGY)

    def test_missing_evidence_fails(self):
        changed = copy.deepcopy(SPEC)
        changed["elements"][0]["evidence_ref"] = "nonexistent"
        with self.assertRaises(AssertionError):
            validate_spec(changed)

    def test_changed_local_evidence_hash_fails(self):
        changed = copy.deepcopy(SPEC)
        changed["evidence_records"][0]["source_file_sha256"] = "0" * 64
        with self.assertRaises(AssertionError):
            validate_spec(changed)

    def test_missing_source_locator_fails(self):
        changed = copy.deepcopy(SPEC)
        changed["evidence_records"][0]["source_locator"] = ""
        with self.assertRaises(AssertionError):
            validate_spec(changed)

    def test_changed_chart_configuration_hash_fails(self):
        changed = copy.deepcopy(QUANT_SPEC)
        changed["data_lineage"]["chart_spec_sha256"] = "0" * 64
        with self.assertRaises(AssertionError):
            validate_spec(changed)


if __name__ == "__main__":
    unittest.main()
