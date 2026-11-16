#!/usr/bin/env python3
"""Build the V8 C01 Image-first source FigureSpec from the V7.4 source redraw."""
from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "figure_specs/c01/C01_composite_defense_slide.json"
OUTPUT = ROOT / "figure_specs/c01/C01_composite_defense_slide_image_first_v8.json"


def _text(spec: dict, element_id: str) -> dict:
    return next(e for e in spec["elements"] if e.get("id") == element_id)


def _add_input_graph(spec: dict) -> None:
    elements = spec["elements"]
    input_box = _text(spec, "el_0066")
    input_box.update(semantic_id="input", semantic_role="scientific_object")
    label = _text(spec, "el_0067")
    label.update(x=0.75, y=5.29, w=0.43, h=0.27, align="left",
                 semantic_id="input_label", semantic_role="scientific_label")

    graph = {
        "type": "graph",
        "x": 1.23, "y": 5.25, "w": 0.36, "h": 0.31,
        "nodes": [
            [0.08, 0.08], [0.50, 0.08], [0.92, 0.08],
            [0.08, 0.36], [0.50, 0.36], [0.92, 0.36],
            [0.08, 0.64], [0.50, 0.64], [0.92, 0.64],
            [0.08, 0.92], [0.50, 0.92], [0.92, 0.92],
        ],
        "edges": [
            [0, 1], [1, 2], [3, 4], [4, 5],
            [6, 7], [7, 8], [9, 10], [10, 11],
        ],
        "fill": "#7896A6", "r": 0.02, "edge": "#43525B", "sw": 0.5,
        "id": "el_0120", "semantic_id": "input_graph_schematic",
        "semantic_role": "schematic_graph", "evidence_ref": "source_1",
    }

    # A few sparse dashed links make the cross-row relationship legible.
    # Their count is deliberately not encoded as a scientific or topology claim.
    illustrative_pairs = [(0, 3), (2, 5), (4, 7), (6, 9), (8, 11)]
    connectors = []
    for index, (source, target) in enumerate(illustrative_pairs, start=121):
        a, b = graph["nodes"][source], graph["nodes"][target]
        connectors.append({
            "type": "line",
            "x1": graph["x"] + a[0] * graph["w"],
            "y1": graph["y"] + a[1] * graph["h"],
            "x2": graph["x"] + b[0] * graph["w"],
            "y2": graph["y"] + b[1] * graph["h"],
            "color": "#7896A6", "sw": 0.55, "dash": True,
            "id": f"el_{index:04d}",
            "semantic_role": "schematic_connector", "evidence_ref": "source_1",
        })
    label_index = elements.index(label)
    elements[label_index + 1:label_index + 1] = [*connectors, graph]


def _add_class_outputs(spec: dict) -> None:
    elements = spec["elements"]
    class_label = _text(spec, "el_0090")
    class_label.update(text="fault class", x=8.48, y=6.08, w=0.68, h=0.2, size=9.5)
    class_label["semantic_id"] = "class_output_label"
    group = {
        "type": "rect", "x": 8.89, "y": 5.0, "w": 0.34, "h": 0.94,
        "fill": "#FFFFFF", "stroke": "#FFFFFF", "sw": 0.1, "radius": 0,
        "id": "el_0130", "semantic_id": "class_output",
        "semantic_role": "scientific_object", "evidence_ref": "source_1",
    }
    elements.append(group)
    for index in range(5):
        y = 5.02 + index * 0.18
        elements.append({
            "type": "rect", "x": 8.90, "y": y, "w": 0.15, "h": 0.15,
            "fill": "#DCA16C" if index == 1 else "#FFFFFF",
            "stroke": "#43525B", "sw": 0.65, "radius": 0,
            "id": f"el_{131 + index:04d}",
            "semantic_role": "illustrative_class_output", "evidence_ref": "source_1",
        })
        elements.append({
            "type": "text", "text": ["C₁", "C₂", "C₃", "C₄", "C₅"][index],
            "x": 9.07, "y": y - 0.005, "w": 0.18, "h": 0.16,
            "size": 9.5, "bold": index == 1, "align": "left", "color": "#28343C",
            "id": f"el_{136 + index:04d}",
            "semantic_role": "illustrative_class_label", "evidence_ref": "source_1",
        })
    if ["dense", "class_output"] not in spec["semantic_edges"]:
        spec["semantic_edges"].append(["dense", "class_output"])
    class_route = next(e for e in elements if e.get("id") == "el_0089")
    class_route.update(semantic_link="dense__class_output", semantic_role="connector")


