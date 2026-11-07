#!/usr/bin/env python3
"""Verify the source image, displayed panel, scale bar and linked quantification."""
from __future__ import annotations

import hashlib
import json
import math
import zipfile

from PIL import Image

from build_image_quant_example import ROOT, SHA256, SOURCE, STEM
from scientific_ir import validate_spec


def validate():
    spec = json.loads((ROOT / f"figure_specs/image/{STEM}.json").read_text(encoding="utf-8"))
    validate_spec(spec)
    contract = spec["image_contract"]
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == contract["source_sha256"] == SHA256
    assert contract["license"] == "CC0" and contract["source_url"]
    image = Image.open(SOURCE)
    width, height = image.size
    hist = image.histogram()
    image.close()
    assert [width, height] == contract["original_size_px"] == [550, 660]
    display = contract["display"]
    assert display["crop_xywh_px"] == [0, 0, 550, 660]
    assert display["stitching"] == "none" and display["intensity_transform"] == "none"
    assert display["lut"] == "grayscale" and display["gamma"] == 1
    panels = [e for e in spec["elements"] if e["type"] == "image"]
    assert len(panels) == 1 and panels[0]["image_ref"] == contract["source_id"]
    assert panels[0]["path"] == contract["source_file"]
    assert math.isclose(panels[0]["w"] / panels[0]["h"], width / height, rel_tol=.003)
    scale = contract["scale_bar"]
    assert scale["length_um"] > 0 and contract["pixel_spacing_um"] > 0
    expected_inches = scale["length_um"] / contract["pixel_spacing_um"] * panels[0]["w"] / width
    assert math.isclose(scale["length_display_in"], expected_inches, rel_tol=1e-10)
    assert math.isclose(scale["length_source_px"], scale["length_um"] / contract["pixel_spacing_um"], rel_tol=1e-10)
    scale_lines = [e for e in spec["elements"] if e["type"] == "line"
                   and e.get("color") == "#FFFFFF" and e.get("sw") == 3]
    assert len(scale_lines) == 1
    scale_line = scale_lines[0]
    assert math.isclose(scale_line["x2"] - scale_line["x1"], expected_inches, abs_tol=1e-10)
    assert math.isclose(scale_line["y1"], scale_line["y2"], abs_tol=1e-10)
    assert panels[0]["x"] <= scale_line["x1"] < scale_line["x2"] <= panels[0]["x"] + panels[0]["w"]
    assert panels[0]["y"] <= scale_line["y1"] <= panels[0]["y"] + panels[0]["h"]
    assert any(e["type"] == "text" and e["text"] == f"{scale['length_um']:g} µm"
               for e in spec["elements"])
    quant = contract["quantification"]
    assert quant["image_ref"] == contract["source_id"] and quant["roi"] == "full field"
    assert quant["n_pixels"] == sum(hist) == width * height
    assert quant["bins"] == [sum(hist[i:i+16]) for i in range(0, 256, 16)]
    assert quant["high_pixel_count"] == sum(hist[quant["threshold"]:])
    assert quant["n_biological_replicates"] == 1 and quant["threshold_role"] == "descriptive display-only"
    bars = [e for e in spec["elements"] if "histogram_bin" in e]
    assert len(bars) == 16
    assert [e["pixel_count"] for e in bars] == quant["bins"]
    assert all(e["image_ref"] == contract["source_id"] for e in bars)
    maximum = max(quant["bins"])
    x0, y0, chart_width, chart_height = 6.53, 1.62, 5.77, 3.90
    for index, bar in enumerate(bars):
        assert bar["histogram_bin"] == index and bar["intensity_range"] == [index*16, index*16+15]
        expected_height = chart_height * quant["bins"][index] / maximum
        assert math.isclose(bar["h"], expected_height, abs_tol=1e-10)
        assert math.isclose(bar["y"] + bar["h"], y0 + chart_height, abs_tol=1e-10)
        assert math.isclose(bar["x"], x0 + index*chart_width/16 + .035, abs_tol=1e-10)
    threshold = quant["threshold"]
    summary = f"Pixels ≥{threshold}: {quant['high_pixel_count']:,} / {quant['n_pixels']:,} ({quant['high_pixel_count']/quant['n_pixels']:.1%})"
    assert any(e["type"] == "text" and e["text"] == summary for e in spec["elements"])
    assert contract["short_description"] and contract["long_description"]
    with zipfile.ZipFile(ROOT / f"dist/{STEM}.pptx") as deck:
        embedded = [deck.read(name) for name in deck.namelist() if name.startswith("ppt/media/")]
    assert embedded == [raw], "PPTX must contain the exact raw source image"
    for extension in ("svg",):
        assert (ROOT / f"examples/{STEM}.{extension}").is_file()
    for extension in ("pptx", "pdf", "preview.png"):
        assert (ROOT / f"dist/{STEM}.{extension}").is_file()
    print(f"PASS {STEM}: source SHA, pixel histogram, scale and embedded image")


if __name__ == "__main__":
    validate()
