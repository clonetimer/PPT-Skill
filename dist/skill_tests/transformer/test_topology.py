#!/usr/bin/env python3
"""Independent source-topology checks and meaningful omission mutations."""
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

TOPO = json.loads((HERE / "expected_topology.json").read_text(encoding="utf-8"))


class TransformerTopologyTests(unittest.TestCase):
    def check(self, name, key):
        spec = json.loads((HERE / f"{name}.json").read_text(encoding="utf-8"))
        expected = {tuple(e) for e in TOPO[key]}
        self.assertEqual({tuple(e) for e in spec["semantic_edges"]}, expected)
        validate_drawn_routes(spec, expected)
        return spec, expected

    def test_both_pages(self):
        self.check("TR01_transformer_architecture", "architecture")
        self.check("TR02_transformer_attention", "attention")

    def test_cross_attention_key_value_handoff_cannot_disappear(self):
        spec, expected = self.check("TR01_transformer_architecture", "architecture")
        changed = copy.deepcopy(spec)
        changed["semantic_edges"].remove(["encoder_norm2", "decoder_cross"])
        changed["elements"] = [e for e in changed["elements"]
                               if e.get("semantic_link") != "encoder_norm2__decoder_cross"]
        with self.assertRaises(AssertionError):
            self.assertEqual({tuple(e) for e in changed["semantic_edges"]}, expected)
        with self.assertRaises(AssertionError):
            validate_drawn_routes(changed, expected)

    def test_value_feed_cannot_disappear(self):
        spec, expected = self.check("TR02_transformer_attention", "attention")
        changed = copy.deepcopy(spec)
        changed["semantic_edges"].remove(["values", "weighted_values"])
        changed["elements"] = [e for e in changed["elements"]
                               if e.get("semantic_link") != "values__weighted_values"]
        with self.assertRaises(AssertionError):
            validate_drawn_routes(changed, expected)


if __name__ == "__main__":
    unittest.main()
