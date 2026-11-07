#!/usr/bin/env python3
"""Re-layout Q03's scientific data at Nature's published two-column example size."""
from __future__ import annotations

import json

from build_quantitative_examples import CONFIG, COLORS, NAMES, load_data, separated_strip_positions
from render_figure_spec import render
from scientific_ir import ROOT, enrich_spec

STEM = "Q03_iris_mean_ci_nature"
WIDTH_MM, HEIGHT_MM = 183, 100
MM_PER_IN = 25.4


def scaled(value, low, high, out_low, out_high):
    return out_low + (value-low)/(high-low)*(out_high-out_low)


def build():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    rows = load_data(config)
    source = json.loads((ROOT / "figure_specs/quant/Q03_iris_mean_ci.json").read_text(encoding="utf-8"))
    chart = next(chart for chart in config["charts"] if chart["id"] == "Q03_iris_mean_ci")
    assert source["chart_contract"] == chart
    assert len(source["computed_values"]) == 3
    elements = []

    def add(kind, **fields):
        elements.append({"type": kind, **fields})

    def text(value, x, y, w, h, size=6.2, bold=False, align="center"):
        add("text", text=str(value), x=x, y=y, w=w, h=h, size=size,
            bold=bold, align=align, color="#1C303A")

    def line(x1, y1, x2, y2, sw=.55):
        add("line", x1=x1, y1=y1, x2=x2, y2=y2, color="#1C303A", sw=sw)

    x0, x1, y0, y1 = .65, 6.88, .32, 3.23
    line(x0, y0, x0, y1)
    line(x0, y1, x1, y1)
    for value in (0, 2, 4, 6, 8):
        y = scaled(value, 0, 8, y1, y0)
        line(x0-.06, y, x0, y)
        text(value, .15, y-.07, .37, .17, 6, align="right")
    text("Petal length (cm)", .54, .05, 1.75, .19, 6.5, True, "left")
    centers = {name: 1.88+index*1.86 for index, name in enumerate(NAMES)}
    for name in NAMES:
        x = centers[name]
        line(x, y1, x, y1+.05)
        text(name.removeprefix("Iris-"), x-.68, y1+.12, 1.36, .18, 6.2)
    text("Species", 2.98, 3.68, 1.40, .18, 6.5, True)
    shapes = {"Iris-setosa": "ellipse", "Iris-versicolor": "rect", "Iris-virginica": "trapezoid"}
    positions = separated_strip_positions(rows, chart, centers, "petal_length_cm", 0, 8, y0, y1)
    for row in rows:
        x, y = positions[row["source_row"]]
        add(shapes[row["species"]], x=x-.020, y=y-.020, w=.040, h=.040,
            fill=COLORS[row["species"]], stroke="#FFFFFF", sw=.25,
            data_row=row["source_row"], data_values={"petal_length_cm": row["petal_length_cm"]})
    for item in source["computed_values"]:
        x = centers[item["species"]] + .70  # Summary lane stays clear of raw observations.
        low = scaled(item["ci95"][0], 0, 8, y1, y0)
        high = scaled(item["ci95"][1], 0, 8, y1, y0)
        mean = scaled(item["mean"], 0, 8, y1, y0)
        line(x, low, x, high, .9)
        line(x-.07, low, x+.07, low, .9)
        line(x-.07, high, x+.07, high, .9)
        add("ellipse", x=x-.052, y=mean-.052, w=.104, h=.104,
            fill="#1C303A", stroke="#FFFFFF", sw=.4)
    target = {
        "journal_name": "Nature", "author_guide_url": "https://research-figure-guide.nature.com/figures/building-and-exporting-figure-panels/",
        "specifications_url": "https://research-figure-guide.nature.com/figures/preparing-figures-our-specifications/",
        "guide_checked_date": "2026-11-07", "figure_class": "main_figure",
        "final_width_mm": WIDTH_MM, "final_height_mm": HEIGHT_MM, "maximum_height_mm": 170,
        "allowed_formats": ["PDF", "SVG", "PPTX"], "preferred_submission_format": "PDF",
        "minimum_text_pt": 5,
        "maximum_text_pt": 7, "raster_resolution_dpi": 450,
        "status": "demonstration_requires_journal_and_expert_review"
    }
    spec = enrich_spec({
        "id": STEM, "version": "7.6.0-dev",
        "canvas": {"width_in": WIDTH_MM/MM_PER_IN, "height_in": HEIGHT_MM/MM_PER_IN},
        "style": {"font": "Arial"}, "publication_target": target,
        "scientific_source_ref": "figure_specs/quant/Q03_iris_mean_ci.json",
        "data_lineage": source["data_lineage"], "chart_contract": chart,
        "computed_values": source["computed_values"], "elements": elements,
    })
    destination = ROOT / f"figure_specs/quant/{STEM}.json"
    destination.write_text(json.dumps(spec, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    render(spec, ROOT / f"examples/{STEM}.svg", ROOT / f"dist/{STEM}.pptx")
    print(f"Built {STEM}: {len(rows)} source flowers at {WIDTH_MM} × {HEIGHT_MM} mm")


if __name__ == "__main__":
    build()
