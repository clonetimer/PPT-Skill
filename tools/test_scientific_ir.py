#!/usr/bin/env python3
"""Mutation checks for defects that structural SVG/PPTX audits would miss."""
from __future__ import annotations

import copy
import json
import unittest

import jsonschema

from scientific_ir import ROOT, validate_drawn_routes, validate_expected_topology, validate_spec

SPEC = json.loads((ROOT / "figure_specs/c01/C01_composite_defense_slide.json").read_text(encoding="utf-8"))
STANDALONE = json.loads((ROOT / "figure_specs/c01/C01_SEANet_graph_level.json").read_text(encoding="utf-8"))
QUANT_SPEC = json.loads((ROOT / "figure_specs/quant/Q03_iris_mean_ci.json").read_text(encoding="utf-8"))
SCHEMA = json.loads((ROOT / "specs/figure_spec_v76.schema.json").read_text(encoding="utf-8"))
TOPOLOGY = json.loads((ROOT / "specs/c01_expected_topology_v76.json").read_text(encoding="utf-8"))
STANDALONE_TOPOLOGY = json.loads((ROOT / "specs/c01_standalone_expected_topology_v76.json").read_text(encoding="utf-8"))
EDGES = {tuple(edge) for edge in TOPOLOGY["critical_edges"]}


class ScientificIRMutationTests(unittest.TestCase):
    def test_baseline(self):
        validate_spec(SPEC)
        validate_expected_topology(SPEC, TOPOLOGY)
        validate_spec(STANDALONE)
        validate_expected_topology(STANDALONE, STANDALONE_TOPOLOGY)

    def test_empty_method_topology_rejected(self):
        empty={"figure_id":SPEC["id"],"required_nodes":[],"required_edges":[]}
        with self.assertRaisesRegex(AssertionError,"critical routes"):
            validate_expected_topology(SPEC,empty)

    def test_standalone_wrong_ea_shortcut_fails(self):
        changed = copy.deepcopy(STANDALONE)
        line = next(e for e in changed["elements"] if e.get("semantic_link") == "ea__gcn_1")
        line["semantic_link"] = "ea__sr_aux"
        with self.assertRaises(AssertionError):
            validate_expected_topology(changed, STANDALONE_TOPOLOGY)

    def test_standalone_missing_dense_route_fails(self):
        changed = copy.deepcopy(STANDALONE)
        changed["elements"] = [e for e in changed["elements"]
                               if e.get("semantic_link") != "sum__dense"]
        with self.assertRaises(AssertionError):
            validate_expected_topology(changed, STANDALONE_TOPOLOGY)

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

    def test_missing_total_graph_to_network_input_fails(self):
        changed = copy.deepcopy(SPEC)
        changed["elements"] = [e for e in changed["elements"]
                               if e.get("semantic_link") != "total_graph__input"]
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

    def test_embedded_chart_drift_fails(self):
        changed = copy.deepcopy(QUANT_SPEC)
        changed["chart_contract"]["statistics"]["resamples"] += 1
        with self.assertRaises(AssertionError):
            validate_spec(changed)

    def test_chart_source_mismatch_fails(self):
        changed = copy.deepcopy(QUANT_SPEC)
        changed["data_lineage"]["row_count"] -= 1
        with self.assertRaises(AssertionError):
            validate_spec(changed)

    def test_schema_requires_quantitative_lineage(self):
        changed = copy.deepcopy(QUANT_SPEC)
        changed["data_lineage"].pop("chart_spec_sha256")
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(changed, SCHEMA)


if __name__ == "__main__":
    unittest.main()
