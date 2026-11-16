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
    input_box=next((e for e in elements if e.get("semantic_id")=="input" and e["type"]=="rect"),None)
    input_label=next((e for e in elements if e.get("semantic_id")=="input_label" and e["type"]=="text"),None)
    if input_box is None:
        raise AssertionError("INPUT_CONTAINER_TOPOLOGY_NODE_MISSING")
    if input_label is None or input_label.get("text")!="Input":
        raise AssertionError("INPUT_LABEL_SEMANTIC_NODE_MISSING")
    poolings=[e for e in elements if e["type"]=="polygon" and e.get("semantic_id") in {"pooling_1","pooling_2"}]
    if len(poolings)!=2:
        raise AssertionError("BOTH_POOLING_MODULES_MUST_USE_SOURCE_LIKE_POLYGONS")
    for pooling in poolings:
        points=pooling["points"]
        if len(points)!=4 or abs(points[1][1]-points[0][1])<.05 or abs(points[2][1]-points[3][1])<.05:
            raise AssertionError("POOLING_QUADRILATERAL_MUST_HAVE_SLOPED_TOP_AND_BOTTOM_EDGES")
    labels=[e.get("text","") for e in elements if e["type"]=="text"]
    if "Frequency" not in labels or not any(e["type"]=="line" and e.get("arrow") and e.get("x1")==e.get("x2") and abs(e["x1"]-8.97)<1e-6 for e in elements):
        raise AssertionError("COMPOSITE_FREQUENCY_DIRECTION_MISSING")
    if labels.count("IR layer")!=2:
        raise AssertionError("COMPOSITE_MUST_PRESERVE_TWO_SOURCE_VISIBLE_IR_LABELS")
    if not any("public abstract uses SR" in label and "unresolved" in label.lower() for label in labels):
        raise AssertionError("COMPOSITE_IR_SR_TERMINOLOGY_BOUNDARY_MISSING")
    if (by_id["el_0120"]["type"] != "graph"
            or len(by_id["el_0120"]["nodes"]) != 12
            or len(by_id["el_0120"]["edges"]) != 8):
        raise AssertionError("INPUT_GRAPH_MUST_HAVE_12_NODES_AND_8_WITHIN_BAND_EDGES")
    node_rows = sorted({round(point[1], 2) for point in by_id["el_0120"]["nodes"]})
    if len(node_rows) != 4:
        raise AssertionError("INPUT_GRAPH_MUST_SHOW_FOUR_BAND_SUBGRAPH_ROWS")
    interband = [e for e in elements if e["type"] == "line" and e.get("dash")
                 and e.get("id") in {f"el_{i:04d}" for i in range(121, 130)}]
    if not interband:
        raise AssertionError("INPUT_GRAPH_SCHEMATIC_INTERBAND_CONNECTIVITY_MISSING")
    if by_id["el_0130"].get("semantic_id") != "class_output":
        raise AssertionError("CLASS_OUTPUT_SEMANTIC_GROUP_MISSING")
    squares = [by_id[f"el_{i:04d}"] for i in range(131, 136)]
    if len(squares) != 5:
        raise AssertionError("FIVE_CLASS_OUTPUT_SQUARES_REQUIRED")
    if squares[1]["fill"] != "#DCA16C" or sum(e["fill"] == "#DCA16C" for e in squares) != 1:
        raise AssertionError("SECOND_CLASS_OUTPUT_MUST_BE_ORANGE")
    class_label=next((e for e in elements if e.get("semantic_id")=="class_output_label" and e["type"]=="text"),None)
    if class_label is None or class_label.get("text")!="fault class":
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
    if sum(s.shape_type == MSO_SHAPE_TYPE.FREEFORM for s in shapes) < 4:
        raise AssertionError("TWO_POOLING_QUADRILATERALS_AND_SHADOWS_MUST_REMAIN_EDITABLE_FREEFORMS")
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
        "input_graph_icon_nodes": 12,
        "input_graph_band_subgraphs": len(node_rows),
        "input_graph_within_band_edges": len(by_id["el_0120"]["edges"]),
        "input_graph_interband_connectivity": "schematic_unspecified",
        "input_graph_interband_connector_count_asserted": False,
        "rendered_schematic_connector_shapes": len(interband),
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
