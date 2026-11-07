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

from build_quantitative_examples import ROOT, CONFIG, COLORS, load_data, predict_loo, NAMES
from scientific_ir import validate_spec


def scale_axis(value, axis, out_low, out_high):
    low, high = axis["domain"]
    return out_low + (value-low) / (high-low) * (out_high-out_low)


def check_axis_tick_labels(chart, spec):
    """Tie visible tick text to its declared value and rendered location."""
    kind = chart["kind"]
    if kind not in {"scatter", "strip", "point_ci", "trend_interval"}:
        return
    if kind == "scatter":
        x0, x1, y0, y1 = 1.28, 9.80, 1.30, 5.66
        xticks = [(scale_axis(value, chart["axes"]["x"], x0, x1), str(value)) for value in range(8)]
        yticks = [(scale_axis(value, chart["axes"]["y"], y1, y0), str(value)) for value in range(4)]
    elif kind in {"strip", "point_ci"}:
        x0, x1, y0, y1 = 1.30, 11.90, 1.28, 5.66
        xticks = [(x0+(index+.5)*(x1-x0)/3, name.removeprefix("Iris-"))
                  for index, name in enumerate(chart["axes"]["x"]["categories"])]
        low, high = chart["axes"]["y"]["domain"]
        yticks = [(scale_axis(value, chart["axes"]["y"], y1, y0), str(value))
                  for value in range(int(low), int(high)+1)]
    else:
        x0, x1, y0, y1 = 1.55, 11.40, 1.35, 5.66
        xticks = [(scale_axis(value, chart["axes"]["x"], x0, x1), f"{value:.1f}")
                  for value in (4, 4.5, 5, 5.5, 6)]
        yticks = [(scale_axis(value, chart["axes"]["y"], y1, y0), f"{value:.1f}")
                  for value in (0, .5, 1, 1.5, 2)]
    labels = [e for e in spec["elements"] if e["type"] == "text"]
    for tick, value in xticks:
        assert any(e["text"] == value and math.isclose(e["x"], tick-.45, abs_tol=1e-6)
                   and math.isclose(e["y"], y1+.12, abs_tol=1e-6) for e in labels), (
                       chart["id"], "x tick", value)
    for tick, value in yticks:
        assert any(e["text"] == value and math.isclose(e["x"], x0-.75, abs_tol=1e-6)
                   and math.isclose(e["y"], tick-.12, abs_tol=1e-6) for e in labels), (
                       chart["id"], "y tick", value)


def validate_axis_coverage(chart, rows, columns):
    for axis in chart["axes"].values():
        if axis["type"] == "linear" and axis["field"] in columns:
            low, high = axis["domain"]
            assert all(low <= row[axis["field"]] <= high for row in rows), (
                chart["id"], axis["field"], "clipped source value")


def check_point_geometry(chart, point, row):
    """Verify the actual plotted centre against the source row and declared axes."""
    kind = chart["kind"]
    if kind == "scatter":
        x = scale_axis(row[chart["x"]], chart["axes"]["x"], 1.28, 9.80)
        y = scale_axis(row[chart["y"]], chart["axes"]["y"], 5.66, 1.30)
        actual_x = point["x"] + point["w"] / 2
        actual_y = point["y"] + point["h"] / 2
        assert math.hypot(actual_x-x, actual_y-y) <= chart["statistics"]["jitter"]["max_display_offset_in"]+1e-9
        return
    elif kind in {"strip", "point_ci"}:
        categories = chart["axes"]["x"]["categories"]
        centers = {name: 1.30 + (i + .5) * (11.90 - 1.30) / len(categories)
                   for i, name in enumerate(categories)}
        x = centers[row["species"]]
        y = scale_axis(row[chart["y"]], chart["axes"]["y"], 5.66, 1.28)
    elif kind == "trend_interval":
        x = scale_axis(row[chart["x"]], chart["axes"]["x"], 1.55, 11.40)
        y = scale_axis(row[chart["y"]], chart["axes"]["y"], 5.66, 1.35)
    else:
        return
    actual_x = point["x"] + point["w"] / 2
    actual_y = point["y"] + point["h"] / 2
    maximum = chart["statistics"]["jitter"]["max_display_offset_in"]
    if kind in {"strip", "point_ci"}:
        assert abs(actual_x-x) <= maximum+1e-9, (chart["id"], row["source_row"], "x")
        assert math.isclose(actual_y, y, abs_tol=1e-6), (chart["id"], row["source_row"], "y")
    else:
        assert math.hypot(actual_x-x, actual_y-y) <= maximum+1e-9, (
            chart["id"], row["source_row"], "offset")


