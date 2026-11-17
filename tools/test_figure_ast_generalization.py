#!/usr/bin/env python3
"""Source-backed FigureAST corpus provenance and semantic round-trip tests."""
from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from figure_ast import FigureAST

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "specs/ast_generalization_corpus_v1.json"
SUPPORTED = {
    "image", "text", "rect", "trapezoid", "line", "polyline",
    "polygon", "ellipse", "grid", "stack_grid", "sensor", "graph",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class FigureAstGeneralizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.figures = cls.corpus["figures"]

    def test_manifest_has_unique_source_backed_paper_figures(self):
        ids = [entry["id"] for entry in self.figures]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(self.figures), 6)
        for entry in self.figures:
            with self.subTest(figure=entry["id"]):
                spec_path = ROOT / entry["figure_spec"]
                self.assertTrue(spec_path.is_file(), entry["figure_spec"])
                self.assertEqual(entry["source_evidence"]["status"], "source_visible_redraw")
                evidence = entry["source_evidence"]
                self.assertEqual(evidence["kind"], "arxiv")
                self.assertTrue(evidence["url"].startswith("https://arxiv.org/"))
                recorded_pdf_hash = evidence.get("source_pdf_sha256")
                if recorded_pdf_hash:
                    self.assertEqual(len(recorded_pdf_hash), 64)
                    self.assertTrue(all(char in "0123456789abcdef" for char in recorded_pdf_hash))
                for asset in entry.get("asset_substitutions", []):
                    asset_path = ROOT / asset["path"]
                    self.assertTrue(asset_path.is_file(), asset["path"])
                    self.assertEqual(sha256(asset_path), asset["sha256"])
                    self.assertTrue(asset.get("license"))
                    self.assertTrue(asset.get("note"))

    def test_independent_paper_specs_round_trip_without_semantic_loss(self):
        observed_types = set()
        for entry in self.figures:
            with self.subTest(figure=entry["id"]):
                path = ROOT / entry["figure_spec"]
                spec = json.loads(path.read_text(encoding="utf-8"))
                if spec.get("id") is not None:
                    self.assertEqual(spec["id"], entry["id"])
                else:
                    self.assertEqual(
                        spec.get("meta", {}).get("paper"),
                        entry["paper_title"],
                        "Legacy source FigureSpecs without explicit IDs are identified by the corpus manifest.",
                    )
                ast = FigureAST.from_spec(spec)
                expected_round_trip = dict(spec)
                expected_round_trip.setdefault("id", "unnamed-figure")
                self.assertEqual(ast.to_spec(), expected_round_trip)
                self.assertEqual(len(ast.source_sha256), 64)
                self.assertEqual(len(ast.ast_sha256), 64)
                self.assertEqual(len(ast.nodes), len(spec["elements"]))
                kinds = {node.kind for node in ast.nodes}
                self.assertTrue(kinds.issubset(SUPPORTED))
                observed_types.update(kinds)
                self.assertGreater(float(spec["canvas"]["width_in"]), 0)
                self.assertGreater(float(spec["canvas"]["height_in"]), 0)
        self.assertIn("image", observed_types)
        self.assertIn("grid", observed_types)
        self.assertIn("ellipse", observed_types)
        self.assertIn("polygon", observed_types)

    def test_clip_replacement_photo_is_not_misrepresented_as_original_paper_art(self):
        clip = next(entry for entry in self.figures if entry["id"] == "MLC01_clip_overview")
        substitutions = clip["asset_substitutions"]
        self.assertEqual(len(substitutions), 1)
        self.assertEqual(substitutions[0]["license"], "CC0 1.0")
        self.assertIn("not the original", substitutions[0]["note"].lower())


if __name__ == "__main__":
    unittest.main()
