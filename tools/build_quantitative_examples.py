#!/usr/bin/env python3
"""Build four data-linked SVG and native-PPTX chart examples from UCI Iris."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from render_figure_spec import render
from scientific_ir import ROOT, enrich_spec

CONFIG = ROOT / "specs/iris_charts_v76.json"
SPEC_DIR = ROOT / "figure_specs/quant"
COLORS = {"Iris-setosa": "#376F75", "Iris-versicolor": "#A45C32", "Iris-virginica": "#755A91"}
NAMES = list(COLORS)
TITLES = {"Q01_iris_scatter": "Petal dimensions separate iris species",
          "Q02_iris_strip": "Sepal length distributions overlap",
          "Q03_iris_mean_ci": "Mean petal length with bootstrap intervals",
          "Q04_iris_confusion": "Leave-one-out 1-NN baseline: actual vs predicted",
          "Q05_iris_ablation": "A paired feature-set comparison",
          "Q06_iris_trend_interval": "Within-setosa trend with raw points and intervals"}


def load_data(config):
    meta = config["data"]
    path = ROOT / meta["file"]
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == meta["sha256"], (digest, meta["sha256"])
    columns = list(meta["columns"])
    rows = []
    with path.open(encoding="utf-8", newline="") as stream:
        for row_number, raw in enumerate(csv.reader(stream), 1):
            if not raw:
                continue
            assert len(raw) == 5, row_number
            row = {name: (float(raw[i]) if meta["columns"][name]["type"] == "number" else raw[i])
                   for name, i in ((name, details["source_position"]) for name, details in meta["columns"].items())}
            assert all(math.isfinite(row[name]) for name in columns if isinstance(row[name], float))
            assert row["species"] in COLORS
            row["source_row"] = row_number
            rows.append(row)
    assert len(rows) == meta["row_count"] == 150
    assert Counter(row["species"] for row in rows) == {name: 50 for name in NAMES}
    return rows


class Figure:
    def __init__(self, chart, meta):
        self.chart, self.meta = chart, meta
        self.elements = []
        self.values = []

    def add(self, kind, **kwargs):
        self.elements.append({"type": kind, **kwargs})

    def text(self, value, x, y, w, h, size=12, bold=False, align="center", color="#26343C"):
        self.add("text", text=str(value), x=x, y=y, w=w, h=h, size=size,
                 bold=bold, align=align, color=color)

    def line(self, x1, y1, x2, y2, color="#5F707B", sw=1):
        self.add("line", x1=x1, y1=y1, x2=x2, y2=y2, color=color, sw=sw)

    def point(self, x, y, color, row, values, r=.043):
        shape = {"Iris-setosa": "ellipse", "Iris-versicolor": "rect",
                 "Iris-virginica": "trapezoid"}[row["species"]]
        self.add(shape, x=x-r, y=y-r, w=2*r, h=2*r, fill=color,
                 stroke="#FFFFFF", sw=.55, data_row=row["source_row"], data_values=values)

    def setup(self):
        self.text(TITLES[self.chart["id"]], .52, .19, 12.2, .50, 22, True, "left")
        self.text(self.chart["caption"], .70, 6.46, 11.9, .37, 11, align="left")
        self.text(f"UCI Iris · {self.chart['sample_size']} flowers · DOI 10.24432/C56C76 · CC BY 4.0", .70, 7.02, 11.9, .23, 9.5, align="left", color="#65737C")

    def axes(self, x0, y0, x1, y1, xlabel, ylabel, xticks, yticks):
        self.line(x0, y1, x1, y1)
        self.line(x0, y0, x0, y1)
        for x, label in xticks:
            self.line(x, y1, x, y1+.08)
            self.text(label, x-.45, y1+.12, .90, .26, 10.5)
        for y, label in yticks:
            self.line(x0-.08, y, x0, y)
            self.text(label, x0-.75, y-.12, .60, .25, 10.5, align="right")
        self.text(xlabel, x0, y1+.53, x1-x0, .29, 12, True)
        self.text(ylabel, .35, .84, 2.20, .27, 11, True, align="left")

    def finish(self):
        chart = self.chart
        return enrich_spec({
            "id": chart["id"], "version": "7.6.0-dev",
            "canvas": {"width_in": 13.333, "height_in": 7.5},
            "style": {"font": "Arial"},
            "data_lineage": {"data_ref": self.meta["file"], "sha256": self.meta["sha256"],
                             "source_url": self.meta["source_url"], "doi": self.meta["doi"],
                             "row_count": self.meta["row_count"], "chart_spec": "specs/iris_charts_v76.json"},
            "chart_contract": chart,
            "computed_values": self.values,
            "elements": self.elements,
        })


def scaled(value, low, high, out_low, out_high):
    return out_low + (value-low) / (high-low) * (out_high-out_low)


def separated_scatter_positions(rows, chart):
    """Separate coincident measured coordinates with bounded display-only offsets."""
    minimum = chart["statistics"]["jitter"]["minimum_center_gap_in"]
    maximum = chart["statistics"]["jitter"]["max_display_offset_in"]
    x0, x1, y0, y1 = 1.28, 9.80, 1.30, 5.66
    placed = []
    positions = {}
    for row in rows:
        true_x = scaled(row[chart["x"]], *chart["axes"]["x"]["domain"], x0, x1)
        true_y = scaled(row[chart["y"]], *chart["axes"]["y"]["domain"], y1, y0)
        candidate = None
        for step in range(int(maximum/.005)+1):
            radius = step*.005
            angles = (0,) if step == 0 else (2*math.pi*(j+.5*(step%2))/24 for j in range(24))
            for angle in angles:
                x, y = true_x+radius*math.cos(angle), true_y+radius*math.sin(angle)
                if all(math.hypot(x-px, y-py) >= minimum-1e-9 for px, py in placed):
                    candidate = (x, y)
                    break
            if candidate:
                break
        assert candidate is not None, (row["source_row"], "scatter packing exceeded bound")
        positions[row["source_row"]] = candidate
        placed.append(candidate)
    return positions


def scatter(chart, meta, rows):
    fig = Figure(chart, meta); fig.setup()
    x0, x1, y0, y1 = 1.28, 9.80, 1.30, 5.66
    fig.axes(x0, y0, x1, y1, "Petal length (cm)", "Petal width (cm)",
             [(scaled(v, 0, 7, x0, x1), str(v)) for v in range(0, 8)],
             [(scaled(v, 0, 3, y1, y0), str(v)) for v in range(0, 4)])
    positions = separated_scatter_positions(rows, chart)
    for row in rows:
        x, y = positions[row["source_row"]]
        fig.point(x, y, COLORS[row["species"]], row,
                  {"petal_length_cm": row["petal_length_cm"], "petal_width_cm": row["petal_width_cm"]},
                  r=.025)
    for i, name in enumerate(NAMES):
        y = 1.90 + i*.48
        shape = {"Iris-setosa": "ellipse", "Iris-versicolor": "rect",
                 "Iris-virginica": "trapezoid"}[name]
        fig.add(shape, x=10.49, y=y, w=.15, h=.15, fill=COLORS[name], stroke="#FFFFFF", sw=.5)
        fig.text(name.removeprefix("Iris-"), 10.76, y-.03, 1.68, .25, 11.5, align="left")
    return fig.finish()


def strip(chart, meta, rows, yfield, with_ci=False):
    fig = Figure(chart, meta); fig.setup()
    x0, x1, y0, y1 = 1.30, 11.90, 1.28, 5.66
    low, high = (0, 8) if with_ci else (3, 9)
    centers = {name: x0 + (i+.5)*(x1-x0)/3 for i, name in enumerate(NAMES)}
    fig.axes(x0, y0, x1, y1, "Species", ("Petal" if with_ci else "Sepal")+" length (cm)",
             [(centers[name], name.removeprefix("Iris-")) for name in NAMES],
             [(scaled(v, low, high, y1, y0), str(v)) for v in range(low, high+1)])
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["species"]].append(row)
        jitter = ((row["source_row"]*37) % 101 - 50) / 50 * .32
        x = centers[row["species"]] + jitter
        y = scaled(row[yfield], low, high, y1, y0)
        fig.point(x, y, COLORS[row["species"]], row, {yfield: row[yfield]}, r=.035)
    if with_ci:
        for name in NAMES:
            vals = [r[yfield] for r in grouped[name]]
            mean = statistics.mean(vals)
            rng = random.Random(chart["statistics"]["seed"] + NAMES.index(name))
            boot = sorted(statistics.mean(rng.choices(vals, k=len(vals)))
                          for _ in range(chart["statistics"]["resamples"]))
            lower, upper = boot[49], boot[1949]  # 2.5th and 97.5th percentiles of 2,000.
            x = centers[name]
            a, b, m = (scaled(v, low, high, y1, y0) for v in (lower, upper, mean))
            fig.line(x, a, x, b, color="#1C303A", sw=1.8)
            fig.line(x-.13, a, x+.13, a, color="#1C303A", sw=1.8)
            fig.line(x-.13, b, x+.13, b, color="#1C303A", sw=1.8)
            fig.add("ellipse", x=x-.085, y=m-.085, w=.17, h=.17, fill="#1C303A", stroke="#FFFFFF", sw=.7)
            fig.values.append({"species": name, "n": len(vals), "mean": round(mean, 4),
                               "ci95": [round(lower, 4), round(upper, 4)], "unit": "cm"})
    return fig.finish()


def predict_loo(rows, fields=("sepal_length_cm", "sepal_width_cm", "petal_length_cm", "petal_width_cm")):
    predictions = []
    for i, row in enumerate(rows):
        best = min((other for j, other in enumerate(rows) if j != i),
                   key=lambda other: (sum((row[k]-other[k])**2 for k in fields), other["source_row"]))
        predictions.append(best["species"])
    return predictions


def confusion(chart, meta, rows):
    fig = Figure(chart, meta); fig.setup()
    predictions = predict_loo(rows)
    counts = Counter((row["species"], predicted) for row, predicted in zip(rows, predictions))
    x0, y0, cell = 4.05, 1.45, 1.42
    fig.text("Predicted species", x0, .82, cell*3, .27, 12, True)
    fig.text("Actual", 2.95, 1.30, .85, .25, 11, True)
    for j, name in enumerate(NAMES):
        fig.text(name.removeprefix("Iris-"), x0+j*cell, 1.18, cell, .25, 10.5)
    for i, actual in enumerate(NAMES):
        fig.text(actual.removeprefix("Iris-"), 2.60, y0+i*cell+.54, 1.32, .25, 10.5, align="right")
        for j, predicted in enumerate(NAMES):
            count = counts[(actual, predicted)]
            fraction = count/50
            shade = round(245 - 115*fraction)
            fill = f"#{shade:02X}{round(250-91*fraction):02X}{round(252-79*fraction):02X}"
            x, y = x0+j*cell, y0+i*cell
            fig.add("rect", x=x, y=y, w=cell-.06, h=cell-.06, fill=fill,
                    stroke="#7D919B", sw=.8, source_rows=[r["source_row"] for r, p in zip(rows, predictions)
                                                   if r["species"] == actual and p == predicted])
            fig.text(count, x+.12, y+.49, cell-.30, .40, 19, True)
            fig.values.append({"actual": actual, "predicted": predicted, "count": count, "unit": "flowers"})
    fig.text("Rows sum to 50. Color and printed counts encode the same quantity.", 4.05, 5.91, 6.4, .29, 11, align="left")
    return fig.finish()


def ablation(chart, meta, rows):
    fig = Figure(chart, meta); fig.setup()
    groups = [
        ("All four measurements", ("sepal_length_cm", "sepal_width_cm", "petal_length_cm", "petal_width_cm")),
        ("Petal measurements only", ("petal_length_cm", "petal_width_cm")),
    ]
    x0, y0, w, h = 2.13, 1.40, 8.80, 4.46
    fig.axes(x0, y0, x0+w, y0+h, "", "Accuracy (%)",
             [(4.50, "Four features"), (8.60, "Petal only")],
             [(scaled(v, 0, 100, y0+h, y0), str(v)) for v in range(0, 101, 20)])
    for index, (name, fields) in enumerate(groups):
        predictions = predict_loo(rows, fields)
        correct_rows = [row["source_row"] for row, predicted in zip(rows, predictions)
                        if row["species"] == predicted]
        count = len(correct_rows)
        accuracy = count / len(rows) * 100
        x = 3.72 + index*4.10
        bh = h*accuracy/100
        fig.add("rect", x=x, y=y0+h-bh, w=1.55, h=bh,
                fill="#376F75" if index == 0 else "#A45C32", stroke="#FFFFFF", sw=.5,
                source_rows=[row["source_row"] for row in rows],
                row_predictions=[{"source_row": row["source_row"], "actual": row["species"], "predicted": pred}
                                 for row, pred in zip(rows, predictions)])
        fig.text(f"{accuracy:.1f}%", x-.18, y0+h-bh-.45, 1.91, .32, 16, True)
        fig.text(f"{count} / {len(rows)} correct", x-.20, y0+h-.45, 1.95, .30, 11.5,
                 color="#FFFFFF", align="center")
        fig.values.append({"feature_set": name, "features": list(fields), "n": len(rows),
                           "correct": count, "accuracy_percent": round(accuracy, 3),
                           "correct_source_rows": correct_rows, "unit": "percent"})
    return fig.finish()


def trend_interval(chart, meta, rows):
    selected = sorted((r for r in rows if r["species"] == chart["filter"]["species"]),
                      key=lambda r: (r[chart["x"]], r["source_row"]))
    assert len(selected) == chart["sample_size"] == 50
    fig = Figure(chart, meta); fig.setup()
    x0, x1, y0, y1 = 1.55, 11.40, 1.35, 5.66
    fig.axes(x0, y0, x1, y1, "Sepal length (cm)", "Petal length (cm)",
             [(scaled(v, 4, 6, x0, x1), f"{v:.1f}") for v in (4, 4.5, 5, 5.5, 6)],
             [(scaled(v, 0, 2, y1, y0), f"{v:.1f}") for v in (0, .5, 1, 1.5, 2)])
    for row in selected:
        fig.point(scaled(row[chart["x"]], 4, 6, x0, x1),
                  scaled(row[chart["y"]], 0, 2, y1, y0), "#9CB4BA", row,
                  {chart["x"]: row[chart["x"]], chart["y"]: row[chart["y"]]}, r=.035)
    locations = []
    for index in range(5):
        group = selected[index*10:(index+1)*10]
        xs = [r[chart["x"]] for r in group]
        ys = [r[chart["y"]] for r in group]
        rng = random.Random(chart["statistics"]["seed"]+index)
        boot = sorted(statistics.mean(rng.choices(ys, k=10)) for _ in range(chart["statistics"]["resamples"]))
        xmean, ymean = statistics.mean(xs), statistics.mean(ys)
        x = scaled(xmean, 4, 6, x0, x1)
        y = scaled(ymean, 0, 2, y1, y0)
        low = scaled(boot[49], 0, 2, y1, y0)
        high = scaled(boot[1949], 0, 2, y1, y0)
        fig.line(x, low, x, high, color="#1C303A", sw=1.4)
        fig.line(x-.10, low, x+.10, low, color="#1C303A", sw=1.4)
        fig.line(x-.10, high, x+.10, high, color="#1C303A", sw=1.4)
        locations.append((x, y))
        fig.values.append({"bin": index+1, "source_rows": [r["source_row"] for r in group], "n": 10,
                           "x_mean_cm": round(xmean, 4), "y_mean_cm": round(ymean, 4),
                           "ci95_cm": [round(boot[49], 4), round(boot[1949], 4)]})
    for (x1p, y1p), (x2p, y2p) in zip(locations, locations[1:]):
        fig.line(x1p, y1p, x2p, y2p, color="#1C303A", sw=1.5)
    for x, y in locations:
        fig.add("ellipse", x=x-.075, y=y-.075, w=.15, h=.15, fill="#1C303A", stroke="#FFFFFF", sw=.5)
    return fig.finish()


def main():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    rows = load_data(config)
    for chart in config["charts"]:
        if chart["kind"] == "scatter": spec = scatter(chart, config["data"], rows)
        elif chart["kind"] == "strip": spec = strip(chart, config["data"], rows, "sepal_length_cm")
        elif chart["kind"] == "point_ci": spec = strip(chart, config["data"], rows, "petal_length_cm", True)
        elif chart["kind"] == "confusion_matrix": spec = confusion(chart, config["data"], rows)
        elif chart["kind"] == "ablation": spec = ablation(chart, config["data"], rows)
        elif chart["kind"] == "trend_interval": spec = trend_interval(chart, config["data"], rows)
        else: raise ValueError(chart["kind"])
        SPEC_DIR.mkdir(parents=True, exist_ok=True)
        path = SPEC_DIR / f"{chart['id']}.json"
        path.write_text(json.dumps(spec, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        render(spec, ROOT/f"examples/{chart['id']}.svg", ROOT/f"dist/{chart['id']}.pptx")
        print(f"Built {chart['id']}: {len(spec['elements'])} elements")


if __name__ == "__main__":
    main()
