#!/usr/bin/env python3
"""Check that the source-derived cross-stage relation cannot silently disappear."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from scientific_ir import validate_drawn_routes  # noqa: E402

SPEC = json.loads((HERE / "GR02_graphrag_method.json").read_text(encoding="utf-8"))
FIXTURE = json.loads((HERE / "GR02_expected_topology.json").read_text(encoding="utf-8"))
REQUIRED = {tuple(pair) for pair in FIXTURE["critical_edges"]}


class GraphRAGTopologyTests(unittest.TestCase):
    def test_complete_figure_passes(self):
        self.assertEqual({tuple(pair) for pair in SPEC["semantic_edges"]}, REQUIRED)
        validate_drawn_routes(SPEC, REQUIRED)

    def test_removed_cross_stage_relation_fails(self):
        changed = copy.deepcopy(SPEC)
        changed["semantic_edges"] = [pair for pair in changed["semantic_edges"]
                                     if pair != ["community_reports", "query_reports"]]
        changed["elements"] = [item for item in changed["elements"]
                               if item.get("semantic_link") != "community_reports__query_reports"]
        # Both declarations and the visible route are removed; the independent
        # source-derived fixture must still expose the omission.
        with self.assertRaises(AssertionError):
            self.assertEqual({tuple(pair) for pair in changed["semantic_edges"]}, REQUIRED)
        with self.assertRaises(AssertionError):
            validate_drawn_routes(changed, REQUIRED)


if __name__ == "__main__":
    unittest.main()
