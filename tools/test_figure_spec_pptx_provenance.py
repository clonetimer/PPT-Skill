#!/usr/bin/env python3
"""Regression tests for stable source-to-native-PPTX object provenance."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from audit_figure_spec_pptx import audit_figure_spec_pptx
from pptx import Presentation
from render_figure_spec import render


class FigureSpecPptxProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.spec_path = self.root / "fixture.json"
        self.svg_path = self.root / "fixture.svg"
        self.pptx_path = self.root / "fixture.pptx"
        self.spec = {
            "id": "provenance-fixture",
            "canvas": {"width_in": 4.0, "height_in": 2.25},
            "style": {"font": "Arial"},
            "semantic_edges": [["input", "gcn"]],
            "elements": [
                {
                    "type": "text", "id": "el_title", "semantic_id": "slide_title",
                    "semantic_role": "annotation", "text": "Provenance test",
                    "x": 0.2, "y": 0.1, "w": 3.5, "h": 0.35,
                    "size": 16, "bold": True, "align": "left"
                },
                {
                    "type": "rect", "id": "el_input", "semantic_id": "input",
                    "semantic_role": "scientific_object",
                    "x": 0.2, "y": 0.8, "w": 0.8, "h": 0.5,
                    "fill": "#EAF2F5", "stroke": "#43525B", "sw": 1
                },
                {
                    "type": "line", "id": "el_route", "semantic_id": "input_to_gcn",
                    "semantic_role": "connector",
                    "x1": 1.0, "y1": 1.05, "x2": 1.8, "y2": 1.05,
                    "color": "#43525B", "sw": 1, "arrow": True
                },
                {
                    "type": "graph", "id": "el_graph", "semantic_id": "input_graph",
                    "semantic_role": "schematic_graph",
                    "x": 2.0, "y": 0.8, "w": 1.2, "h": 0.5,
                    "nodes": [[0.1, 0.5], [0.5, 0.1], [0.9, 0.5]],
                    "edges": [[0, 1], [1, 2]],
                    "fill": "#7896A6", "edge": "#43525B", "r": 0.06
                },
                {
                    "type": "polyline", "id": "el_wave", "semantic_id": "sensor_wave",
                    "semantic_role": "trace",
                    "points": [[0.2, 1.8], [0.5, 1.65], [0.8, 1.8]],
                    "color": "#668A9C", "sw": 1.2
                },
                {
                    "type": "polygon", "id": "el_triangle", "semantic_id": "decision",
                    "semantic_role": "scientific_object",
                    "points": [[3.3, 0.8], [3.8, 0.8], [3.55, 1.25]],
                    "fill": "#FFFFFF", "stroke": "#43525B", "sw": 1
                }
            ]
        }
        self.spec_path.write_text(json.dumps(self.spec, indent=2), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_renderer_preserves_source_ids_and_semantic_ids(self):
        render(self.spec, self.svg_path, self.pptx_path, preserve_source_ids=True)
        deck = Presentation(str(self.pptx_path))
        names = [shape.name for shape in deck.slides[0].shapes]
        self.assertTrue(any(name.startswith("slide_title__el_title__") for name in names))
        self.assertTrue(any(name.startswith("input__el_input__") for name in names))
        self.assertTrue(any(name.startswith("input_to_gcn__el_route__line") for name in names))
        self.assertTrue(any(name.startswith("input_to_gcn__el_route__arrowhead") for name in names))
        self.assertTrue(any(name.startswith("input_graph__el_graph__edge-01") for name in names))
        self.assertTrue(any(name.startswith("input_graph__el_graph__node-03") for name in names))
        self.assertTrue(any(name.startswith("sensor_wave__el_wave__segment-01") for name in names))
        self.assertTrue(any(name.startswith("decision__el_triangle__polygon") for name in names))

    def test_object_audit_maps_every_source_element(self):
        render(self.spec, self.svg_path, self.pptx_path, preserve_source_ids=True)
        report = audit_figure_spec_pptx(self.spec_path, self.pptx_path)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["source_element_count"], len(self.spec["elements"]))
        self.assertEqual(report["source_element_covered_count"], len(self.spec["elements"]))
        self.assertEqual(report["source_element_coverage"], 1.0)
        self.assertEqual(report["missing_source_element_ids"], [])
        self.assertEqual(report["semantic_object_counts"]["input_graph"], 5)
        self.assertGreater(report["object_inventory"]["native_text_shapes"], 0)
        self.assertGreater(report["object_inventory"]["native_connectors"], 0)

    def test_default_renderer_keeps_legacy_shape_names(self):
        render(self.spec, self.svg_path, self.pptx_path)
        deck = Presentation(str(self.pptx_path))
        names = [shape.name for shape in deck.slides[0].shapes]
        self.assertFalse(any("el_title" in name for name in names))
        self.assertFalse(any("el_graph" in name for name in names))

    def test_duplicate_source_element_ids_are_rejected(self):
        render(self.spec, self.svg_path, self.pptx_path, preserve_source_ids=True)
        duplicated = json.loads(self.spec_path.read_text(encoding="utf-8"))
        duplicated["elements"][1]["id"] = duplicated["elements"][0]["id"]
        self.spec_path.write_text(json.dumps(duplicated), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "FIGURE_SPEC_ELEMENT_ID_DUPLICATE"):
            audit_figure_spec_pptx(self.spec_path, self.pptx_path)


if __name__ == "__main__":
    unittest.main()
