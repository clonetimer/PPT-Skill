#!/usr/bin/env python3
"""Build an image and pixel-histogram example with explicit image provenance."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

from render_figure_spec import render
from scientific_ir import ROOT, enrich_spec, validate_spec

SOURCE = ROOT / "data/cell_scikit_image_v026.png"
SHA256 = "8d23a7fb81f7cc877cd09f330357fc7f595651306e84e17252f6e0a1b3f61515"
STEM = "I01_cell_image_quant"


def build():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SHA256
    image = Image.open(SOURCE)
    assert image.mode == "L" and image.size == (550, 660)
    hist = image.histogram()
    assert len(hist) == 256 and sum(hist) == 550 * 660
    bins = [sum(hist[i:i + 16]) for i in range(0, 256, 16)]
    threshold = 128
    high = sum(hist[threshold:])
    elements = []

    def add(kind, **fields):
        elements.append({"type": kind, **fields})

    def txt(value, x, y, w, h, size=12, bold=False, color="#26343C", align="left"):
        add("text", text=str(value), x=x, y=y, w=w, h=h, size=size,
            bold=bold, color=color, align=align)

    txt("One microscopy image, one linked pixel summary", .55, .18, 12.1, .45, 22, True)
    txt("A  ·  Quantitative phase image", .62, .94, 5.0, .35, 15, True)
    txt("B  ·  Raw 8-bit pixel histogram", 6.33, .94, 6.0, .35, 15, True)
    add("rect", x=1.23, y=1.41, w=3.57, h=4.28, fill="#FFFFFF", stroke="#596873", sw=.8)
    add("image", path="data/cell_scikit_image_v026.png", x=1.24, y=1.42, w=3.55, h=4.26,
        image_ref="cell_raw", processing_ref="display_1")
    # 10 µm / 0.107 µm per pixel = 93.458 pixels; displayed at 3.55 / 550 inch per pixel.
    bar_in = (10 / .107) * 3.55 / 550
    add("line", x1=3.95-bar_in, y1=5.30, x2=3.95, y2=5.30, color="#FFFFFF", sw=3)
    txt("10 µm", 3.23, 5.37, .90, .26, 11, True, "#FFFFFF", "center")
    txt("Full field · 550 × 660 px · 0.107 µm/px", .81, 5.86, 4.88, .32, 11.5)
    txt("No crop, stitch, LUT or intensity adjustment", .81, 6.18, 4.88, .32, 11.5)

    x0, y0, w, h = 6.53, 1.62, 5.77, 3.90
    add("line", x1=x0, y1=y0+h, x2=x0+w, y2=y0+h, color="#394A53", sw=1)
    add("line", x1=x0, y1=y0, x2=x0, y2=y0+h, color="#394A53", sw=1)
    max_count = max(bins)
    gap = .035
    bw = w/16
    for index, count in enumerate(bins):
        bh = h * count / max_count
        add("rect", x=x0+index*bw+gap, y=y0+h-bh, w=bw-2*gap, h=bh,
            fill="#376F75", stroke="#376F75", sw=.2, histogram_bin=index,
            intensity_range=[index*16, index*16+15], pixel_count=count, image_ref="cell_raw")
    for value in (0, 64, 128, 192, 255):
        x = x0 + w*value/255
        add("line", x1=x, y1=y0+h, x2=x, y2=y0+h+.08, color="#394A53", sw=.7)
        txt(value, x-.36, y0+h+.12, .72, .25, 10.5, align="center")
    txt("Pixel intensity (0–255, arbitrary image units)", 7.10, 5.94, 4.9, .30, 11.5, True, align="center")
    txt(f"Pixels ≥128: {high:,} / {sum(hist):,} ({high/sum(hist):.1%})", 6.49, 6.37, 5.9, .34, 12, True)
    txt("Descriptive threshold only; no cell segmentation or biological replicate.", .61, 6.89, 12.1, .27, 10.5)
    spec = enrich_spec({
        "id": STEM, "version": "7.6.0-dev", "canvas": {"width_in": 13.333, "height_in": 7.5},
        "style": {"font": "Arial"},
        "image_contract": {
            "source_id": "cell_raw", "source_file": "data/cell_scikit_image_v026.png",
            "source_sha256": SHA256, "source_url": "https://scikit-image.org/docs/stable/api/skimage.data.html#skimage.data.cell",
            "license": "CC0", "pixel_spacing_um": .107, "original_size_px": [550, 660],
            "display": {"crop_xywh_px": [0, 0, 550, 660], "stitching": "none", "lut": "grayscale",
                        "intensity_transform": "none", "gamma": 1, "interpolation": "PowerPoint/renderer default; no pixel inference from preview"},
            "scale_bar": {"length_um": 10, "length_source_px": 10/.107, "length_display_in": bar_in},
            "quantification": {"image_ref": "cell_raw", "roi": "full field", "statistic": "16-bin pixel intensity histogram",
                               "threshold": threshold, "threshold_role": "descriptive display-only", "n_pixels": sum(hist),
                               "n_biological_replicates": 1, "high_pixel_count": high, "bins": bins},
            "short_description": "A grayscale cell image sits beside its raw pixel intensity histogram.",
            "long_description": "A single quantitative phase image of a cell in saline is shown in full, with a 10 µm scale bar. The adjacent histogram counts all 363,000 raw image pixels in 16 bins. A descriptive count above intensity 128 is shown; no segmentation or group comparison is claimed."
        },
        "elements": elements,
    })
    validate_spec(spec)
    output = ROOT / f"figure_specs/image/{STEM}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    render(spec, ROOT / f"examples/{STEM}.svg", ROOT / f"dist/{STEM}.pptx")
    print(f"PASS {STEM}: {sum(hist)} source pixels; {high} >= {threshold}")


if __name__ == "__main__":
    build()
