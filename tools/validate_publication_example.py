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
    assert spec["computed_values"] == source["computed_values"]
    assert spec["chart_contract"] == source["chart_contract"]
    assert spec["data_lineage"] == source["data_lineage"]
    source_rows = {row["source_row"]: row for row in rows}
    points = [e for e in spec["elements"] if "data_row" in e]
    assert len(points) == len(rows) == 150
    assert {e["data_row"] for e in points} == set(source_rows)
    assert all(e["data_values"]["petal_length_cm"] == source_rows[e["data_row"]]["petal_length_cm"]
               for e in points)
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
    assert "2,000" in caption and "50 per species" in caption and "jitter" in caption
    print(f"PASS {STEM}: same 150 rows/statistics, {WIDTH_MM} × {HEIGHT_MM} mm PPTX/PDF")


if __name__ == "__main__":
    main()
