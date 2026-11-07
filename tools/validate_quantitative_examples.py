#!/usr/bin/env python3
"""Check source hashes, units, row lineage, intervals, and chart outputs."""
from __future__ import annotations

import hashlib
import json
import math
import random
import statistics
from collections import Counter
from pathlib import Path

from build_quantitative_examples import ROOT, CONFIG, load_data, predict_loo, NAMES
from scientific_ir import validate_spec


def check_point_geometry(chart, point, row):
    """Verify the actual plotted centre against the source row and declared axes."""
    kind = chart["kind"]
    if kind == "scatter":
        x = 1.28 + row["petal_length_cm"] / 7 * (9.80 - 1.28)
        y = 5.66 - row["petal_width_cm"] / 3 * (5.66 - 1.30)
    elif kind in {"strip", "point_ci"}:
        centers = {name: 1.30 + (i + .5) * (11.90 - 1.30) / 3 for i, name in enumerate(NAMES)}
        jitter = ((row["source_row"] * 37) % 101 - 50) / 50 * .32
        x = centers[row["species"]] + jitter
        value = row["petal_length_cm" if kind == "point_ci" else "sepal_length_cm"]
        low, high = (0, 8) if kind == "point_ci" else (3, 9)
        y = 5.66 - (value - low) / (high - low) * (5.66 - 1.28)
    elif kind == "trend_interval":
        x = 1.55 + (row["sepal_length_cm"] - 4) / 2 * (11.40 - 1.55)
        y = 5.66 - row["petal_length_cm"] / 2 * (5.66 - 1.35)
    else:
        return
    actual_x = point["x"] + point["w"] / 2
    actual_y = point["y"] + point["h"] / 2
    assert math.isclose(actual_x, x, abs_tol=1e-6), (chart["id"], row["source_row"], "x")
    assert math.isclose(actual_y, y, abs_tol=1e-6), (chart["id"], row["source_row"], "y")


def validate_config(config):
    meta = config["data"]
    assert meta["row_unit"] and meta["source_url"] and meta["license"]
    assert meta["missing_value_policy"] in {"fail", "documented_exclusion", "documented_imputation"}
    assert len({field["source_position"] for field in meta["columns"].values()}) == len(meta["columns"])
    for field in meta["columns"].values():
        assert field["unit"], "Every numeric or categorical axis needs a declared unit/type"
    for chart in config["charts"]:
        assert chart["claim"] and chart["caption"]
        assert chart["sample_size"] == (50 if chart.get("filter") == {"species": "Iris-setosa"} else meta["row_count"])
        assert chart["group"] in meta["columns"] or chart["kind"] == "ablation" and chart["group"] == "feature_set"
        if chart["kind"] not in {"confusion_matrix", "ablation"}:
            assert chart["x"] in meta["columns"] and chart["y"] in meta["columns"]
        assert chart["statistics"]["display"] and chart["statistics"]["interval"]
        if chart["kind"] == "point_ci":
            assert chart["statistics"]["interval"] == "bootstrap_percentile_95"
            assert chart["statistics"]["resamples"] >= 1000
            assert isinstance(chart["statistics"]["seed"], int)
            assert chart["statistics"]["resampling_unit"] == meta["row_unit"] or chart["statistics"]["resampling_unit"] == "flower within species"
        if chart["kind"] == "trend_interval":
            assert chart["statistics"]["interval"] == "bootstrap_percentile_95"
            assert chart["statistics"]["resamples"] >= 1000 and isinstance(chart["statistics"]["seed"], int)
            assert chart["statistics"]["resampling_unit"] == "flower within bin"
        if chart["kind"] in {"confusion_matrix", "ablation"}:
            assert chart["statistics"]["method"] and chart["statistics"]["splits"]
    try:
        import jsonschema
    except ImportError:
        pass
    else:
        schema = json.loads((ROOT / "specs/chart_spec_v76.schema.json").read_text(encoding="utf-8"))
        jsonschema.validate(config, schema)


