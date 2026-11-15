#!/usr/bin/env python3
"""Build the source-checked C01 composite FigureSpec and its SVG/PPTX outputs."""
from __future__ import annotations

import json
from pathlib import Path

from render_figure_spec import render
from scientific_ir import enrich_spec

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "figure_specs/c01/C01_composite_defense_slide.json"


def make_spec():
    source = json.loads((ROOT / "figure_specs/c01/C01_FBG_construction_v74.json").read_text(encoding="utf-8"))
    graphs = [e for e in source["elements"] if e["type"] == "graph"]
    ink, muted, line = "#28343C", "#687780", "#AAB5BC"
    elements = []

    def add(kind, **values):
        elements.append({"type": kind, **values})

    def txt(value, x, y, w, h, size=12, bold=False, align="center", color=ink, semantic_id=None):
        value_spec = dict(text=value, x=x, y=y, w=w, h=h, size=size, bold=bold, align=align, color=color)
        if semantic_id:
            value_spec["semantic_id"] = semantic_id
        add("text", **value_spec)

    def box(x, y, w, h, fill="#FFFFFF", stroke=line, radius=0, semantic_id=None):
        values = dict(x=x, y=y, w=w, h=h, fill=fill, stroke=stroke, sw=.8, radius=radius)
        if semantic_id:
            values["semantic_id"] = semantic_id
        add("rect", **values)

    def polygon(points, fill="#F3F7F9", stroke="#7896A6", sw=.8, semantic_id=None):
        values = dict(points=points, fill=fill, stroke=stroke, sw=sw)
        if semantic_id:
            values["semantic_id"] = semantic_id
        add("polygon", **values)

    def arrow(x1, y1, x2, y2, color="#43525B", semantic_link=None):
        values = dict(x1=x1, y1=y1, x2=x2, y2=y2, color=color, sw=1, arrow=True)
        if semantic_link:
            values["semantic_link"] = semantic_link
        add("line", **values)

    def segment(x1, y1, x2, y2, semantic_link):
        add("line", x1=x1, y1=y1, x2=x2, y2=y2,
            color="#43525B", sw=1, semantic_link=semantic_link)

    txt("FBG-SEANet: frequency-band graph construction and diagnosis", .42, .16, 12.5, .45, 22, True, "left")
    box(.42, .82, 8.67, 3.05, stroke="#CFD8DE")
    box(.42, 4.02, 8.67, 2.78, stroke="#CFD8DE")
    box(9.26, .82, 3.64, 5.98, stroke="#CFD8DE")
    txt("01  Graph Construction (Time-Frequency Graph)", .63, 1.02, 8.2, .30, 13.5, True, "left")
    txt("Sensor signals", .65, 1.43, 2.15, .25, 11, True, "left")
    txt("OCF / notch filter", 3.18, 1.43, 1.65, .27, 11, True, semantic_id="ocf")
    txt("Band subgraphs", 5.15, 1.43, 1.58, .27, 11, True, semantic_id="band_group")
    txt("Total graph", 7.31, 1.43, 1.46, .27, 11, True, semantic_id="total_graph")
    txt("band-pass filters", 5.15, 1.72, 1.58, .18, 9.5, color=muted)
    txt("1st · 2nd · 3rd · Nth", 7.31, 1.72, 1.46, .18, 8.8, color=muted)

    colors = ["#668A9C", "#6D9A8E", "#B88E58", "#8A7CA5"]
    labels = ["Sensor 1", "Sensor 2", "Sensor M-1", "Sensor M"]
    bands = ["B₁", "B₂", "B₃", "Bq"]
    box(5.02, 1.94, 1.66, 1.79, stroke="#D5DEE4", semantic_id="band_group")
    box(7.30, 1.94, 1.50, 1.79, stroke="#D5DEE4", semantic_id="total_graph")
    for i, (label, band, color) in enumerate(zip(labels, bands, colors)):
        signal_y = 1.79 + i * .45
        band_y = 1.99 + i * .42
        add("sensor", x=.69, y=signal_y, scale=.73, variant=i, color=color)
        txt(label, 1.08, signal_y+.035, 1.02, .22, 10.5, align="left")
        wave = [(2.02+j*.092, signal_y+.16+(.065 if j%4 == 1 else -.05 if j%4 == 3 else 0)) for j in range(9)]
        add("polyline", points=wave, color=color, sw=1.2)
        arrow(2.87, signal_y+.15, 3.18, signal_y+.15)
        txt(band, 5.12, band_y+.035, .35, .22, 11, True, color=color, semantic_id=f"band_{i+1}")
        graph = dict(graphs[i])
        graph.update(x=5.51, y=band_y-.005, w=1.12, h=.31, semantic_id=f"band_{i+1}")
        elements.append(graph)
        arrow(6.67, band_y+.15, 7.39, band_y+.15, semantic_link=f"band_{i+1}__total_graph")
        layer = dict(graphs[i])
        layer.update(x=7.43, y=band_y-.005, w=1.23, h=.31, semantic_id="total_graph")
        elements.append(layer)
    box(3.19, 1.87, 1.56, 1.67, fill="#F7F9FA", stroke="#AAB5BC", radius=.05, semantic_id="ocf")
    txt("Notch filter", 3.33, 2.13, 1.27, .28, 11, True)
    txt("Operational\ncomponent removed", 3.31, 2.65, 1.32, .55, 10)
    txt("Fault cues clearer", 3.28, 3.25, 1.38, .20, 9.5, color="#43525B")
    arrow(4.75, 2.72, 5.05, 2.72, semantic_link="ocf__band_group")
    for i in range(3):
        top = 2.29 + i * .42
        for x in (7.75, 8.12, 8.46):
            add("line", x1=x, y1=top, x2=x+.04, y2=top+.10,
                color="#43525B", sw=1.1, dash=True)
    txt("Inter-band links", 6.72, 3.63, 1.35, .16, 8.5, color=muted)
    arrow(8.97, 2.02, 8.97, 3.56)
    txt("Frequency", 8.32, 3.63, .56, .16, 7.8, align="right", color=muted)
    segment(8.05, 3.73, 8.05, 3.94, "total_graph__input")
    segment(8.05, 3.94, .55, 3.94, "total_graph__input")
    segment(.55, 3.94, .55, 5.43, "total_graph__input")
    arrow(.55, 5.43, .68, 5.43, semantic_link="total_graph__input")

    txt("02  Graph-level fault diagnosis framework", .63, 4.19, 8.2, .30, 13.5, True, "left")
    # Separate geometry for this narrow panel keeps the scientific sequence readable.
    stages = [("Input", .70, 1.00), ("GCN", 1.94, .79), ("pooling", 2.95, .91),
              ("GCN", 4.09, .79), ("pooling", 5.10, .91), ("IR layer", 6.25, .90)]
    cy = 5.17
    stage_nodes = ["input", "gcn_1", "pooling_1", "gcn_2", "pooling_2", "sr_main"]
    for j, (label, x, width) in enumerate(stages):
        if j in (2, 4):
            front = [[x, cy], [x+width, cy+.10], [x+width, cy+.51], [x, cy+.41]]
            shadow = [[px+.05, py+.05] for px, py in front]
            polygon(shadow, fill="#E4EAED", stroke="#E4EAED", sw=.3)
            polygon(front, fill="#F1F4F5", stroke="#7896A6", sw=.9,
                    semantic_id=stage_nodes[j])
            txt(label, x+.05, cy+.13, width-.10, .25, 9.8, True,
                semantic_id=stage_nodes[j])
        else:
            box(x, cy, width, .51, fill="#F3F7F9" if j else "#EAF2F5",
                stroke="#7896A6", radius=.035, semantic_id=stage_nodes[j])
            txt(label, x+.035, cy+.12, width-.07, .27,
                9.8 if j == 5 else 10.5, True, semantic_id=stage_nodes[j])
        if j:
            prev_x, prev_w = stages[j-1][1], stages[j-1][2]
            arrow(prev_x+prev_w+.025, cy+.255, x-.035, cy+.255,
                  semantic_link=f"{stage_nodes[j-1]}__{stage_nodes[j]}")
    add("ellipse", x=7.24, y=5.20, w=.45, h=.45, fill="#FFFFFF", stroke="#43525B", sw=1)
    txt("+", 7.28, 5.25, .37, .33, 15, True, semantic_id="sum")
    arrow(7.17, 5.43, 7.21, 5.43, semantic_link="sr_main__sum")
    box(7.88, 5.17, .70, .51, fill="#F3F7F9", stroke="#7896A6", radius=.035)
    txt("Dense", 7.91, 5.29, .64, .27, 10, True, semantic_id="dense")
    arrow(7.71, 5.43, 7.85, 5.43, semantic_link="sum__dense")
    arrow(8.61, 5.43, 8.90, 5.43, semantic_link="dense__class_output")
    segment(1.18, 5.70, 1.18, 6.24, "input__ea")
    box(1.28, 6.03, 2.62, .48, fill="#F7F5F9", stroke="#8A7CA5", radius=.035)
    txt("Energy-assisted module", 1.39, 6.14, 2.41, .26, 10.5, True, semantic_id="ea")
    arrow(1.21, 6.27, 1.25, 6.27, semantic_link="input__ea")
    arrow(2.32, 6.00, 2.32, 5.71, semantic_link="ea__gcn_1")
    box(5.12, 6.03, .92, .48, fill="#F7F5F9", stroke="#8A7CA5", radius=.035)
    txt("IR layer", 5.17, 6.14, .82, .26, 9.5, True, semantic_id="sr_ea")
    segment(3.84, 5.67, 4.00, 5.82, "pooling_1__sr_ea")
    segment(4.00, 5.82, 4.00, 6.27, "pooling_1__sr_ea")
    arrow(4.00, 6.27, 5.09, 6.27, semantic_link="pooling_1__sr_ea")
    segment(6.06, 6.27, 7.46, 6.27, "sr_ea__sum")
    arrow(7.46, 6.27, 7.46, 5.68, semantic_link="sr_ea__sum")

    txt("Reading guide", 9.52, 1.04, 3.06, .34, 15, True, "left")
    for y, n, title, body in [
        (1.58, "1", "Filter", "Remove operational components from sensor signals."),
        (2.65, "2", "Construct", "Band-pass filters form 1st, 2nd, 3rd … Nth subgraphs; these connect into the total graph."),
        (3.72, "3", "Diagnose", "EA feeds first GCN; first pooling branches to two readout paths."),
    ]:
        box(9.54, y, .37, .37, fill="#EAF2F5", stroke="#7896A6", radius=.18)
        txt(n, 9.58, y+.045, .29, .27, 10.5, True)
        txt(title, 10.03, y-.02, 2.42, .28, 11.5, True, "left")
        txt(body, 10.03, y+.34, 2.52, .66, 9.2 if n == "2" else 10.5, align="left")
    txt("Evidence boundary", 9.52, 4.89, 3.00, .27, 11.5, True, "left")
    txt("Graph nodes/edges are schematic. The author-lab figure appears to label both readouts IR; the public abstract uses SR. The exact label remains unresolved.",
        9.52, 5.22, 3.00, .78, 9.0, align="left")
    txt("Lee et al., EAAI 179 (2026), 115273\nDOI: 10.1016/j.engappai.2026.115273", 9.52, 6.12, 3.04, .47, 9.5, align="left", color=muted)
    txt("Author-lab source-visible redraw · schematic graph adjacency · readout label IR/SR discrepancy unresolved", .65, 6.96, 12.14, .23, 9.2, align="left", color=muted)
    semantic_edges = [["input", "gcn_1"], ["gcn_1", "pooling_1"],
                      ["pooling_1", "gcn_2"], ["gcn_2", "pooling_2"],
                      ["pooling_2", "sr_main"], ["sr_main", "sum"],
                      ["input", "ea"], ["ea", "gcn_1"],
                      ["pooling_1", "sr_ea"], ["sr_ea", "sum"], ["sum", "dense"]]
    semantic_edges += [["ocf", "band_group"], ["total_graph", "input"]]
    semantic_edges += [[f"band_{i}", "total_graph"] for i in range(1, 5)]
    return enrich_spec({"version": "7.4.0", "id": "C01_composite_defense_slide",
            "canvas": {"width_in": 13.333, "height_in": 7.5},
            "style": {"font": "Times New Roman"},
            "evidence_status": "source-visible structural redraw with schematic substitutions",
            "source": "DOI:10.1016/j.engappai.2026.115273",
            "semantic_edges": semantic_edges, "elements": elements})


def main():
    spec = make_spec()
    SPEC.parent.mkdir(parents=True, exist_ok=True)
    SPEC.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    render(spec, ROOT / "examples/C01_composite_defense_slide_v74.svg",
           ROOT / "dist/C01_composite_defense_slide_v74.pptx")
    print(f"Built {SPEC.name}: {len(spec['elements'])} elements")


if __name__ == "__main__":
    main()
