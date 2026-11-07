#!/usr/bin/env python3
"""Build a second-data-source scatter example from UCI Wine without Iris assumptions."""
from __future__ import annotations

import json
from collections import Counter

from build_quantitative_examples import Figure, scaled, separated_scatter_positions
from chart_data import load_rows
from render_figure_spec import render
from scientific_ir import ROOT, validate_spec

CONFIG = ROOT / "specs/wine_charts_v76.json"
COLORS = {"1": "#376F75", "2": "#A45C32", "3": "#755A91"}
SHAPES = {"1": "ellipse", "2": "rect", "3": "trapezoid"}


def build() -> dict:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    chart, = config["charts"]
    meta = config["data"]
    rows = load_rows(meta)
    assert Counter(row["cultivar"] for row in rows) == {"1": 59, "2": 71, "3": 48}
    assert chart["sample_size"] == len(rows)
    for direction in ("x", "y"):
        axis = chart["axes"][direction]
        assert axis["field"] == chart[direction]
        assert axis["unit"] == meta["columns"][chart[direction]]["unit"]
        low, high = axis["domain"]
        assert low < high and all(low <= row[chart[direction]] <= high for row in rows)

    fig = Figure(chart, meta, "specs/wine_charts_v76.json")
    fig.text("Wine chemistry: raw measurements by coded cultivar", .52, .19, 12.2, .50,
             22, True, "left")
    fig.text("Each mark is one sample; small offsets separate overlaps. The source does not report units for these fields.",
             .70, 6.50, 11.9, .35, 11, align="left")
    fig.text("UCI Wine · 178 samples · DOI 10.24432/C5PC7J · CC BY 4.0", .70, 7.02,
             11.9, .23, 9.5, align="left", color="#65737C")
    x0, x1, y0, y1 = 1.28, 9.80, 1.30, 5.66
    xlow, xhigh = chart["axes"]["x"]["domain"]
    ylow, yhigh = chart["axes"]["y"]["domain"]
    fig.axes(x0, y0, x1, y1, "Alcohol (unit unreported)", "Color intensity (unit unreported)",
             [(scaled(v, xlow, xhigh, x0, x1), str(v)) for v in range(10, 16)],
             [(scaled(v, ylow, yhigh, y1, y0), str(v)) for v in range(0, 15, 2)])
    positions = separated_scatter_positions(rows, chart)
    for row in rows:
        x, y = positions[row["source_row"]]
        fig.point(x, y, COLORS[row["cultivar"]], row,
                  {"alcohol": row["alcohol"], "color_intensity": row["color_intensity"],
                   "cultivar": row["cultivar"]}, r=.025, shape=SHAPES[row["cultivar"]])
    for index, code in enumerate(COLORS):
        y = 1.90 + index*.48
        fig.add(SHAPES[code], x=10.49, y=y, w=.15, h=.15, fill=COLORS[code],
                stroke="#FFFFFF", sw=.5)
        fig.text(f"Cultivar {code}", 10.76, y-.03, 1.68, .25, 11.5, align="left")
    spec = fig.finish()
    validate_spec(spec)
    return spec


def main() -> None:
    spec = build()
    stem = spec["id"]
    (ROOT / "figure_specs/quant" / f"{stem}.json").write_text(
        json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    render(spec, ROOT / f"examples/{stem}.svg", ROOT / f"dist/{stem}.pptx")
    print(f"Built {stem}: {len(spec['elements'])} elements")


if __name__ == "__main__":
    main()
