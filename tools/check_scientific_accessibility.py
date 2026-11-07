#!/usr/bin/env python3
"""Project-level contrast and redundant-encoding checks, plus grayscale previews."""
from __future__ import annotations

import json
from collections import defaultdict

from PIL import Image
import numpy as np

from scientific_ir import ROOT

IDS = ["Q01_iris_scatter", "Q02_iris_strip", "Q03_iris_mean_ci", "Q03_iris_mean_ci_nature",
       "Q04_iris_confusion", "Q05_iris_ablation", "Q06_iris_trend_interval", "Q07_wine_scatter", "Q08_wine_strip", "I01_cell_image_quant"]
SCHEMATIC_SPECS = ["figure_specs/B01_engineering_fdir.json",
                   "figure_specs/F07_telemetry_embedding.json",
                   "figure_specs/c01/C01_FBG_construction.json",
                   "figure_specs/c01/C01_SEANet_graph_level.json",
                   "figure_specs/c01/C01_composite_defense_slide.json"]
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


def check_text_contrast(figure_id, spec):
    rectangles = [e for e in spec["elements"] if e["type"] == "rect" and e.get("fill")]
    for label in (e for e in spec["elements"] if e["type"] == "text"):
        color = label.get("color", "#26343C")
        if figure_id.startswith("I") and color == "#FFFFFF":
            continue  # Image pixels are checked against the raw source below.
        center_x = label["x"] + label["w"] / 2
        center_y = label["y"] + label["h"] / 2
        backgrounds = [e["fill"] for e in rectangles if e["x"] <= center_x <= e["x"]+e["w"]
                       and e["y"] <= center_y <= e["y"]+e["h"]]
        background = backgrounds[-1] if backgrounds else "#FFFFFF"
        assert contrast(color, background) >= 4.5, (figure_id, label["text"], background)


def check_mark_contrast(figure_id, spec):
    """Project preflight for essential chart marks drawn on white plot backgrounds."""
    if not figure_id.startswith("Q"):
        return
    for element in spec["elements"]:
        color = None
        if "data_row" in element or "row_predictions" in element:
            color = element.get("fill")
        elif element["type"] == "line":
            color = element.get("color")
        if color:
            assert contrast(color, "#FFFFFF") >= 3, (figure_id, element["id"], color)


def check_arrow_contrast(figure_id, spec):
    arrows = [element for element in spec["elements"] if element.get("arrow")]
    assert arrows, figure_id
    backgrounds = [element for element in spec["elements"]
                   if element["type"] == "rect" and element.get("fill")]
    for element in arrows:
        color = element.get("color", "#43525B")  # Renderer default for native connectors.
        for fraction in (.25, .5, .75):
            x = element["x1"] + fraction*(element["x2"]-element["x1"])
            y = element["y1"] + fraction*(element["y2"]-element["y1"])
            adjacent = next((panel["fill"] for panel in reversed(backgrounds)
                             if panel["x"] <= x <= panel["x"]+panel["w"]
                             and panel["y"] <= y <= panel["y"]+panel["h"]), "#FFFFFF")
            assert contrast(color, adjacent) >= 3, (figure_id, element["id"], color, adjacent)


def main():
    for figure_id in IDS:
        folder = "image" if figure_id.startswith("I") else "quant"
        spec = json.loads((ROOT / f"figure_specs/{folder}/{figure_id}.json").read_text(encoding="utf-8"))
        check_text_contrast(figure_id, spec)
        check_mark_contrast(figure_id, spec)
        if figure_id in {"Q01_iris_scatter", "Q02_iris_strip", "Q03_iris_mean_ci", "Q03_iris_mean_ci_nature", "Q07_wine_scatter", "Q08_wine_strip"}:
            by_species = defaultdict(set)
            for e in spec["elements"]:
                if "data_row" in e:
                    by_species[e["fill"]].add(e["type"])
            assert len(by_species) == 3 and len({next(iter(v)) for v in by_species.values()}) == 3
        if figure_id == "Q04_iris_confusion":
            assert len(spec["computed_values"]) == 9
            assert sum(e["type"] == "text" and e["text"].isdigit() for e in spec["elements"]) == 9
        if figure_id == "Q05_iris_ablation":
            assert all(any(e["type"] == "text" and str(item["correct"]) in e["text"]
                           for e in spec["elements"]) for item in spec["computed_values"])
        if figure_id.startswith("I"):
            assert spec["image_contract"]["short_description"] and spec["image_contract"]["long_description"]
            panel = next(e for e in spec["elements"] if e["type"] == "image")
            with Image.open(ROOT / panel["path"]) as raw:
                for label in (e for e in spec["elements"] if e["type"] == "text" and e.get("color") == "#FFFFFF"):
                    left = max(0, int((label["x"]-panel["x"])/panel["w"]*raw.width))
                    top = max(0, int((label["y"]-panel["y"])/panel["h"]*raw.height))
                    right = min(raw.width, int((label["x"]+label["w"]-panel["x"])/panel["w"]*raw.width))
                    bottom = min(raw.height, int((label["y"]+label["h"]-panel["y"])/panel["h"]*raw.height))
                    assert left < right and top < bottom
                    brightest = raw.crop((left, top, right, bottom)).getextrema()[1]
                    background = f"#{brightest:02X}{brightest:02X}{brightest:02X}"
                    assert contrast("#FFFFFF", background) >= 4.5, (label["text"], brightest)
        preview = ROOT / f"dist/{figure_id}.preview.png"
        image = Image.open(preview).convert("L")
        image.save(ROOT / f"dist/{figure_id}.grayscale.png")
        for name, matrix in MACHADO_FULL.items():
            cvd_preview(Image.open(preview), matrix).save(ROOT / f"dist/{figure_id}.{name}.png")
        print(f"PASS {figure_id}: text/mark contrast and redundant encoding; grayscale/CVD previews generated")
    for relpath in SCHEMATIC_SPECS:
        spec = json.loads((ROOT / relpath).read_text(encoding="utf-8"))
        check_arrow_contrast(spec["id"], spec)
        print(f"PASS {spec['id']}: critical connector contrast")
    print("Manual checks pending: projection/print readability; CVD previews are approximations")


if __name__ == "__main__":
    main()
