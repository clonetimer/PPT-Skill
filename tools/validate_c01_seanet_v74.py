#!/usr/bin/env python3
"""Validate the C01-SEANet v7.4 scope, source geometry, accessibility and PPTX."""
from __future__ import annotations

import json
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Inches

from scientific_ir import validate_expected_topology

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "figure_specs/c01/C01_SEANet_graph_level_v74.json"
PPTX_PATH = ROOT / "dist/C01_SEANet_graph_level_v74.pptx"


def _descr(shape):
    for node in shape._element.iter():
        if node.tag.endswith("}cNvPr"):
            return node.get("descr")
    return None


def validate():
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    elements = spec["elements"]
    topology = json.loads((ROOT / "specs/c01_standalone_expected_topology_v76.json").read_text(encoding="utf-8"))
    validate_expected_topology(spec, topology)
    ids = [e["id"] for e in elements]
    if len(ids) != len(set(ids)):
        raise AssertionError("DUPLICATE_FIGURESPEC_ELEMENT_IDS")
    by_id = {e["id"]: e for e in elements}
    if len([e for e in elements if e["type"] == "graph"]) != 2:
        raise AssertionError("INPUT_TOTAL_GRAPH_MUST_HAVE_TWO_SCHEMATIC_SUBGRAPHS")
    if len([e for e in elements if e["type"] == "polygon"]) != 4:
        raise AssertionError("BOTH_POOLING_MODULES_AND_SHADOWS_MUST_BE_FREEFORM_POLYGONS")
    if any(by_id[x]["type"] != "polygon" for x in ("el_0012", "el_0013", "el_0020", "el_0021")):
        raise AssertionError("POOLING_GEOMETRY_NOT_SOURCE_ALIGNED")
    outputs = [e for e in elements if e["id"] in {f"el_{i:04d}" for i in range(59, 64)}]
    if by_id["el_0058"].get("semantic_id") != "class_output":
        raise AssertionError("FIVE_SQUARE_OUTPUT_GROUP_SEMANTIC_TARGET_MISSING")
    if len(outputs) != 5:
        raise AssertionError("FIVE_CLASS_OUTPUT_SQUARES_REQUIRED")
    if sum(e["fill"] == "#DCA16C" for e in outputs) != 1 or outputs[1]["fill"] != "#DCA16C":
        raise AssertionError("SECOND_CLASS_OUTPUT_MUST_BE_HIGHLIGHTED")
    if ("excerpt" not in by_id["el_0043"]["text"].lower()
            or "not the full graphical abstract" not in by_id["el_0043"]["text"].lower()
            or "C01_FBG_construction" not in by_id["el_0043"]["text"]
            or "C01_composite" not in by_id["el_0043"]["text"]):
        raise AssertionError("GRAPH_LEVEL_EXCERPT_SCOPE_NOT_DISCLOSED")
    if "10.1016/j.engappai.2026.115273" not in " ".join(e.get("text", "") for e in elements):
        raise AssertionError("SOURCE_DOI_MISSING")

    prs = Presentation(PPTX_PATH)
    if len(prs.slides) != 1:
        raise AssertionError("C01_SEANET_V74_EXPECTS_ONE_SLIDE")
    slide = prs.slides[0]
    shapes = list(slide.shapes)
    if len(shapes) < 90:
        raise AssertionError("UNEXPECTEDLY_LOW_EDITABLE_OBJECT_COUNT")
    if any(s.shape_type == MSO_SHAPE_TYPE.PICTURE for s in shapes):
        raise AssertionError("RASTERIZED_FIGURE_NOT_ALLOWED")
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
    freeforms = sum(s.shape_type == MSO_SHAPE_TYPE.FREEFORM for s in shapes)
    if freeforms < 4:
        raise AssertionError("POOLING_FREEFORM_SHAPES_MISSING")
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
        "freeform_count": freeforms,
        "alt_text_coverage": 1.0,
        "text_box_count": len(text_shapes),
        "text_overlaps": 0,
        "out_of_bounds": 0,
        "scope": "SEANet graph-level excerpt; C01-FBG construction is separate",
    }


def main():
    result = validate()
    output = ROOT / "dist/C01_SEANet_graph_level_v74_validation.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
