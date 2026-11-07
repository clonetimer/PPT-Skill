#!/usr/bin/env python3
"""Independently trace both Wine charts' editable marks to UCI source rows."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter

from build_wine_scatter import COLORS, CONFIG, SHAPES
from chart_contract import validate_chart_contract
from chart_data import load_rows
from scientific_ir import ROOT, validate_spec

SPEC = ROOT / "figure_specs/quant/Q07_wine_scatter.json"
STRIP_SPEC = ROOT / "figure_specs/quant/Q08_wine_strip.json"


def check(config: dict, spec: dict) -> None:
    chart = next(item for item in config["charts"] if item["id"] == spec["id"])
    meta = config["data"]
    source = ROOT / meta["file"]
    validate_chart_contract(config, load_rows(meta))
    assert hashlib.sha256(source.read_bytes()).hexdigest() == meta["sha256"]
    with source.open(encoding="utf-8", newline="") as stream:
        raw = list(csv.reader(stream))
    assert len(raw) == meta["row_count"] == chart["sample_size"] == 178
    assert all(len(row) == 14 for row in raw)
    assert Counter(row[0] for row in raw) == {"1": 59, "2": 71, "3": 48}
    assert raw[0][:2] == ["1", "14.23"] and raw[-1][:2] == ["3", "14.13"]
    assert spec["id"] == chart["id"] and spec["chart_contract"] == chart
    assert spec["data_lineage"]["sha256"] == meta["sha256"]
    assert spec["data_lineage"]["chart_spec"] == "specs/wine_charts_v76.json"
    validate_spec(spec)

    for direction in ("x", "y"):
        field = chart[direction]
        axis = chart["axes"][direction]
        assert axis["field"] == field and axis["unit"] == meta["columns"][field]["unit"]
        if axis["type"] == "linear":
            assert axis["unit"] == "source unit not reported"
            low, high = axis["domain"]
            assert low < high and all(low <= float(row[meta["columns"][field]["source_position"]]) <= high
                                      for row in raw)
        else:
            assert axis["categories"] == ["1", "2", "3"]
    assert chart["statistics"]["display"] == "all_raw_points"
    assert chart["statistics"]["interval"] == "none"
    assert "display-only" in chart["caption"].lower() and "unit" in chart["caption"].lower()

    marks = [e for e in spec["elements"] if "data_row" in e]
    assert len(marks) == len(raw)
    assert {e["data_row"] for e in marks} == set(range(1, len(raw)+1))
    centers = []
    for mark in marks:
        row = raw[mark["data_row"]-1]
        cultivar, alcohol, color = row[0], float(row[1]), float(row[10])
        if chart["kind"] == "scatter":
            assert mark["data_values"] == {"alcohol": alcohol, "color_intensity": color,
                                            "cultivar": cultivar}
        else:
            assert chart["kind"] == "strip"
            assert mark["data_values"] == {"alcohol": alcohol, "cultivar": cultivar}
        assert mark["type"] == SHAPES[cultivar] and mark["fill"] == COLORS[cultivar]
        center = (mark["x"]+mark["w"]/2, mark["y"]+mark["h"]/2)
        if chart["kind"] == "scatter":
            true_x = 1.28 + (alcohol-10)/5*(9.80-1.28)
            true_y = 5.66 - color/14*(5.66-1.30)
            assert math.dist(center, (true_x, true_y)) <= chart["statistics"]["jitter"]["max_display_offset_in"]+1e-9
        else:
            categories = chart["axes"]["x"]["categories"]
            true_x = 1.30 + (categories.index(cultivar)+.5)*(11.90-1.30)/len(categories)
            true_y = 5.66 - (alcohol-10)/5*(5.66-1.28)
            assert abs(center[0]-true_x) <= chart["statistics"]["jitter"]["max_display_offset_in"]+1e-9
            assert math.isclose(center[1], true_y, abs_tol=1e-6)
        centers.append(center)
    minimum = chart["statistics"]["jitter"]["minimum_center_gap_in"]
    assert all(math.dist(a, b) >= minimum-1e-6 for i, a in enumerate(centers) for b in centers[i+1:])
    labels = {e["text"] for e in spec["elements"] if e["type"] == "text"}
    expected = {"Alcohol (unit unreported)", "Cultivar 1", "Cultivar 2", "Cultivar 3"}
    if chart["kind"] == "scatter":
        expected.add("Color intensity (unit unreported)")
    else:
        expected.add("Cultivar code")
    assert expected <= labels
    assert any("178 samples" in label and "10.24432/C5PC7J" in label for label in labels)
    for suffix, base in (("svg", "examples"), ("pptx", "dist"), ("pdf", "dist")):
        assert (ROOT / base / f"{spec['id']}.{suffix}").is_file()


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "specs/chart_spec_v76.schema.json").read_text(encoding="utf-8"))
    try:
        import jsonschema
    except ImportError:
        jsonschema = None
    if jsonschema:
        jsonschema.validate(config, schema)
    for path in (SPEC, STRIP_SPEC):
        check(config, json.loads(path.read_text(encoding="utf-8")))
        print(f"PASS {path.stem}: 178 source-linked marks, coordinates, units boundary, encoding and SVG/PPTX/PDF")


if __name__ == "__main__":
    main()
