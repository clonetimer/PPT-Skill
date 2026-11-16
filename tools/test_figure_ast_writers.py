#!/usr/bin/env python3
"""Round-trip and writer tests for the backend-neutral FigureAST pilot."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from figure_ast import FigureAST
from figure_ast_writers import DrawingMLWriter, SvgWriter, render_ast


class FigureAstWriterTests(unittest.TestCase):
    def make_spec(self, root: Path) -> dict:
        image_path = root / "one-pixel.png"
        Image.new("RGB", (1, 1), (40, 80, 120)).save(image_path)
        return {
            "id": "AST_WRITER_TEST",
            "canvas": {"width_in": 8.0, "height_in": 4.5},
            "style": {"font": "DejaVu Sans"},
            "semantic_edges": [["input", "gcn"]],
            "elements": [
                {"type": "rect", "id": "r1", "x": .2, "y": .2, "w": 1.0, "h": .5, "fill": "#FFFFFF", "stroke": "#223344", "sw": 1},
                {"type": "text", "id": "t1", "x": .3, "y": .25, "w": .8, "h": .3, "text": "AST", "font": "DejaVu Sans", "size": 12, "color": "#112233", "align": "center"},
                {"type": "line", "id": "l1", "x1": 1.3, "y1": .4, "x2": 2.0, "y2": .4, "color": "#223344", "sw": 1, "arrow": True, "dash": True},
                {"type": "trapezoid", "id": "tr1", "x": 2.1, "y": .2, "w": .8, "h": .5, "fill": "#E8F0F3", "stroke": "#223344"},
                {"type": "polyline", "id": "pl1", "x": .2, "y": 1.0, "points": [[.2, 1.0], [.6, 1.2], [1.0, 1.0]], "color": "#336699"},
                {"type": "polygon", "id": "pg1", "points": [[1.2, 1.0], [1.7, 1.0], [1.5, 1.5]], "fill": "#DDEEFF", "stroke": "#223344"},
                {"type": "ellipse", "id": "el1", "x": 2.0, "y": 1.0, "w": .5, "h": .5, "fill": "#DDEEFF", "stroke": "#223344"},
                {"type": "grid", "id": "g1", "x": 2.7, "y": 1.0, "w": 1.0, "h": .7, "rows": 2, "cols": 3},
                {"type": "stack_grid", "id": "sg1", "x": 3.9, "y": 1.0, "w": 1.0, "h": .7, "rows": 2, "cols": 2, "layers": 3},
                {"type": "sensor", "id": "s1", "x": 5.1, "y": 1.0, "scale": .7, "variant": 1},
                {"type": "graph", "id": "gr1", "x": 6.0, "y": 1.0, "w": 1.0, "h": .8, "nodes": [[.1, .5], [.5, .1], [.9, .5]], "edges": [[0, 1], [1, 2]], "fill": "#77AACC", "edge": "#223344"},
                {"type": "image", "id": "im1", "x": 6.9, "y": 2.0, "w": .5, "h": .5, "path": str(image_path)},
            ],
        }

    def test_ast_round_trip_preserves_figure_spec_and_source_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            spec = self.make_spec(Path(folder))
            ast = FigureAST.from_spec(spec)
            self.assertEqual(ast.to_spec(), spec)
            self.assertEqual(len(ast.nodes), len(spec["elements"]))
            self.assertEqual(len(ast.source_sha256), 64)
            self.assertEqual(len(ast.ast_sha256), 64)
            self.assertEqual(ast.to_dict()["ast_version"], "1.0.0")
            self.assertEqual(ast.nodes[0].kind, "rect")
            self.assertEqual(ast.nodes[0].geometry.get("x"), .2)
            self.assertEqual(ast.nodes[0].paint.get("fill"), "#FFFFFF")
            with self.assertRaises(Exception):
                ast.nodes[0].geometry.items += (("x", 99),)

    def test_two_writers_consume_same_ast_and_emit_native_pptx(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            spec = self.make_spec(root)
            ast = FigureAST.from_spec(spec)
            svg = root / "out.svg"
            pptx = root / "out.pptx"
            result = render_ast(ast, svg, pptx, root=root, preserve_source_ids=True)
            self.assertTrue(svg.is_file())
            self.assertTrue(pptx.is_file())
            svg_text = svg.read_text(encoding="utf-8")
            self.assertIn("<svg", svg_text)
            self.assertIn("<text", svg_text)
            self.assertIn("<polyline", svg_text)
            self.assertIn("<pattern", svg_text) if "<pattern" in svg_text else self.assertIn("<line", svg_text)
            self.assertEqual(result["ast_sha256"], ast.ast_sha256)
            deck = Presentation(pptx)
            self.assertEqual(len(deck.slides), 1)
            shapes = list(deck.slides[0].shapes)
            self.assertGreaterEqual(len(shapes), 20)
            self.assertEqual(sum(s.shape_type == MSO_SHAPE_TYPE.PICTURE for s in shapes), 1)
            names = {s.name for s in shapes}
            self.assertTrue(any("r1" in name for name in names))
            self.assertTrue(any("t1" in name for name in names))
            for shape in shapes:
                self.assertGreaterEqual(shape.left, 0)
                self.assertGreaterEqual(shape.top, 0)
                self.assertLessEqual(shape.left + shape.width, deck.slide_width)
                self.assertLessEqual(shape.top + shape.height, deck.slide_height)

    def test_invalid_or_duplicate_primitives_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            spec = self.make_spec(Path(folder))
            spec["elements"][1]["id"] = "r1"
            with self.assertRaisesRegex(ValueError, "DUPLICATE_ELEMENT_ID"):
                FigureAST.from_spec(spec)
            spec = self.make_spec(Path(folder))
            spec["elements"].append({"type": "unknown", "id": "bad"})
            with self.assertRaisesRegex(ValueError, "UNSUPPORTED_PRIMITIVE"):
                FigureAST.from_spec(spec)
            spec = self.make_spec(Path(folder))
            spec["elements"][-2]["edges"] = [[0, 99]]
            with self.assertRaisesRegex(ValueError, "INVALID_GRAPH_EDGE"):
                FigureAST.from_spec(spec)


if __name__ == "__main__":
    unittest.main()