def validate_outputs(config, rows):
    lookup = {row["source_row"]: row for row in rows}
    for chart in config["charts"]:
        stem = chart["id"]
        spec_path = ROOT / f"figure_specs/quant/{stem}.json"
        svg = ROOT / f"examples/{stem}.svg"
        pptx = ROOT / f"dist/{stem}.pptx"
        assert all(path.is_file() for path in (spec_path, svg, pptx))
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        validate_spec(spec)
        assert spec["chart_contract"] == chart
        assert spec["data_lineage"]["sha256"] == config["data"]["sha256"]
        points = [e for e in spec["elements"] if "data_row" in e]
        chart_lookup = {key: row for key, row in lookup.items()
                        if not chart.get("filter") or row["species"] == chart["filter"]["species"]}
        if chart["kind"] not in {"confusion_matrix", "ablation"}:
            assert Counter(e["data_row"] for e in points) == Counter({key: 1 for key in chart_lookup})
            for point in points:
                row = lookup[point["data_row"]]
                assert all(row[key] == value for key, value in point["data_values"].items())
                assert point["type"] == {"Iris-setosa": "ellipse", "Iris-versicolor": "rect",
                                         "Iris-virginica": "trapezoid"}[row["species"]]
                check_point_geometry(chart, point, row)
        elif chart["kind"] == "confusion_matrix":
            cells = [e for e in spec["elements"] if "source_rows" in e]
            assert len(cells) == 9
            assert Counter(row for cell in cells for row in cell["source_rows"]) == Counter({key: 1 for key in lookup})
            assert sum(v["count"] for v in spec["computed_values"]) == len(rows)
            predictions = predict_loo(rows)
            expected = Counter((row["species"], pred) for row, pred in zip(rows, predictions))
            for item, cell in zip(spec["computed_values"], cells):
                pair = (item["actual"], item["predicted"])
                assert item["count"] == expected[pair]
                expected_rows = [row["source_row"] for row, pred in zip(rows, predictions)
                                 if (row["species"], pred) == pair]
                assert cell["source_rows"] == expected_rows
            printed_counts = [int(e["text"]) for e in spec["elements"]
                              if e["type"] == "text" and e["text"].isdigit()]
            assert printed_counts == [item["count"] for item in spec["computed_values"]]
        else:
            bars = [e for e in spec["elements"] if "row_predictions" in e]
            assert len(bars) == len(spec["computed_values"]) == 2
            for bar, item in zip(bars, spec["computed_values"]):
                predictions = predict_loo(rows, tuple(item["features"]))
                expected_rows = [row["source_row"] for row, pred in zip(rows, predictions)
                                 if row["species"] == pred]
                assert item["n"] == len(rows) and item["correct"] == len(expected_rows)
                assert item["correct_source_rows"] == expected_rows
                assert math.isclose(item["accuracy_percent"], 100*len(expected_rows)/len(rows), abs_tol=.001)
                assert bar["source_rows"] == list(lookup)
                assert bar["row_predictions"] == [{"source_row": row["source_row"], "actual": row["species"],
                                                    "predicted": pred} for row, pred in zip(rows, predictions)]
                assert any(e["type"] == "text" and e["text"] == f"{item['correct']} / {len(rows)} correct"
                           for e in spec["elements"])
                expected_height = 4.46 * item["accuracy_percent"] / 100
                assert math.isclose(bar["h"], expected_height, abs_tol=.00005)
                assert math.isclose(bar["y"] + bar["h"], 1.40 + 4.46, abs_tol=1e-6)
        if chart["kind"] == "point_ci":
            assert len(spec["computed_values"]) == 3
            for item in spec["computed_values"]:
                raw = [row[chart["y"]] for row in rows if row["species"] == item["species"]]
                assert item["n"] == len(raw) == 50
                assert math.isclose(item["mean"], statistics.mean(raw), abs_tol=.0001)
                assert item["ci95"][0] <= item["mean"] <= item["ci95"][1]
                rng = random.Random(chart["statistics"]["seed"] + NAMES.index(item["species"]))
                boot = sorted(statistics.mean(rng.choices(raw, k=len(raw)))
                              for _ in range(chart["statistics"]["resamples"]))
                assert item["ci95"] == [round(boot[49], 4), round(boot[1949], 4)]
            markers = [e for e in spec["elements"] if e["type"] == "ellipse"
                       and math.isclose(e.get("w", 0), .17, abs_tol=1e-6)
                       and e.get("fill") == "#1C303A"]
            assert len(markers) == 3
            for index, (marker, item) in enumerate(zip(markers, spec["computed_values"])):
                expected_x = 1.30 + (index + .5) * (11.90 - 1.30) / 3
                expected_y = 5.66 - item["mean"] / 8 * (5.66 - 1.28)
                assert math.isclose(marker["x"] + marker["w"] / 2, expected_x, abs_tol=1e-6)
                assert math.isclose(marker["y"] + marker["h"] / 2, expected_y, abs_tol=.0001)
        if chart["kind"] == "trend_interval":
            assert len(spec["computed_values"]) == 5
            selected = sorted(chart_lookup.values(), key=lambda r: (r[chart["x"]], r["source_row"]))
            for index, item in enumerate(spec["computed_values"]):
                group = selected[index*10:(index+1)*10]
                xs = [row[chart["x"]] for row in group]
                ys = [row[chart["y"]] for row in group]
                assert item["bin"] == index+1 and item["n"] == 10
                assert item["source_rows"] == [row["source_row"] for row in group]
                assert item["x_mean_cm"] == round(statistics.mean(xs), 4)
                assert item["y_mean_cm"] == round(statistics.mean(ys), 4)
                rng = random.Random(chart["statistics"]["seed"]+index)
                boot = sorted(statistics.mean(rng.choices(ys, k=10))
                              for _ in range(chart["statistics"]["resamples"]))
                assert item["ci95_cm"] == [round(boot[49], 4), round(boot[1949], 4)]
            markers = [e for e in spec["elements"] if e["type"] == "ellipse"
                       and math.isclose(e.get("w", 0), .15, abs_tol=1e-6)
                       and e.get("fill") == "#1C303A"]
            assert len(markers) == 5
            for marker, item in zip(markers, spec["computed_values"]):
                expected_x = 1.55 + (item["x_mean_cm"] - 4) / 2 * (11.40 - 1.55)
                expected_y = 5.66 - item["y_mean_cm"] / 2 * (5.66 - 1.35)
                assert math.isclose(marker["x"] + marker["w"] / 2, expected_x, abs_tol=.0003)
                assert math.isclose(marker["y"] + marker["h"] / 2, expected_y, abs_tol=.0003)
        print(f"PASS {stem}: {len(points)} raw points, {len(spec['computed_values'])} summaries")


def main():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    validate_config(config)
    data_path = ROOT / config["data"]["file"]
    assert hashlib.sha256(data_path.read_bytes()).hexdigest() == config["data"]["sha256"]
    rows = load_data(config)
    validate_outputs(config, rows)


if __name__ == "__main__":
    main()
