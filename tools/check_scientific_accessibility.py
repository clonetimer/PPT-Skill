#!/usr/bin/env python3
"""Project-level contrast and redundant-encoding checks, plus grayscale previews."""
from __future__ import annotations

import json
from collections import defaultdict

from PIL import Image
import numpy as np

from scientific_ir import ROOT

IDS = ["Q01_iris_scatter", "Q02_iris_strip", "Q03_iris_mean_ci",
       "Q04_iris_confusion", "Q05_iris_ablation", "Q06_iris_trend_interval", "I01_cell_image_quant"]
# Full-severity Machado matrices (2009), applied in linear sRGB for screening only.
# https://doi.org/10.1109/TVCG.2009.113
# https://colour.readthedocs.io/en/latest/generated/colour.matrix_cvd_Machado2009.html
MACHADO_FULL = {
    "protanopia": np.array([[.152286, 1.052583, -.204868], [.114503, .786281, .099216],
                            [-.003882, -.048116, 1.051998]]),
    "deuteranopia": np.array([[.367322, .860646, -.227968], [.280085, .672501, .047413],
                              [-.011820, .042940, .968881]]),
}


def cvd_preview(image, matrix):
    srgb = np.asarray(image.convert("RGB"), dtype=np.float32) / 255
    linear = np.where(srgb <= .04045, srgb / 12.92, ((srgb+.055)/1.055)**2.4)
    transformed = np.clip(linear @ matrix.T, 0, 1)
    result = np.where(transformed <= .0031308, 12.92*transformed,
                      1.055*np.power(transformed, 1/2.4)-.055)
    return Image.fromarray(np.uint8(np.rint(np.clip(result, 0, 1)*255)), "RGB")


def luminance(hex_color):
    channels = [int(hex_color[i:i+2], 16)/255 for i in (1, 3, 5)]
    linear = [c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4 for c in channels]
    return sum(a*b for a, b in zip(linear, (.2126, .7152, .0722)))


def contrast(a, b):
    x, y = sorted((luminance(a), luminance(b)), reverse=True)
    return (x+.05)/(y+.05)


def main():
    for figure_id in IDS:
        folder = "image" if figure_id.startswith("I") else "quant"
        spec = json.loads((ROOT / f"figure_specs/{folder}/{figure_id}.json").read_text(encoding="utf-8"))
        for e in spec["elements"]:
            if e["type"] == "text" and e.get("color", "#26343C") != "#FFFFFF":
                assert contrast(e.get("color", "#26343C"), "#FFFFFF") >= 4.5, (figure_id, e["text"])
        if figure_id in {"Q01_iris_scatter", "Q02_iris_strip", "Q03_iris_mean_ci"}:
            by_species = defaultdict(set)
            for e in spec["elements"]:
                if "data_row" in e:
                    by_species[e["fill"]].add(e["type"])
            assert len(by_species) == 3 and len({next(iter(v)) for v in by_species.values()}) == 3
        if figure_id == "Q04_iris_confusion":
            assert len(spec["computed_values"]) == 9
            assert sum(e["type"] == "text" and e["text"].isdigit() for e in spec["elements"]) == 9
        if figure_id == "Q05_iris_ablation":
            assert all(contrast("#FFFFFF", color) >= 4.5 for color in ("#376F75", "#A45C32"))
            assert all(any(e["type"] == "text" and str(item["correct"]) in e["text"]
                           for e in spec["elements"]) for item in spec["computed_values"])
        if figure_id.startswith("I"):
            assert spec["image_contract"]["short_description"] and spec["image_contract"]["long_description"]
        preview = ROOT / f"dist/{figure_id}.preview.png"
        image = Image.open(preview).convert("L")
        image.save(ROOT / f"dist/{figure_id}.grayscale.png")
        for name, matrix in MACHADO_FULL.items():
            cvd_preview(Image.open(preview), matrix).save(ROOT / f"dist/{figure_id}.{name}.png")
        print(f"PASS {figure_id}: text contrast and redundant encoding; grayscale/CVD previews generated")
    print("Manual checks pending: image-overlay contrast and projection/print readability; previews are approximations")


if __name__ == "__main__":
    main()
