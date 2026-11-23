"""Behavior checks for invisible-region composition using the real renderer."""
import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

try:
    from single_page_composer import PageError, compile_page, render_page, revise_region
except ImportError:
    PageError = ValueError
    compile_page = render_page = revise_region = None


def sample_page():
    return {
        "id": "attention", "title": "A local mechanism", "claim": "A schematic claim.",
        "canvas": {"width_in": 12, "height_in": 8}, "style": {"font": "Arial"},
        "sources": [{"id": "paper", "url": "https://example.org/paper", "locator": "Fig. 2"}],
        "notes": "Adjacency is schematic, not a measured network.",
        "regions": [{
            "id": "mechanism", "role": "figure", "bounds": {"x": 2, "y": 1, "w": 6, "h": 5},
            "spec": {"canvas": {"width_in": 4, "height_in": 2},
                     "semantic_edges": [["label", "body"]], "elements": [
                {"id": "label", "type": "text", "x": 0, "y": 0, "w": 4, "h": .4,
                 "text": "Attention", "size": 20},
                {"id": "body", "type": "rect", "x": .2, "y": .4, "w": 1, "h": .6,
                 "fill": "#FFFFFF", "stroke": "#334455", "radius": .1},
            ]},
        }],
    }


class SinglePageComposerTests(unittest.TestCase):
    def compile(self, page):
        self.assertIsNotNone(compile_page, "Missing single-page composition utility")
        return compile_page(page)

    def test_uniform_contain_fit_centers_geometry_without_drawing_region_frames(self):
        page = sample_page()
        before = copy.deepcopy(page)
        spec = self.compile(page)
        self.assertEqual(len(spec["elements"]), 2)
        title, body = spec["elements"]
        for key, expected in {"x": 2, "y": 2, "w": 6, "h": .6, "size": 30}.items():
            self.assertAlmostEqual(title[key], expected)
        for key, expected in {"x": 2.3, "y": 2.6, "w": 1.5, "h": .9,
                              "radius": .15, "sw": 1.5}.items():
            self.assertAlmostEqual(body[key], expected)
        self.assertEqual(spec["sources"], page["sources"])
        self.assertEqual(spec["regions"], page["regions"])
        self.assertEqual(page, before)

    def test_absolute_points_lines_and_normalized_graph_nodes_transform_correctly(self):
        page = sample_page()
        page["regions"][0]["spec"]["elements"] = [
            {"id": "edge", "type": "line", "x1": 0, "y1": 0, "x2": 2, "y2": 2,
             "arrow": True, "arrow_size": .2, "sw": 2},
            {"id": "path", "type": "polyline", "points": [[0, 0], [1, 2]], "color": "#334455"},
            {"id": "area", "type": "polygon", "points": [[0, 0], [2, 0], [1, 2]]},
            {"id": "graph", "type": "graph", "x": 0, "y": 0, "w": 4, "h": 2,
             "nodes": [[0, .5], [1, 1]], "edges": [[0, 1]], "r": .1,
             "fill": "#AABBCC", "edge": "#334455"},
        ]
        edge, path, area, graph = self.compile(page)["elements"]
        self.assertEqual([edge[k] for k in ("x1", "y1", "x2", "y2", "sw")], [2, 2, 5, 5, 3])
        self.assertAlmostEqual(edge["arrow_size"], .3)
        self.assertEqual(path["points"], [[2, 2], [3.5, 5]])
        self.assertAlmostEqual(path["sw"], 1.8)
        self.assertEqual(area["points"], [[2, 2], [5, 2], [3.5, 5]])
        self.assertEqual(graph["nodes"], [[0, .5], [1, 1]])
        self.assertEqual(graph["edges"], [[0, 1]])
        self.assertEqual([graph[k] for k in ("x", "y", "w", "h")], [2, 2, 6, 3])
        self.assertAlmostEqual(graph["r"], .15)
        self.assertAlmostEqual(graph["sw"], 1.125)

    def test_other_primitives_and_implicit_sizes_keep_the_same_scale(self):
        page = sample_page()
        region = page["regions"][0]
        region["spec"]["style"] = {"font": "DejaVu Sans"}
        region["spec"]["elements"] = [
            {"type": kind, "x": .2, "y": .4, "w": 1, "h": .6,
             "fill": "#AABBCC", "stroke": "#334455", "rows": 2, "cols": 3,
             "layers": 3, "path": "an-image.png"}
            for kind in ("ellipse", "trapezoid", "grid", "stack_grid", "image")
        ] + [{"type": "sensor", "x": .2, "y": .4},
             {"type": "text", "x": 0, "y": 0, "w": 1, "h": 1, "text": "Default size"},
             {"type": "line", "x1": 0, "y1": 0, "x2": 1, "y2": 1, "arrow": True}]
        elements = self.compile(page)["elements"]
        for element in elements[:5]:
            for key, expected in {"x": 2.3, "y": 2.6, "w": 1.5, "h": .9}.items():
                self.assertAlmostEqual(element[key], expected)
        self.assertAlmostEqual(elements[3]["offset"], .24)
        self.assertEqual(elements[5]["scale"], 1.5)
        self.assertEqual(elements[6]["size"], 21)
        self.assertEqual(elements[6]["font"], "DejaVu Sans")
        self.assertAlmostEqual(elements[7]["arrow_size"], .1575)

    def test_local_revision_deep_copies_and_leaves_sibling_compilation_unchanged(self):
        page = sample_page()
        sibling = copy.deepcopy(page["regions"][0])
        sibling.update(id="footer", bounds={"x": 0, "y": 6, "w": 12, "h": 2})
        page["regions"].append(sibling)
        original = copy.deepcopy(page)
        replacement = copy.deepcopy(page["regions"][0]["spec"])
        replacement["elements"][0]["text"] = "Revised attention"
        self.assertIsNotNone(revise_region, "Missing region revision utility")
        revised = revise_region(page, "mechanism", {"spec": replacement})
        self.assertNotIn("elements", revised)
        self.assertEqual(page, original)
        self.assertEqual(revised["regions"][1], page["regions"][1])
        old = [e for e in self.compile(page)["elements"] if e["region_id"] == "footer"]
        new = [e for e in self.compile(revised)["elements"] if e["region_id"] == "footer"]
        self.assertEqual(new, old)
        self.assertEqual(revised["regions"][0]["id"], "mechanism")
        replacement["elements"][0]["text"] = "Caller changed again"
        revised["regions"][1]["spec"]["elements"][0]["text"] = "Sibling changed later"
        self.assertEqual(revised["regions"][0]["spec"]["elements"][0]["text"], "Revised attention")
        self.assertEqual(page, original)

    def test_revising_compiled_page_updates_direct_renderer_content(self):
        from render_figure_spec import render

        page = sample_page()
        sibling = copy.deepcopy(page["regions"][0])
        sibling.update(id="footer", bounds={"x": 0, "y": 6, "w": 12, "h": 2})
        page["regions"].append(sibling)
        compiled = self.compile(page)
        original = copy.deepcopy(compiled)
        replacement = copy.deepcopy(compiled["regions"][0]["spec"])
        replacement["elements"][0]["text"] = "Revised compiled attention"
        revised = revise_region(compiled, "mechanism", {"spec": replacement})
        self.assertEqual(compiled, original)
        old_sibling = [e for e in compiled["elements"] if e["region_id"] == "footer"]
        new_sibling = [e for e in revised["elements"] if e["region_id"] == "footer"]
        self.assertEqual(new_sibling, old_sibling)
        with TemporaryDirectory() as directory:
            svg, pptx = Path(directory) / "revised.svg", Path(directory) / "revised.pptx"
            render(revised, svg, pptx)
            slide = Presentation(pptx).slides[0]
            text = [s.text for s in slide.shapes if s.has_text_frame and s.text]
            self.assertEqual(text, ["Revised compiled attention", "Attention"])
            self.assertIn("Revised compiled attention", svg.read_text(encoding="utf-8"))

    def test_namespaces_are_unique_even_when_input_ids_contain_separators(self):
        page = sample_page()
        first = page["regions"][0]
        first["id"] = "a/b"
        first["spec"]["elements"][0]["id"] = "c"
        second = copy.deepcopy(first)
        second["id"] = "a"
        second["spec"]["elements"][0]["id"] = "b/c"
        del second["spec"]["elements"][1]["id"]
        page["regions"].append(second)
        ids = [e["id"] for e in self.compile(page)["elements"]]
        self.assertEqual(len(set(ids)), 4)
        page["regions"].reverse()
        self.assertEqual(set(ids), {e["id"] for e in self.compile(page)["elements"]})

    def test_invalid_dimensions_unsupported_types_and_duplicate_ids_are_rejected(self):
        mutations = [
            (lambda p: p["canvas"].update(width_in=0), "canvas"),
            (lambda p: p["regions"][0]["bounds"].update(x=-1), "bounds"),
            (lambda p: p["regions"][0]["bounds"].update(x=8), "bounds"),
            (lambda p: p["regions"][0]["bounds"].update(h=float("inf")), "bounds"),
            (lambda p: p["regions"][0]["spec"]["canvas"].update(height_in=-1), "canvas"),
            (lambda p: p["regions"][0]["spec"]["elements"][0].update(w=0), "w"),
            (lambda p: p["regions"][0]["spec"]["elements"][0].update(type="arc"), "unsupported"),
            (lambda p: p["regions"].append(copy.deepcopy(p["regions"][0])), "duplicate"),
            (lambda p: p["regions"][0]["spec"]["elements"][1].update(id="label"), "duplicate"),
        ]
        for mutate, message in mutations:
            with self.subTest(message=message):
                page = sample_page()
                mutate(page)
                self.assertIsNotNone(compile_page, "Missing single-page composition utility")
                with self.assertRaisesRegex(PageError, message):
                    compile_page(page)

    def test_revise_rejects_unknown_region_identity_changes_and_unknown_fields(self):
        self.assertIsNotNone(revise_region, "Missing region revision utility")
        for region_id, patch, message in [
            ("missing", {}, "unknown"),
            ("mechanism", {"id": "renamed"}, "identity"),
            ("mechanism", {"elements": []}, "fields"),
        ]:
            with self.subTest(region_id=region_id, patch=patch):
                with self.assertRaisesRegex(PageError, message):
                    revise_region(sample_page(), region_id, patch)

    def test_malformed_point_lists_and_graph_node_indices_are_rejected(self):
        bad_elements = [
            {"type": "polygon", "points": [[0, 0], [1, 2]]},
            {"type": "polyline", "points": [[0, 0], [1, float("nan")]], "color": "#334455"},
            {"type": "line", "x1": 0, "y1": 0, "x2": 1},
            {"type": "graph", "x": 0, "y": 0, "w": 1, "h": 1,
             "nodes": [[0, 0], [1, 1]], "edges": [[0, 2]], "fill": "#AABBCC", "edge": "#334455"},
        ]
        for element in bad_elements:
            with self.subTest(kind=element["type"]):
                page = sample_page()
                page["regions"][0]["spec"]["elements"] = [element]
                self.assertIsNotNone(compile_page, "Missing single-page composition utility")
                with self.assertRaises(PageError):
                    compile_page(page)

    def test_render_writes_one_native_slide_and_retains_source_notes(self):
        self.assertIsNotNone(render_page, "Missing page rendering utility")
        with TemporaryDirectory() as directory:
            paths = render_page(sample_page(), directory, stem="one-page")
            self.assertEqual(set(paths), {"json", "svg", "pptx"})
            self.assertTrue(all(Path(path).is_file() for path in paths.values()))
            compiled = json.loads(Path(paths["json"]).read_text(encoding="utf-8"))
            self.assertEqual(compiled["elements"][0]["region_id"], "mechanism")
            self.assertIn("Attention", Path(paths["svg"]).read_text(encoding="utf-8"))
            deck = Presentation(paths["pptx"])
            self.assertEqual(len(deck.slides), 1)
            slide = deck.slides[0]
            self.assertEqual(len(slide.shapes), 2)
            self.assertFalse(any(shape.shape_type == MSO_SHAPE_TYPE.PICTURE for shape in slide.shapes))
            self.assertEqual(slide.shapes[0].text, "Attention")
            self.assertEqual(slide.shapes[0].text_frame.paragraphs[0].runs[0].font.size.pt, 30)
            notes = slide.notes_slide.notes_text_frame.text
            for text in ("A schematic claim.", "https://example.org/paper", "Fig. 2", "Adjacency is schematic"):
                self.assertIn(text, notes)


if __name__ == "__main__":
    unittest.main()
