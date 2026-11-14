#!/usr/bin/env python3
"""Build the C01 two-panel composite v7.5 with source-critical class outputs."""
from __future__ import annotations

import copy
import json
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from build_c01_v74 import make_spec
from render_figure_spec import render

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "figure_specs/c01/C01_composite_defense_slide_v75.json"
SVG = ROOT / "examples/C01_composite_defense_slide_v75.svg"
PPTX = ROOT / "dist/C01_composite_defense_slide_v75.pptx"

PANEL_ALT = (
    "Complete two-panel FBG-SEANet structural redraw. The upper panel shows sensor signals, "
    "notch filtering, frequency-band subgraphs and their connected total graph. The total graph "
    "feeds the lower SEANet diagnosis panel. The lower panel shows the GCN/pooling main route, "
    "energy-assisted branch, two SR readouts, summation, Dense and five vertically stacked class "
    "outputs with the second highlighted. Sensor glyphs and graph adjacency are schematic."
)


def add_input_graph_icon(spec: dict) -> None:
    elements = spec["elements"]
    label = next(e for e in elements if e.get("id") == "el_0067")
    label.update(x=0.75, y=5.29, w=0.43, h=0.27, align="left")
    graph = {
        "type": "graph", "x": 1.23, "y": 5.25, "w": 0.36, "h": 0.31,
        "nodes": [[0.08, 0.20], [0.50, 0.05], [0.92, 0.20],
                  [0.15, 0.80], [0.50, 0.95], [0.85, 0.80]],
        "edges": [[0, 1], [1, 2], [3, 4], [4, 5]],
        "fill": "#7896A6", "r": 0.025, "edge": "#43525B", "sw": 0.55,
        "id": "el_0120", "semantic_id": "input_graph_schematic",
        "semantic_role": "schematic_graph", "evidence_ref": "source_1",
    }
    label_index = elements.index(label)
    elements.insert(label_index + 1, graph)
    # Dashed inter-subgraph links echo the source's connected band-group structure.
    for i, (a, b) in enumerate(((0, 3), (1, 4), (2, 5)), start=0):
        x1 = graph["x"] + graph["nodes"][a][0] * graph["w"]
        y1 = graph["y"] + graph["nodes"][a][1] * graph["h"]
        x2 = graph["x"] + graph["nodes"][b][0] * graph["w"]
        y2 = graph["y"] + graph["nodes"][b][1] * graph["h"]
        elements.insert(label_index + 2 + i, {
            "type": "line", "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "color": "#7896A6", "sw": 0.55, "dash": True,
            "id": f"el_{String(121+i).zfill(4)}",
            "semantic_role": "connector", "evidence_ref": "source_1",
        })


def add_class_output(spec: dict) -> None:
    elements = spec["elements"]
    dense = next(e for e in elements if e.get("semantic_id") == "dense")
    line = next(e for e in elements if e.get("id") == "el_0089")
    label = next(e for e in elements if e.get("id") == "el_0090")
    group = {
        "type": "rect", "x": 8.89, "y": 5.00, "w": 0.15, "h": 0.85,
        "fill": "#FFFFFF", "stroke": "#FFFFFF", "sw": 0.1,
        "radius": 0, "dash": False, "id": "el_0124",
        "semantic_id": "class_output", "semantic_role": "scientific_object",
        "evidence_ref": "source_1",
    }
    # The semantic group is the endpoint of Dense -> class output; visible squares remain independent.
    line["semantic_link"] = "dense__class_output"
    label.update(text="fault class", x=8.58, y=5.91, w=0.68, h=0.21,
                 size=9.5, align="center", color="#687780",
                 semantic_id="class_output_label", semantic_role="scientific_label")
    index = elements.index(line)
    elements.insert(index, group)
    squares = []
    for i in range(5):
        square = {
            "type": "rect", "x": 8.90, "y": 5.02 + i * 0.17, "w": 0.13, "h": 0.13,
            "fill": "#DCA16C" if i == 1 else "#FFFFFF",
            "stroke": "#43525B", "sw": 0.65, "radius": 0, "dash": False,
            "id": f"el_{String(125+i).zfill(4)}",
            "semantic_role": "layout_shape", "evidence_ref": "source_1",
        }
        squares.append(square)
    label_index = elements.index(label)
    elements[label_index:label_index] = squares
    spec["semantic_edges"] = [*spec["semantic_edges"], ["dense", "class_output"]]


