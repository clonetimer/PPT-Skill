"""Behavioral checks for evidenced, editable scientific glyphs."""
from __future__ import annotations

import copy
import importlib
import math
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile


CASES = {
    "tensor": {"shape": ["N", 16, "T"]},
    "time_series": {"shape": ["T", 3]},
    "conv1d": {"shape": ["T", 16]},
    "embedding": {"shape": ["N", "D"]},
    "add": {},
    "graph_attention": {"heads": 3, "merge": "unknown", "adjacency": "unknown"},
    "pool": {"groups": 3, "reduction": "mean"},
    "concat": {"shape": ["N", "D"], "inputs": 2},
    "projection": {"shape": ["N", 16]},
    "head": {"outputs": 3, "activation": "softmax"},
    "gate": {},
    "process": {"opaque": True, "explanation": "Internal operation not supplied"},
}


def node(node_kind, **updates):
    item = {"id": "sample", "kind": node_kind, "label": node_kind,
            "evidence": ["source"], "params": copy.deepcopy(CASES[node_kind]),
            "box": [1.0, 2.0, 3.2, 1.9], "glyph": node_kind}
    item.update(updates)
    return item


def extent(element):
    if element["type"] in {"line", "polyline", "polygon"}:
        points = element.get("points", [(element.get("x1"), element.get("y1")),
                                         (element.get("x2"), element.get("y2"))])
        return min(p[0] for p in points), min(p[1] for p in points), \
            max(p[0] for p in points), max(p[1] for p in points)
    return element["x"], element["y"], element["x"] + element["w"], element["y"] + element["h"]


def on_segment(point, a, b):
    px, py = point
    ax, ay = a
    bx, by = b
    return (abs((px-ax)*(by-ay)-(py-ay)*(bx-ax)) < 1e-7 and
            min(ax, bx)-1e-7 <= px <= max(ax, bx)+1e-7 and
            min(ay, by)-1e-7 <= py <= max(ay, by)+1e-7)


def on_boundary(point, element):
    kind = element["type"]
    if kind == "ellipse":
        x, y, w, h = (element[k] for k in ("x", "y", "w", "h"))
        return abs(((point[0]-x-w/2)/(w/2))**2 +
                   ((point[1]-y-h/2)/(h/2))**2 - 1) < 1e-6
    if kind in {"rect", "polygon", "polyline", "line"}:
        if kind == "rect":
            x, y, right, bottom = extent(element)
            points = [(x, y), (right, y), (right, bottom), (x, bottom), (x, y)]
        elif kind == "line":
            points = [(element["x1"], element["y1"]), (element["x2"], element["y2"])]
        else:
            points = element["points"] + (element["points"][:1] if kind == "polygon" else [])
        return any(on_segment(point, a, b) for a, b in zip(points, points[1:]))
    return False