def validate_config(config):
    meta = config["data"]
    assert meta["row_unit"] and meta["source_url"] and meta["license"]
    assert meta["transforms"] and all(meta["transforms"])
    assert meta["missing_value_policy"] in {"fail", "documented_exclusion", "documented_imputation"}
    assert len({field["source_position"] for field in meta["columns"].values()}) == len(meta["columns"])
    for field in meta["columns"].values():
        assert field["unit"], "Every numeric or categorical axis needs a declared unit/type"
    for chart in config["charts"]:
        assert chart["claim"] and chart["caption"]
        derived = chart.get("derived_fields", {})
        referenced = {chart[key] for key in ("x", "y", "group")}
        assert set(derived) == referenced - set(meta["columns"]), (chart["id"], "derived field declaration")
        for name, field in derived.items():
            assert field["derivation"] and field["source_fields"]
            assert set(field["source_fields"]) <= set(meta["columns"]), (chart["id"], name, "unknown source field")
            assert field["type"] in {"number", "category"} and field["unit"]
        assert set(chart["axes"]) == {"x", "y"}
        for direction in ("x", "y"):
            axis = chart["axes"][direction]
            assert axis["field"] == chart[direction]
            if axis["field"] in meta["columns"]:
                assert axis["unit"] == meta["columns"][axis["field"]]["unit"]
            else:
                assert axis["unit"] == derived[axis["field"]]["unit"]
                assert (axis["type"] == "linear") is (derived[axis["field"]]["type"] == "number")
            if axis["type"] == "linear":
                low, high = axis["domain"]
                assert math.isfinite(low) and math.isfinite(high) and low < high
                assert axis["zero_included"] is (low <= 0 <= high)
                assert axis["zero_included"] or axis.get("domain_reason")
            else:
                assert axis["type"] == "category" and axis["unit"] == "category"
                assert axis["categories"] and len(axis["categories"]) == len(set(axis["categories"]))
                if axis["field"] in {"species", "actual_species", "predicted_species"}:
                    assert axis["categories"] == NAMES
        assert chart["sample_size"] == (50 if chart.get("filter") == {"species": "Iris-setosa"} else meta["row_count"])
        assert chart["group"] in meta["columns"] or chart["kind"] == "ablation" and chart["group"] == "feature_set"
        if chart["kind"] not in {"confusion_matrix", "ablation"}:
            assert chart["x"] in meta["columns"] and chart["y"] in meta["columns"]
        assert chart["statistics"]["display"] and chart["statistics"]["interval"]
        if chart["kind"] == "scatter":
            jitter = chart["statistics"]["jitter"]
            assert jitter["purpose"] == "display_only_separate_coincident_coordinates"
            assert .05 < jitter["minimum_center_gap_in"] <= jitter["max_display_offset_in"] <= .15
            assert "display-only offsets" in chart["caption"].lower()
        if chart["kind"] in {"strip", "point_ci", "trend_interval"}:
            jitter = chart["statistics"]["jitter"]
            expected = ("display_only_separate_close_coordinates" if chart["kind"] == "trend_interval"
                        else "display_only_horizontal_beeswarm")
            assert jitter["purpose"] == expected
            assert 0 < jitter["minimum_center_gap_in"] <= jitter["max_display_offset_in"] <= .55
            assert "display-only" in chart["caption"].lower()
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
            algorithm = chart["statistics"]["algorithm"]
            assert {key: algorithm[key] for key in ("classifier", "k", "distance", "feature_scaling",
                                                    "validation", "distance_tie_break")} == {
                "classifier": "nearest_neighbor", "k": 1, "distance": "euclidean",
                "feature_scaling": "none", "validation": "leave_one_out",
                "distance_tie_break": "lowest_source_row"}
            if chart["kind"] == "confusion_matrix":
                assert algorithm["features"] == ["sepal_length_cm", "sepal_width_cm",
                                                 "petal_length_cm", "petal_width_cm"]
            else:
                assert chart["statistics"]["paired_folds"] is True
                groups = chart["statistics"]["feature_sets"]
                assert [item["label"] for item in groups] == chart["axes"]["x"]["categories"]
                assert [item["fields"] for item in groups] == [
                    ["sepal_length_cm", "sepal_width_cm", "petal_length_cm", "petal_width_cm"],
                    ["petal_length_cm", "petal_width_cm"]]
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
        check_axis_tick_labels(chart, spec)
        assert spec["data_lineage"]["sha256"] == config["data"]["sha256"]
        points = [e for e in spec["elements"] if "data_row" in e]
        chart_lookup = {key: row for key, row in lookup.items()
                        if not chart.get("filter") or row["species"] == chart["filter"]["species"]}
        validate_axis_coverage(chart, chart_lookup.values(), config["data"]["columns"])
        if chart["kind"] not in {"confusion_matrix", "ablation"}:
            assert Counter(e["data_row"] for e in points) == Counter({key: 1 for key in chart_lookup})
            for point in points:
                row = lookup[point["data_row"]]
                assert all(row[key] == value for key, value in point["data_values"].items())
                assert point["type"] == {"Iris-setosa": "ellipse", "Iris-versicolor": "rect",
                                         "Iris-virginica": "trapezoid"}[row["species"]]
                check_point_geometry(chart, point, row)
            minimum = chart["statistics"]["jitter"]["minimum_center_gap_in"]
            centers = [(point["x"]+point["w"]/2, point["y"]+point["h"]/2) for point in points]
            assert all(point["w"] < minimum for point in points), (stem, "marks overlap at declared gap")
            assert all(math.dist(first, second) >= minimum-1e-9
                       for i, first in enumerate(centers) for second in centers[i+1:]), (
                           stem, "raw points overlap")
            if chart["kind"] == "scatter":
                legend_shapes = [e for e in spec["elements"] if e["type"] in {"ellipse", "rect", "trapezoid"}
                                 and math.isclose(e.get("x", -1), 10.49, abs_tol=1e-6)
                                 and math.isclose(e.get("w", 0), .15, abs_tol=1e-6)]
                assert len(legend_shapes) == len(NAMES)
                for index, name in enumerate(NAMES):
                    symbol = legend_shapes[index]
                    assert symbol["type"] == {"Iris-setosa": "ellipse", "Iris-versicolor": "rect",
                                              "Iris-virginica": "trapezoid"}[name]
                    assert symbol["fill"] == COLORS[name]
                    assert any(e["type"] == "text" and e["text"] == name.removeprefix("Iris-")
                               and math.isclose(e["y"], symbol["y"]-.03, abs_tol=1e-6)
                               for e in spec["elements"]), (stem, name, "legend label")
                counts = Counter((row[chart["x"]], row[chart["y"]]) for row in chart_lookup.values())
                centers = []
                moved = 0
                for point in points:
                    row = lookup[point["data_row"]]
                    actual = (point["x"]+point["w"]/2, point["y"]+point["h"]/2)
                    exact = (scale_axis(row[chart["x"]], chart["axes"]["x"], 1.28, 9.80),
                             scale_axis(row[chart["y"]], chart["axes"]["y"], 5.66, 1.30))
                    distance = math.dist(actual, exact)
                    if counts[(row[chart["x"]], row[chart["y"]])] == 1:
                        assert distance <= 1e-9, (stem, row["source_row"], "unique point moved")
                    moved += distance > 1e-9
                    centers.append(actual)
                assert moved == sum(count-1 for count in counts.values())
        elif chart["kind"] == "confusion_matrix":
            text_elements = [e for e in spec["elements"] if e["type"] == "text"]
            for index, name in enumerate(chart["axes"]["x"]["categories"]):
                label = name.removeprefix("Iris-")
                assert any(e["text"] == label and math.isclose(e["x"], 4.05+index*1.42, abs_tol=1e-6)
                           and math.isclose(e["y"], 1.18, abs_tol=1e-6) for e in text_elements)
            for index, name in enumerate(chart["axes"]["y"]["categories"]):
                label = name.removeprefix("Iris-")
                assert any(e["text"] == label and math.isclose(e["x"], 2.60, abs_tol=1e-6)
                           and math.isclose(e["y"], 1.99+index*1.42, abs_tol=1e-6)
                           for e in text_elements)
            cells = [e for e in spec["elements"] if "source_rows" in e]
            assert len(cells) == 9
            assert [item["count"] for item in spec["computed_values"]] == [50, 0, 0, 0, 47, 3, 0, 3, 47]
            assert Counter(row for cell in cells for row in cell["source_rows"]) == Counter({key: 1 for key in lookup})
            assert sum(v["count"] for v in spec["computed_values"]) == len(rows)
            predictions = predict_loo(rows, tuple(chart["statistics"]["algorithm"]["features"]))
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
            text_elements = [e for e in spec["elements"] if e["type"] == "text"]
            assert [item["label"] for item in chart["statistics"]["feature_sets"]] == [
                "All four measurements", "Petal measurements only"]
            for x, label in ((4.05, "Four features"), (8.15, "Petal only")):
                assert any(e["text"] == label and math.isclose(e["x"], x, abs_tol=1e-6)
                           and math.isclose(e["y"], 5.98, abs_tol=1e-6) for e in text_elements)
            for value in range(0, 101, 20):
                y = scale_axis(value, chart["axes"]["y"], 5.86, 1.40)-.12
                assert any(e["text"] == str(value) and math.isclose(e["x"], 1.38, abs_tol=1e-6)
                           and math.isclose(e["y"], y, abs_tol=1e-6) for e in text_elements)
            bars = [e for e in spec["elements"] if "row_predictions" in e]
            assert len(bars) == len(spec["computed_values"]) == 2
            assert [item["correct"] for item in spec["computed_values"]] == [144, 143]
            assert chart["axes"]["x"]["categories"] == [item["feature_set"] for item in spec["computed_values"]]
            assert chart["axes"]["y"]["unit"] == "%"
            for bar, item in zip(bars, spec["computed_values"]):
                assert item["features"] == next(group["fields"] for group in chart["statistics"]["feature_sets"]
                                                if group["label"] == item["feature_set"])
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
                expected_height = 4.46 * (item["accuracy_percent"] - chart["axes"]["y"]["domain"][0]) / (
                    chart["axes"]["y"]["domain"][1] - chart["axes"]["y"]["domain"][0])
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
                expected_x = 1.30 + (index + .5) * (11.90 - 1.30) / 3 + .75
                expected_y = scale_axis(item["mean"], chart["axes"]["y"], 5.66, 1.28)
                assert math.isclose(marker["x"] + marker["w"] / 2, expected_x, abs_tol=1e-6)
                assert math.isclose(marker["y"] + marker["h"] / 2, expected_y, abs_tol=.0001)
                assert all(math.dist((marker["x"]+marker["w"]/2, marker["y"]+marker["h"]/2),
                                     (point["x"]+point["w"]/2, point["y"]+point["h"]/2))
                           > (marker["w"]+point["w"])/2
                           for point in points), (chart["id"], "summary covers raw observation")
            whiskers = [e for e in spec["elements"] if e["type"] == "line"
                        and e.get("color") == "#1C303A" and e.get("sw") == 1.8
                        and math.isclose(e["x1"], e["x2"], abs_tol=1e-6)]
            assert len(whiskers) == 3
            for index, (whisker, item) in enumerate(zip(whiskers, spec["computed_values"])):
                expected_x = 1.30 + (index + .5) * (11.90 - 1.30) / 3 + .75
                expected_ys = sorted(scale_axis(value, chart["axes"]["y"], 5.66, 1.28)
                                     for value in item["ci95"])
                assert math.isclose(whisker["x1"], expected_x, abs_tol=1e-6)
                assert all(math.isclose(actual, expected, abs_tol=.0001)
                           for actual, expected in zip(sorted((whisker["y1"], whisker["y2"])), expected_ys))
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
                expected_x = scale_axis(item["x_mean_cm"], chart["axes"]["x"], 1.55, 11.40)
                expected_y = scale_axis(item["y_mean_cm"], chart["axes"]["y"], 5.66, 1.35)
                assert math.isclose(marker["x"] + marker["w"] / 2, expected_x, abs_tol=.0003)
                assert math.isclose(marker["y"] + marker["h"] / 2, expected_y, abs_tol=.0003)
                assert all(math.dist((marker["x"]+marker["w"]/2, marker["y"]+marker["h"]/2),
                                     (point["x"]+point["w"]/2, point["y"]+point["h"]/2))
                           > (marker["w"]+point["w"])/2
                           for point in points), (chart["id"], "summary covers raw observation")
            whiskers = [e for e in spec["elements"] if e["type"] == "line"
                        and e.get("color") == "#1C303A" and e.get("sw") == 1.4
                        and math.isclose(e["x1"], e["x2"], abs_tol=1e-6)]
            assert len(whiskers) == 5
            for whisker, item in zip(whiskers, spec["computed_values"]):
                expected_x = scale_axis(item["x_mean_cm"], chart["axes"]["x"], 1.55, 11.40)
                expected_ys = sorted(scale_axis(value, chart["axes"]["y"], 5.66, 1.35)
                                     for value in item["ci95_cm"])
                assert math.isclose(whisker["x1"], expected_x, abs_tol=.0003)
                assert all(math.isclose(actual, expected, abs_tol=.0003)
                           for actual, expected in zip(sorted((whisker["y1"], whisker["y2"])), expected_ys))
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
