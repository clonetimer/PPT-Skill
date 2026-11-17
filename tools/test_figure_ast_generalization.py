#!/usr/bin/env python3
"""Source-corpus coverage tests for the immutable FigureAST compiler."""
from __future__ import annotations

import json
import unittest
from collections import Counter
from pathlib import Path

from figure_ast import FigureAST

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ("Mamba_Figure1", "Swin_Figure2")
SUPPORTED = {
    "image", "text", "rect", "trapezoid", "line", "polyline",
    "polygon", "ellipse", "grid", "stack_grid", "sensor", "graph",
}


class FigureAstGeneralizationTests(unittest.TestCase):
    def test_independent_paper_specs_round_trip_without_semantic_loss(self):
        for name in FIGURES:
            with self.subTest(figure=name):
                path = ROOT / "dist/skill_tests/generalization" / f"{name}.json"
                spec = json.loads(path.read_text(encoding="utf-8"))
                ast = FigureAST.from_spec(spec)
                self.assertEqual(ast.to_spec(), spec)
                self.assertEqual(ast.source_sha256.__len__(), 64)
                self.assertEqual(ast.ast_sha256.__len__(), 64)
                self.assertEqual(len(ast.nodes), len(spec["elements"]))
                self.assertTrue({node.kind for node in ast.nodes}.issubset(SUPPORTED))
                self.assertEqual(
                    sum(Counter(node.kind for node in ast.nodes).values()),
                    len(spec["elements"]),
                )
                self.assertGreater(float(spec["canvas"]["width_in"]), 0)
                self.assertGreater(float(spec["canvas"]["height_in"]), 0)


if __name__ == "__main__":
    unittest.main()
