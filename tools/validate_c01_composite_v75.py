#!/usr/bin/env python3
"""Validate C01 composite v7.5 source topology, class outputs and accessibility."""
from __future__ import annotations

import json
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Inches

from scientific_ir import validate_expected_topology

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "figure_specs/c01/C01_composite_defense_slide_v75.json"
TOPOLOGY_PATH = ROOT / "specs/c01_composite_expected_topology_v75.json"
PPTX_PATH = ROOT / "dist/C01_composite_defense_slide_v75.pptx"


def _descr(shape):
    for node in shape._element.iter():
        if node.tag.endswith("}cNvPr"):
            return node.get("descr")
    return None


def validate():
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    topology = json.loads(TOPOLOGY_PATH.read_text(encoding="utf-8"))
    validate_expected_topology(spec, topology)
    elements = spec["elements"]
    ids = [e["id"] for e in elements]
    if len(ids) != len(set(ids)):
        raise AssertionError("DUPLICATE_COMPOSITE_V75_ELEMENT_IDS")

    by_id = {e["id"]: e for e in elements}
    if by_id["el_0120"]["type"] != "graph" or len(by_id["el_0120"]["nodes"]) != 6:
        raise AssertionError("INPUT_GRAPH_ICON_MISSING")
    interband = [e for e in elements if e["type"] == "line" and e.get("dash")
                 and e.get("id") in {"el_0121", "el_0122", "el_0123"}]
    if len(interband) != 3:
        raise AssertionError("INPUT_GRAPH_INTER_GROUP_LINKS_MISSING")
    if by_id["el_0124"].get("semantic_id") != "class_output":
        raise AssertionError("CLASS_OUTPUT_SEMANTIC_GROUP_MISSING")
    squares = [by_id[f"el_{i:04d}"] for i in range(125, 130)]
    if len(squares) != 5:
        raise AssertionError("FIVE_CLASS_OUTPUT_SQUARES_REQUIRED")
    if squares[1]["fill"] != "#DCA16C" or sum(e["fill"] == "#DCA16C" for e in squares) != 1:
        raise AssertionError("SECOND_CLASS_OUTPUT_MUST_BE_ORANGE")
    if by_id["el_0090"].get("text") != "fault class":
        raise AssertionError("FAULT_CLASS_LABEL_MISSING")
    if ("dense", "class_output") not in {tuple(x) for x in spec["semantic_edges"]}:
        raise AssertionError("DENSE_TO_CLASS_OUTPUT_EDGE_MISSING")

    prs = Presentation(PPTX_PATH)
    if len(prs.slides) != 1:
        raise AssertionError("C01_COMPOSITE_V75_EXPECTS_ONE_SLIDE")
    slide = prs.slides[0]
    shapes = list(slide.shapes)
    if len(shapes) < 250:
        raise AssertionError("UNEXPECTEDLY_LOW_EDITABLE_OBJECT_COUNT")
    if any(s.shape_type == MSO_SHAPE_TYPE.PICTURE for s in shapes):
        raise AssertionError("RASTERIZED_COMPOSITE_NOT_ALLOWED")
    missing_alt = [s.name for s in shapes if not (_descr(s) or "").strip()]
    if missing_alt:
        raise AssertionError("MISSING_ALT_TEXT:" + ",".join(missing_alt))
    oob = [
        s.name for s in shapes
        if s.left < 0 or s.top < 0
        or s.left + s.width > prs.slide_width
        or s.top + s.height > prs.slide_height
    ]
    if oob:
        raise AssertionError("OBJECTS_OUT_OF_BOUNDS:" + ",".join(oob))
    text_shapes = [s for s in shapes if s.has_text_frame and s.text.strip()]
    overlaps = []
    for i, a in enumerate(text_shapes):
        for b in text_shapes[i + 1:]:
            iw = max(0, min(a.left + a.width, b.left + b.width) - max(a.left, b.left))
            ih = max(0, min(a.top + a.height, b.top + b.height) - max(a.top, b.top))
            if iw > Inches(0.03) and ih > Inches(0.03):
                overlaps.append((a.name, b.name))
    if overlaps:
        raise AssertionError("TEXT_BOX_OVERLAPS:" + repr(overlaps))
    return {
        "status": "PASS",
        "spec_elements": len(elements),
        "pptx_shapes": len(shapes),
        "picture_count": 0,
        "alt_text_coverage": 1.0,
        "text_box_count": len(text_shapes),
        "text_overlaps": 0,
        "out_of_bounds": 0,
        "input_graph_icon_nodes": 6,
        "input_graph_inter_group_links": 3,
        "class_output_squares": 5,
        "orange_highlight_index": 2,
        "critical_routes": len(topology["critical_edges"]),
    }


def main():
    result = validate()
    output = ROOT / "dist/C01_composite_defense_slide_v75_validation.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