def _c_nv_pr(shape):
    for node in shape._element.iter():
        if node.tag.endswith("}cNvPr"):
            return node
    return None


def annotate_accessibility(path: Path) -> dict:
    prs = Presentation(path)
    if len(prs.slides) != 1:
        raise ValueError("C01_COMPOSITE_V75_EXPECTS_ONE_SLIDE")
    slide = prs.slides[0]
    missing = []
    output_squares = sorted(
        [s for s in slide.shapes if s.left > int(8.85 * 914400)
         and abs(s.width - int(0.13 * 914400)) < 500
         and abs(s.height - int(0.13 * 914400)) < 500],
        key=lambda s: s.top,
    )
    if len(output_squares) != 5:
        raise ValueError("C01_COMPOSITE_V75_EXPECTS_FIVE_OUTPUT_SQUARES")
    for index, shape in enumerate(slide.shapes):
        shape.name = f"C01_composite_v75_obj_{index:03d}"
        if shape in output_squares:
            square_index = output_squares.index(shape) + 1
            alt = f"Fault-class output indicator {square_index} of 5" + (
                "; second class is highlighted orange" if square_index == 2 else ""
            )
        elif shape.has_text_frame and shape.text.strip():
            alt = "Text label: " + shape.text.replace("\\n", "; ")
        elif shape.shape_type == MSO_SHAPE_TYPE.LINE:
            alt = "Editable connector in the complete two-panel FBG-SEANet method overview."
        elif shape.width > 10 * 914400 and shape.height > 5 * 914400:
            alt = PANEL_ALT
        elif shape.left > int(8.85 * 914400) and abs(shape.width - int(0.15 * 914400)) < 500:
            alt = "Semantic grouping boundary for the five independent class-output squares."
        elif shape.left > int(1.2 * 914400) and shape.top > int(5.2 * 914400) and shape.width < int(0.5 * 914400):
            alt = "Schematic input graph icon with two node groups and dashed inter-group links."
        else:
            alt = "Editable vector object in the complete two-panel FBG-SEANet method overview."
        node = _c_nv_pr(shape)
        if node is None:
            missing.append(shape.name)
        else:
            node.set("descr", alt)
    if missing:
        raise ValueError("ALT_TEXT_METADATA_MISSING:" + ",".join(missing))
    for shape in slide.shapes:
        if shape.has_text_frame and shape.text.strip() == "FBG-SEANet: frequency-band graph construction and diagnosis":
            node = _c_nv_pr(shape)
            if node is not None:
                node.set("descr", PANEL_ALT)
    prs.save(path)
    return {
        "shape_count": len(slide.shapes),
        "alt_text_count": len(slide.shapes),
        "alt_text_coverage": 1.0,
        "input_graph_icon": "schematic two-group graph with dashed inter-group links",
        "class_output_squares": 5,
        "orange_highlight_index": 2,
        "panel_description": PANEL_ALT,
    }


def build_spec() -> dict:
    spec = copy.deepcopy(make_spec())
    add_input_graph_icon(spec)
    add_class_output(spec)
    spec["id"] = "C01_composite_defense_slide_v75"
    spec["version"] = "7.5.0"
    spec["evidence_status"] = "source-visible two-panel structural redraw with schematic substitutions"
    return spec


def main():
    spec = build_spec()
    SPEC.parent.mkdir(parents=True, exist_ok=True)
    SVG.parent.mkdir(parents=True, exist_ok=True)
    PPTX.parent.mkdir(parents=True, exist_ok=True)
    SPEC.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
    render(spec, SVG, PPTX)
    accessibility = annotate_accessibility(PPTX)
    report = {
        "spec": str(SPEC.relative_to(ROOT)),
        "svg": str(SVG.relative_to(ROOT)),
        "pptx": str(PPTX.relative_to(ROOT)),
        "element_count": len(spec["elements"]),
        "semantic_edges": len(spec["semantic_edges"]),
        "accessibility": accessibility,
    }
    report_path = ROOT / "dist/C01_composite_defense_slide_v75_build.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
