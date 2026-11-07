#!/usr/bin/env python3
"""Verify publication-size layout retains Q03 data and final-size PDF geometry."""
from __future__ import annotations

import json
import math

from pptx import Presentation
from pypdf import PdfReader

from build_publication_example import HEIGHT_MM, STEM, WIDTH_MM
from build_quantitative_examples import CONFIG, load_data
from scientific_ir import ROOT, validate_spec


def main():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    rows = load_data(config)
    source = json.loads((ROOT / "figure_specs/quant/Q03_iris_mean_ci.json").read_text(encoding="utf-8"))
    spec = json.loads((ROOT / f"figure_specs/quant/{STEM}.json").read_text(encoding="utf-8"))
    validate_spec(spec)
    assert spec["figure_contract"]["output_mode"] == "publication"
    assert spec["scientific_source_ref"] == "figure_specs/quant/Q03_iris_mean_ci.json"
    target = spec["publication_target"]
    assert target["journal_name"] == "Nature" and target["figure_class"] == "main_figure"
    assert target["final_width_mm"] == 183 and target["maximum_height_mm"] == 170
    assert target["preferred_submission_format"] == "PDF"
    assert spec["computed_values"] == source["computed_values"]
    assert spec["chart_contract"] == source["chart_contract"]
    assert spec["chart_contract"]["axes"]["x"]["categories"] == [
        "Iris-setosa", "Iris-versicolor", "Iris-virginica"]
    assert spec["chart_contract"]["axes"]["y"]["domain"] == [0, 8]
    assert spec["data_lineage"] == source["data_lineage"]
    source_rows = {row["source_row"]: row for row in rows}
    points = [e for e in spec["elements"] if "data_row" in e]
    assert len(points) == len(rows) == 150
    assert {e["data_row"] for e in points} == set(source_rows)
    assert all(e["data_values"]["petal_length_cm"] == source_rows[e["data_row"]]["petal_length_cm"]
               for e in points)
    centers = {name: 1.88 + index * 1.86 for index, name in enumerate(
        ("Iris-setosa", "Iris-versicolor", "Iris-virginica"))}
    minimum = spec["chart_contract"]["statistics"]["jitter"]["minimum_center_gap_in"]
    maximum = spec["chart_contract"]["statistics"]["jitter"]["max_display_offset_in"]
    visible_centers = []
    for point in points:
        row = source_rows[point["data_row"]]
        expected_x = centers[row["species"]]
        expected_y = 3.23 - row["petal_length_cm"] / 8 * (3.23 - .32)
        actual_x = point["x"] + point["w"] / 2
        actual_y = point["y"] + point["h"] / 2
        assert abs(actual_x-expected_x) <= maximum+1e-9
        assert math.isclose(actual_y, expected_y, abs_tol=1e-6)
        assert point["w"] < minimum
        visible_centers.append((actual_x, actual_y))
    assert all(math.dist(first, second) >= minimum-1e-9
               for i, first in enumerate(visible_centers) for second in visible_centers[i+1:])
    markers = [e for e in spec["elements"] if e["type"] == "ellipse"
               and math.isclose(e.get("w", 0), .104, abs_tol=1e-6)
               and e.get("fill") == "#1C303A"]
    assert len(markers) == 3
    for marker, item in zip(markers, spec["computed_values"]):
        assert math.isclose(marker["x"] + marker["w"] / 2, centers[item["species"]]+.70, abs_tol=1e-6)
        assert all(math.dist((marker["x"]+marker["w"]/2, marker["y"]+marker["h"]/2),
                             point_center) > (marker["w"]+.040)/2
                   for point_center in visible_centers)
        expected_y = 3.23 - item["mean"] / 8 * (3.23 - .32)
        assert math.isclose(marker["y"] + marker["h"] / 2, expected_y, abs_tol=.0001)
    whiskers = [e for e in spec["elements"] if e["type"] == "line" and e.get("sw") == .9
                and math.isclose(e["x1"], e["x2"], abs_tol=1e-6)]
    assert len(whiskers) == 3
    for whisker, item in zip(whiskers, spec["computed_values"]):
        assert math.isclose(whisker["x1"], centers[item["species"]]+.70, abs_tol=1e-6)
        expected_ys = sorted(3.23 - value / 8 * (3.23 - .32) for value in item["ci95"])
        assert all(math.isclose(actual, expected, abs_tol=.0001)
                   for actual, expected in zip(sorted((whisker["y1"], whisker["y2"])), expected_ys))
    labels = [e["text"] for e in spec["elements"] if e["type"] == "text"]
    assert "Petal length (cm)" in labels and "Species" in labels
    deck = Presentation(ROOT / f"dist/{STEM}.pptx")
    assert len(deck.slides) == 1
    assert math.isclose(deck.slide_width / 914400*25.4, WIDTH_MM, abs_tol=.01)
    assert math.isclose(deck.slide_height / 914400*25.4, HEIGHT_MM, abs_tol=.01)
    pdf = PdfReader(ROOT / f"dist/{STEM}.pdf")
    assert len(pdf.pages) == 1
    page = pdf.pages[0]
    assert math.isclose(float(page.mediabox.width)/72*25.4, WIDTH_MM, abs_tol=.05)
    assert math.isclose(float(page.mediabox.height)/72*25.4, HEIGHT_MM, abs_tol=.05)
    fonts = [value.get_object() for value in page["/Resources"]["/Font"].values()]
    assert fonts and all(font.get("/Subtype") == "/TrueType" for font in fonts)
    assert all(font["/FontDescriptor"].get_object().get("/FontFile2") for font in fonts)
    assert not page["/Resources"].get("/XObject"), "Vector plot must not be flattened into a PDF image"
    caption = (ROOT / "docs/Q03_NATURE_PUBLICATION_CAPTION.md").read_text(encoding="utf-8")
    assert "2,000" in caption and "50 per species" in caption and "beeswarm" in caption
    print(f"PASS {STEM}: same 150 rows/statistics, {WIDTH_MM} × {HEIGHT_MM} mm PPTX/PDF")


if __name__ == "__main__":
    main()