def build_spec(source_spec: dict | None = None) -> dict:
    if source_spec is None:
        source_spec = json.loads(SOURCE.read_text(encoding="utf-8"))
    spec = copy.deepcopy(source_spec)
    spec["id"] = "C01_composite_defense_slide_image_first_v8"
    spec["version"] = "8.0.0-dev"
    spec["evidence_status"] = (
        "source-visible process redraw with variable band count and explicitly schematic graph connectivity"
    )

    for element in spec["elements"]:
        if element.get("type") == "graph" and element.get("semantic_id") in {
            "band_1", "band_2", "band_3", "band_4", "total_graph"
        }:
            # Three nodes per displayed subgraph/layer are a visual-consistency motif,
            # not a recovered numerical adjacency topology.
            element["nodes"] = [[0.08, 0.5], [0.5, 0.12], [0.92, 0.5]]
            element["edges"] = [[0, 1], [1, 2]]
        if element.get("type") == "text" and element.get("semantic_id") == "band_4":
            element["text"] = "Bₙ"
        if element.get("type") == "text" and element.get("semantic_id") in {"sr_main", "sr_ea"}:
            element["text"] = "IR layer"
        if element.get("id") == "el_0010":
            element.update(text="B₁, B₂, B₃, …, Bₙ", x=5.02, y=1.72, w=2.45,
                           h=0.2, size=9.5, align="center")
        if element.get("id") == "el_0011":
            element.update(text="N variable", x=7.5, y=1.72, w=1.3,
                           h=0.2, size=9.5, align="center")
        if element.get("id") == "el_0060":
            element.update(text="Schematic links only", size=9.5)
        if element.get("id") == "el_0115":
            element["text"] = "EA feeds the first GCN; first pooling branches to two readout paths."
        if element.get("id") == "el_0117":
            element.update(
                text=(
                    "N varies; visible bands are examples. Graph links are schematic; "
                    "no exact link count or numerical adjacency is asserted. Five outputs "
                    "are illustrative, not a fixed class count. Author-lab labels readouts "
                    "IR; public abstract uses SR; unresolved."
                ),
                x=9.52, y=5.20, w=3.00, h=0.96, size=9.5,
            )
        if element.get("id") == "el_0118":
            element.update(y=6.24, h=0.38, size=9.5)
        if element.get("id") == "el_0119":
            element["text"] = "Source-visible redraw · schematic connectivity · variable N"

    # Keep only a sparse illustrative subset of the pre-existing upper-panel dashed links.
    upper_dash = [
        e for e in spec["elements"]
        if e.get("type") == "line" and e.get("dash") is True
        and 7.6 <= e.get("x1", -1) <= 8.7 and 2.2 <= e.get("y1", -1) <= 3.3
    ]
    keep_ids = {e["id"] for index, e in enumerate(upper_dash) if index in {0, 2, 4, 6, 8}}
    spec["elements"] = [
        e for e in spec["elements"]
        if e not in upper_dash or e.get("id") in keep_ids
    ]

    _add_input_graph(spec)
    _add_class_outputs(spec)
    spec["figure_contract"] = {
        "claim": "The slide explains frequency-band graph construction and the two-branch graph-level diagnosis path.",
        "archetype": "schematic_led_composite",
        "output_mode": "presentation",
        "unverified": [
            "Numerical adjacency matrix",
            "Exact number of dashed inter-band or inter-row links",
            "Fixed frequency-band count",
            "Fixed class-output count",
            "Pixel-level source-image match",
        ],
    }
    spec["image_first_v8_contract"] = {
        "band_count": "N_variable",
        "three_node_band_icons": "schematic_consistency_motif_only",
        "input_graph": "12_nodes_4_by_3_source_visible_schematic",
        "cross_band_edges": "schematic_unspecified",
        "class_outputs": "five_output_illustrative_example",
    }
    return spec


def main() -> None:
    spec = build_spec()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "output": str(OUTPUT.relative_to(ROOT)),
        "graph_objects": sum(e.get("type") == "graph" for e in spec["elements"]),
        "band_labels": [
            e["text"] for e in spec["elements"]
            if e.get("type") == "text" and e.get("semantic_id") in {
                "band_1", "band_2", "band_3", "band_4"
            }
        ],
        "input_nodes": len(next(
            e["nodes"] for e in spec["elements"] if e.get("semantic_id") == "input_graph_schematic"
        )),
        "class_outputs": sum(
            e.get("semantic_role") == "illustrative_class_output" for e in spec["elements"]
        ),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
