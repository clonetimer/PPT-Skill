#!/usr/bin/env python3
"""Compose one editable page from invisible regions using the existing renderer.

A page has ``id``, ``canvas`` (inches), optional ``style``/``title``/``claim``/
``sources``/``notes``, and ``regions``. Each region has ``id``, ``bounds`` with
``x, y, w, h`` in final-page inches, and a native FigureSpec in ``spec``. The
source canvas is uniformly fitted and centered inside the bounds. No frame is
drawn. Page metadata and original regions, including semantic-edge metadata,
are retained alongside the compiled, namespaced ``elements``.

Supply explicit element IDs for stability when inserting or reordering elements;
omitted IDs use their position within their own region. Include all visual
extents (such as rotated labels and stacked layers) in each source canvas.
This utility does not detect overlap, crop overflow, reflow text, assess beauty,
or reroute cross-region connectors. Revise a connector's region explicitly when
moving its endpoint regions. Prefer composing at final size: the unchanged
renderer has fixed internal margins, dash spacing and a few glyph outlines that
cannot be scaled through its primitive fields.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path
from urllib.parse import quote


class PageError(ValueError):
    """The supplied page cannot be composed without losing or guessing geometry."""


_BOX_TYPES = {"text", "rect", "ellipse", "trapezoid", "grid", "stack_grid", "graph", "image"}
_TYPES = _BOX_TYPES | {"line", "polyline", "polygon", "sensor"}
_STROKES = {"rect": 1, "ellipse": 1, "trapezoid": 1, "line": 1,
            "polyline": 1.2, "polygon": 1, "grid": .4, "stack_grid": .4, "graph": .75}


def _require(condition, message):
    if not condition:
        raise PageError(message)


def _object(value, owner):
    _require(isinstance(value, dict), f"{owner} must be an object")
    return value


def _id(value, owner):
    _require(isinstance(value, str) and bool(value.strip()), f"{owner} must be nonempty text")
    return value


def _number(value, owner, *, positive=False, nonnegative=False):
    _require(isinstance(value, (int, float)) and not isinstance(value, bool)
             and math.isfinite(value), f"{owner} must be a finite number")
    _require(not positive or value > 0, f"{owner} must be positive")
    _require(not nonnegative or value >= 0, f"{owner} must be nonnegative")
    return value


def _canvas(value, owner):
    value = _object(value, owner)
    return tuple(_number(value.get(key), f"{owner}.{key}", positive=True)
                 for key in ("width_in", "height_in"))


def _points(value, owner, minimum):
    _require(isinstance(value, (list, tuple)) and len(value) >= minimum,
             f"{owner} needs at least {minimum} points")
    for point in value:
        _require(isinstance(point, (list, tuple)) and len(point) == 2,
                 f"{owner} points must have two coordinates")
        for number in point:
            _number(number, owner)
    return value


def _element(source, scale, tx, ty, owner, font):
    element = copy.deepcopy(_object(source, owner))
    kind = element.get("type")
    _require(isinstance(kind, str) and kind in _TYPES,
             f"{owner}: unsupported primitive type {kind!r}")
    if kind in _BOX_TYPES:
        for key in ("x", "y", "w", "h"):
            value = _number(element.get(key), f"{owner}.{key}", positive=key in {"w", "h"})
            element[key] = value * scale + (tx if key == "x" else ty if key == "y" else 0)
    elif kind == "line":
        for key in ("x1", "x2", "y1", "y2"):
            value = _number(element.get(key), f"{owner}.{key}")
            element[key] = value * scale + (tx if key.startswith("x") else ty)
    elif kind in {"polyline", "polygon"}:
        points = _points(element.get("points"), f"{owner}.points", 3 if kind == "polygon" else 2)
        element["points"] = [[x * scale + tx, y * scale + ty] for x, y in points]
    else:  # sensor has an origin and an intrinsic glyph scale, not a bounding box.
        element["x"] = _number(element.get("x"), f"{owner}.x") * scale + tx
        element["y"] = _number(element.get("y"), f"{owner}.y") * scale + ty

    # Materialize the renderer's defaults before scaling them, too.
    sizes = {}
    if kind in _STROKES:
        sizes["sw"] = _STROKES[kind]
    if kind == "text":
        _require(isinstance(element.get("text"), str), f"{owner}.text must be text")
        element.setdefault("font", font)
        _id(element["font"], f"{owner}.font")
        _require(element.get("align", "center") in {"left", "center", "right"},
                 f"{owner}.align must be left, center or right")
        sizes["size"] = 14
    if kind == "rect" and "radius" in element:
        sizes["radius"] = 0
    if kind == "stack_grid":
        sizes["offset"] = .16
    if kind == "sensor":
        sizes["scale"] = 1
    if kind == "graph":
        sizes["r"] = .045
    if kind == "line" and (element.get("arrow") or "arrow_size" in element):
        sizes["arrow_size"] = .105
    for key, default in sizes.items():
        value = _number(element.get(key, default), f"{owner}.{key}",
                        positive=key in {"size", "scale", "r", "arrow_size"},
                        nonnegative=key in {"sw", "radius"})
        element[key] = value * scale
    if "rotation" in element:
        _number(element["rotation"], f"{owner}.rotation")
    if kind in {"ellipse", "trapezoid", "polyline", "graph", "image"}:
        required = {"ellipse": ("fill", "stroke"), "trapezoid": ("fill", "stroke"),
                    "polyline": ("color",), "graph": ("fill", "edge"), "image": ("path",)}
        for key in required[kind]:
            _id(element.get(key), f"{owner}.{key}")
    if kind in {"grid", "stack_grid"}:
        for key in ("rows", "cols") + (("layers",) if kind == "stack_grid" else ()):
            value = element.get(key, 5 if key == "layers" else None)
            _require(type(value) is int and value > 0, f"{owner}.{key} must be a positive integer")
    if kind == "graph":
        nodes = _points(element.get("nodes"), f"{owner}.nodes", 1)
        edges = element.get("edges")
        _require(isinstance(edges, (list, tuple)), f"{owner}.edges must be a list")
        for edge in edges:
            _require(isinstance(edge, (list, tuple)) and len(edge) == 2 and
                     all(type(i) is int and 0 <= i < len(nodes) for i in edge),
                     f"{owner}.edges has an invalid node index")
        # Node coordinates are relative to the transformed x/y/w/h, not inches.
    return element


def compile_page(page: dict) -> dict:
    """Return a native FigureSpec; never mutate the input or draw region frames."""
    _object(page, "page")
    _id(page.get("id"), "page.id")
    width, height = _canvas(page.get("canvas"), "page.canvas")
    style = _object(page.get("style", {}), "page.style")
    default_font = _id(style.get("font", "Times New Roman"), "page.style.font")
    regions = page.get("regions")
    _require(isinstance(regions, list) and regions, "page.regions must be a nonempty list")
    result = copy.deepcopy(page)
    result["style"] = copy.deepcopy(style)
    result["elements"] = []
    region_ids = set()
    for region in regions:
        _object(region, "region")
        rid = _id(region.get("id"), "region.id")
        _require(rid not in region_ids, f"duplicate region id: {rid}")
        region_ids.add(rid)
        bounds = _object(region.get("bounds"), f"{rid}.bounds")
        x, y, w, h = (_number(bounds.get(key), f"{rid}.bounds.{key}",
                             positive=key in {"w", "h"}) for key in ("x", "y", "w", "h"))
        _require(x >= 0 and y >= 0 and x + w <= width + 1e-9 and y + h <= height + 1e-9,
                 f"{rid}.bounds must fit inside the page canvas")
        spec = _object(region.get("spec"), f"{rid}.spec")
        sw, sh = _canvas(spec.get("canvas"), f"{rid}.spec.canvas")
        region_style = _object(spec.get("style", {}), f"{rid}.spec.style")
        font = _id(region_style.get("font", default_font), f"{rid}.spec.style.font")
        elements = spec.get("elements")
        _require(isinstance(elements, list), f"{rid}.spec.elements must be a list")
        scale = min(w / sw, h / sh)
        tx, ty = x + (w - sw * scale) / 2, y + (h - sh * scale) / 2
        element_ids = set()
        for index, source in enumerate(elements):
            _object(source, f"{rid}.elements[{index}]")
            eid = _id(source.get("id", f"element-{index + 1:04d}"), f"{rid}.element.id")
            _require(eid not in element_ids, f"{rid}: duplicate element id: {eid}")
            element_ids.add(eid)
            element = _element(source, scale, tx, ty, f"{rid}/{eid}", font)
            element["id"] = f"{quote(rid, safe='')}/{quote(eid, safe='')}"
            element["region_id"] = rid
            result["elements"].append(element)
    return result


def revise_region(page: dict, region_id: str, replacement: dict) -> dict:
    """Deep-copy a page and replace supplied region fields, preserving identity.

    ``replacement`` is a region-level patch such as ``{"spec": new_spec}`` or
    ``{"bounds": new_bounds}``. Supplied dictionaries replace whole fields;
    they are not recursively merged. Unmentioned fields and siblings survive.
    If the input already has compiled ``elements``, the returned elements are
    refreshed for direct renderer use. Source-only pages remain source-only.
    """
    compile_page(page)
    _object(replacement, "replacement")
    _require(set(replacement) <= {"id", "role", "bounds", "spec"},
             "replacement has unknown region fields; place primitives inside spec")
    _require("id" not in replacement or replacement["id"] == region_id,
             "a region revision cannot change its identity")
    result = copy.deepcopy(page)
    target = next((region for region in result["regions"] if region["id"] == region_id), None)
    _require(target is not None, f"unknown region id: {region_id}")
    target.update(copy.deepcopy(replacement))
    compiled = compile_page(result)
    return compiled if "elements" in page else result


def _speaker_notes(page):
    chunks = []
    for key in ("title", "claim", "sources", "notes"):
        value = page.get(key)
        if value:
            rendered = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)
            chunks.append(f"{key.capitalize()}:\n{rendered}")
    return "\n\n".join(chunks)


def render_page(page: dict, output_dir: str | Path, stem: str | None = None) -> dict[str, Path]:
    """Write compiled JSON, SVG and one-slide PPTX with source/claim notes."""
    spec = compile_page(page)
    spec['delivery_status'] = 'draft_requires_academic_delivery_gate'
    stem = _id(stem if stem is not None else page["id"], "output stem")
    _require(stem not in {".", ".."} and "/" not in stem and "\\" not in stem,
             "output stem must be a filename without path separators")
    _require(all(1 <= spec["canvas"][key] <= 56 for key in ("width_in", "height_in")),
             "PowerPoint page canvas dimensions must be within 1–56 inches")
    if __package__:
        from .render_figure_spec import render
    else:
        from render_figure_spec import render
    from pptx import Presentation

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    paths = {extension: directory / f"{stem}.{extension}" for extension in ("json", "svg", "pptx")}
    render(spec, paths["svg"], paths["pptx"])
    notes = _speaker_notes(page)
    if notes:
        deck = Presentation(paths["pptx"])
        deck.slides[0].notes_slide.notes_text_frame.text = notes
        deck.save(paths["pptx"])
    paths["json"].write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("page", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--stem")
    args = parser.parse_args()
    try:
        page = json.loads(args.page.read_text(encoding="utf-8"))
        paths = render_page(page, args.output_dir, args.stem)
    except (PageError, OSError, json.JSONDecodeError) as error:
        parser.error(str(error))
    for kind, path in paths.items():
        print(f"{kind}: {path}")


if __name__ == "__main__":
    main()