class ScientificGlyphTests(unittest.TestCase):
    def test_process_text_occupies_its_frame_without_repeated_unknown_banner(self):
        drawn = self.draw(node('process', label='Shared network'))
        frame = next(e for e in drawn['elements'] if e['visual_role'] == 'process_body')
        label = next(e for e in drawn['elements'] if e['visual_role'] == 'node_label')
        fx, fy, fr, fb = extent(frame)
        lx, ly, lr, lb = extent(label)
        self.assertGreaterEqual(ly, fy)
        self.assertGreaterEqual(lx, fx)
        self.assertLessEqual(lr, fr)
        self.assertLessEqual(lb, fb)
        self.assertNotIn('内部未提供', '\n'.join(e.get('text', '') for e in drawn['elements']))

    def draw(self, item):
        try:
            module = importlib.import_module("scientific_figure_glyphs")
        except ModuleNotFoundError as exc:
            if exc.name != "scientific_figure_glyphs":
                raise
            self.fail("scientific draw_node is not implemented")
        return module.draw_node(item)

    def test_each_kind_emits_bounded_editable_marks_and_boundary_ports(self):
        for kind in CASES:
            with self.subTest(kind=kind):
                item = node(kind)
                before = copy.deepcopy(item)
                drawn = self.draw(item)
                self.assertEqual(item, before)
                self.assertEqual(drawn["box"], item["box"])
                x, y, w, h = item["box"]
                nontext = [e for e in drawn["elements"] if e["type"] != "text"]
                self.assertTrue(nontext)
                for e in drawn["elements"]:
                    self.assertEqual(e["semantic_owner"], "sample")
                    self.assertTrue(e["visual_role"])
                    self.assertNotEqual(e["type"], "image")
                    left, top, right, bottom = extent(e)
                    self.assertGreaterEqual(left, x-1e-8)
                    self.assertGreaterEqual(top, y-1e-8)
                    self.assertLessEqual(right, x+w+1e-8)
                    self.assertLessEqual(bottom, y+h+1e-8)
                    if e["type"] == "text":
                        self.assertGreaterEqual(e["size"], 9)
                for name in ("left", "right", "top", "bottom", "input", "output"):
                    point = drawn["ports"][name]
                    self.assertTrue(all(math.isfinite(v) for v in point))
                    self.assertTrue(any(on_boundary(point, e) for e in nontext), name)
                self.assertEqual(drawn["ports"]["input"], drawn["ports"]["left"])
                self.assertEqual(drawn["ports"]["output"], drawn["ports"]["right"])

    def test_head_count_changes_visible_parallel_head_geometry(self):
        for count in (1, 2, 3, 4):
            item = node("graph_attention", box=[0, 0, 4.2, 2.0])
            item["params"]["heads"] = count
            drawn = self.draw(item)
            centers = []
            for i in range(count):
                heads = [e for e in drawn["elements"] if e.get("head_index") == i
                         and e["visual_role"] == "attention_head" and e["type"] != "text"]
                self.assertTrue(heads, f"Head {i} has no visible mark")
                centers.append((heads[0]["x"] + heads[0]["w"]/2))
            self.assertEqual(len(set(centers)), count)
            self.assertEqual({e["head_index"] for e in drawn["elements"] if "head_index" in e},
                             set(range(count)))

    def test_deleting_one_head_changes_actual_svg_and_native_shapes(self):
        from render_figure_spec import render
        drawn = self.draw(node("graph_attention"))
        altered = [e for e in drawn["elements"] if e.get("head_index") != 1]
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for name, elements in (("complete", drawn["elements"]), ("deleted", altered)):
                base = Path(directory) / name
                render({"canvas": {"width_in": 5, "height_in": 5}, "elements": elements},
                       base.with_suffix(".svg"), base.with_suffix(".pptx"))
                paths.append(base)
            svg = [ET.parse(p.with_suffix(".svg")).getroot() for p in paths]
            svg_ns = "{http://www.w3.org/2000/svg}"
            self.assertGreater(len(svg[0].findall(svg_ns + "ellipse")),
                               len(svg[1].findall(svg_ns + "ellipse")))
            counts = []
            for path in paths:
                with zipfile.ZipFile(path.with_suffix(".pptx")) as deck:
                    xml = ET.fromstring(deck.read("ppt/slides/slide1.xml"))
                    ns = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
                    self.assertEqual(len(xml.findall(".//" + ns + "pic")), 0)
                    counts.append(len(xml.findall(".//" + ns + "sp")))
            self.assertGreater(counts[0], counts[1])

    def test_unknown_neighborhood_and_merge_are_visibly_preserved(self):
        drawn = self.draw(node("graph_attention"))
        text = " ".join(e.get("text", "") for e in drawn["elements"])
        self.assertIn("融合未提供", text)
        self.assertIn("示意", text)
        self.assertIn("N(i)", text)
        self.assertNotIn("concat", text)
        self.assertNotIn("mean", text)
        self.assertNotIn("sum", text)

    def test_known_adjacency_keeps_given_edges_in_every_head(self):
        item = node("graph_attention", box=[0, 0, 5, 2.2], params={
            "heads": 2, "merge": "mean", "adjacency": "known",
            "graph_nodes": ["a", "b", "c"], "graph_edges": [[0, 1], [2, 1]]})
        drawn = self.draw(item)
        for head in (0, 1):
            edges = [e for e in drawn["elements"] if e.get("head_index") == head
                     and e.get("graph_edge") is not None and e["type"] == "line"]
            self.assertEqual({tuple(e["graph_edge"]) for e in edges}, {(0, 1), (2, 1)})
        text = " ".join(e.get("text", "") for e in drawn["elements"])
        self.assertIn("mean", text)
        self.assertNotIn("邻域示意", text)

    def test_each_attention_head_has_a_path_from_the_shared_input(self):
        for adjacency in ("unknown", "known"):
            params = {"heads": 3, "merge": "unknown", "adjacency": adjacency}
            if adjacency == "known":
                params.update(graph_nodes=["a", "b", "c"], graph_edges=[[0, 1], [2, 1]])
            drawn = self.draw(node("graph_attention", box=[0, 0, 5, 2.4], params=params))
            buses = [e for e in drawn["elements"] if e["type"] == "line"
                     and e["visual_role"] == "shared_input"]
            self.assertTrue(any(on_boundary(drawn["ports"]["input"], e) for e in buses))
            self.assertTrue(any(on_boundary(drawn["ports"]["top"], e) for e in buses))
            for index in range(3):
                paths = [e for e in drawn["elements"] if e["type"] == "line"
                         and e["visual_role"] == "head_input" and e.get("head_index") == index]
                self.assertTrue(paths, f"Head {index} has no input path")
                self.assertTrue(any(on_boundary([e["x1"], e["y1"]], bus)
                                    for e in paths for bus in buses))

    def test_scientific_kinds_have_mechanism_specific_geometry(self):
        expected = {"tensor": "tensor_plane", "conv1d": "conv_window",
                    "pool": "pool_feature", "concat": "concat_segment",
                    "head": "output_marker", "gate": "gate_boundary"}
        signatures = []
        for kind, role in expected.items():
            drawn = self.draw(node(kind))
            marks = [e for e in drawn["elements"] if e["type"] != "text"]
            self.assertTrue(any(e["visual_role"] == role for e in marks))
            signatures.append(tuple((e["type"], tuple(round(v, 3) for v in extent(e)))
                                    for e in marks))
        self.assertEqual(len(set(signatures)), len(expected))

    def test_dimensions_activation_and_symbolic_threshold_stay_visible(self):
        for kind, fragments in (("tensor", ("N", "16", "T")),
                                ("head", ("3", "softmax")), ("gate", ("τ", "未提供"))):
            with self.subTest(kind=kind):
                text = " ".join(e.get("text", "") for e in self.draw(node(kind))["elements"])
                for fragment in fragments:
                    self.assertIn(fragment, text)

    def test_concat_input_count_controls_visible_segments(self):
        drawn = self.draw(node("concat", params={"inputs": 4}))
        segments = [e for e in drawn["elements"] if e["visual_role"] == "concat_segment"
                    and e["type"] != "text"]
        self.assertEqual(len(segments), 4)
        self.assertEqual(len({e["x"] for e in segments}), 4)

    def test_two_dimensional_tensor_uses_one_plane(self):
        drawn = self.draw(node("tensor", params={"shape": ["N", 64]}))
        planes = [e for e in drawn["elements"] if e["visual_role"] == "tensor_plane"
                  and e["type"] != "text"]
        self.assertEqual(len(planes), 1)
        text = " ".join(e.get("text", "") for e in drawn["elements"])
        self.assertIn("N × 64", text)
        self.assertIn("示意", text)

    def test_higher_rank_tensor_stack_is_disclosed_as_schematic(self):
        drawn = self.draw(node("tensor"))
        planes = [e for e in drawn["elements"] if e["visual_role"] == "tensor_plane"
                  and e["type"] != "text"]
        self.assertGreater(len(planes), 1)
        self.assertTrue(any("示意" in e.get("text", "") for e in drawn["elements"]))

    def test_group_pooling_keeps_independent_group_outputs(self):
        for groups, visible in ((3, {0, 1, 2}), (17, {0, 16})):
            with self.subTest(groups=groups):
                drawn = self.draw(node("pool", params={"groups": groups, "reduction": "mean",
                                                        "shape": [groups, 128]}))
                outputs = [e for e in drawn["elements"] if e["visual_role"] == "pool_output"
                           and e["type"] == "rect"]
                means = [e for e in drawn["elements"] if e["visual_role"] == "pool_reduction"
                         and e["type"] == "ellipse"]
                self.assertEqual({e.get("group_index") for e in outputs}, visible)
                self.assertEqual({e.get("group_index") for e in means}, visible)
                self.assertEqual(len(outputs), len(visible))
                text = " ".join(e.get("text", "") for e in drawn["elements"])
                self.assertIn(f"G={groups}", text)
                self.assertIn("128", text)
                self.assertIn("示意", text)
                if groups == 17:
                    self.assertTrue(all(e.get("compressed") for e in outputs))
                    self.assertTrue(any("⋯" in e.get("text", "") for e in drawn["elements"]))

    def test_large_task_heads_keep_exact_count_with_omission(self):
        for count in (25, 43):
            with self.subTest(outputs=count):
                drawn = self.draw(node("head", params={"outputs": count, "activation": "softmax"}))
                markers = [e for e in drawn["elements"] if e["visual_role"] == "output_marker"
                           and e["type"] != "text"]
                self.assertEqual({e.get("output_index") for e in markers}, {0, count-1})
                self.assertTrue(all(e.get("compressed") and e.get("schematic") for e in markers))
                text = " ".join(e.get("text", "") for e in drawn["elements"])
                for label in (str(count), "softmax", "示意", "⋯"):
                    self.assertIn(label, text)

    def test_chinese_labels_and_requested_font_are_preserved(self):
        label = "多任务共享编码器的图邻域注意力表示"
        drawn = self.draw(node("graph_attention", label=label, box=[1, 1, 3.2, 2.4],
                               font="Microsoft YaHei", font_size=12))
        title = [e for e in drawn["elements"] if e["visual_role"] == "node_label"]
        self.assertEqual("".join(e["text"].replace("\n", "") for e in title), label)
        self.assertTrue(all(e["font"] == "Microsoft YaHei" for e in drawn["elements"]
                            if e["type"] == "text"))
        self.assertTrue(all(e["size"] == 12 for e in title))

    def test_timeseries_is_disclosed_as_schematic(self):
        drawn = self.draw(node("time_series"))
        self.assertTrue(any("示意" in e.get("text", "") or "schematic" in e.get("text", "")
                            for e in drawn["elements"]))
        self.assertTrue(any(e["type"] in {"line", "polyline"} for e in drawn["elements"]))

    def test_provided_sequence_dimensions_remain_visible(self):
        for kind, shape, expected in (("conv1d", [48], "48"),
                                      ("time_series", ["T", 48], "T × 48")):
            drawn = self.draw(node(kind, params={"shape": shape}))
            text = " ".join(e.get("text", "") for e in drawn["elements"])
            self.assertIn(expected, text)

    def test_all_explicit_shapes_remain_visible(self):
        for kind in CASES:
            with self.subTest(kind=kind):
                item = node(kind, box=[0, 0, 3.2, 2.4])
                item["params"]["shape"] = ["N", 48]
                text = " ".join(e.get("text", "") for e in self.draw(item)["elements"])
                self.assertIn("N × 48", text)

    def test_known_node_identifiers_and_self_loops_fit_their_box(self):
        item = node("graph_attention", box=[0, 0, 7, 3], params={
            "heads": 2, "merge": "mean", "adjacency": "known",
            "graph_nodes": ["sensor_A", "sensor_B"], "graph_edges": [[0, 0], [0, 1]]})
        drawn = self.draw(item)
        text = " ".join(e.get("text", "") for e in drawn["elements"])
        self.assertIn("sensor_A", text)
        self.assertIn("sensor_B", text)
        for e in drawn["elements"]:
            left, top, right, bottom = extent(e)
            self.assertGreaterEqual(left, 0)
            self.assertGreaterEqual(top, 0)
            self.assertLessEqual(right, 7)
            self.assertLessEqual(bottom, 3)

    def test_large_counts_fit_the_provided_twelve_point_boxes(self):
        samples = [node("pool", box=[0, 0, 2.3, 2.0], font_size=12,
                        params={"groups": 17, "reduction": "mean", "shape": [17, 48]})]
        samples += [node("head", box=[0, 0, 3.3, 1.8], font_size=12,
                         params={"outputs": count, "activation": "softmax"}) for count in (25, 43)]
        for item in samples:
            drawn = self.draw(item)
            for element in drawn["elements"]:
                left, top, right, bottom = extent(element)
                self.assertGreaterEqual(left, 0)
                self.assertGreaterEqual(top, 0)
                self.assertLessEqual(right, item["box"][2]+1e-8)
                self.assertLessEqual(bottom, item["box"][3]+1e-8)

    def test_invalid_or_unreadable_inputs_fail_actionably(self):
        examples = [node("tensor", kind="invented"), node("tensor", box=[0, 0, .1, .1]),
                    node("tensor", box=[0, 0, float("nan"), 1]),
                    node("graph_attention", params={"heads": 0}),
                    node("graph_attention", params={"heads": True}),
                    node("graph_attention", params={"heads": 40, "merge": "unknown"}),
                    node("graph_attention", params={"heads": 2, "merge": "unknown",
                          "adjacency": "known", "graph_nodes": ["a"], "graph_edges": [[0, 4]]})]
        for item in examples:
            with self.subTest(item=item):
                with self.assertRaisesRegex(ValueError, r"kind|box|heads|adjacency|edge"):
                    self.draw(item)


if __name__ == "__main__":
    unittest.main()
