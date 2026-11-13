#!/usr/bin/env python3
"""Check native PPTX radar curves against a source-grounded numeric table.

Source F1 values are NOT read from screenshots: they are stored in a frozen,
attributed CSV. Each PowerPoint radar freeform is checked by recovering its
nine vertex positions and normalizing against the author red polygon.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

DEFAULT_SERIES = [
    ("naive_qwen", "34A853"), ("naive_gpt", "66BB6A"),
    ("std_qwen", "00ACC1"), ("std_gpt", "1E88E5"),
    ("sft_qwen", "4285F4"), ("grpo_qwen", "5C6BC0"),
    ("rag_any_gpt", "7E57C2"), ("mmsearch_r1_qwen", "8E24AA"),
    ("mmgraph_agent", "EA4335"),
]


def read_source_table(path: Path) -> dict:
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 23 or len({r["dataset"] for r in rows}) != 23:
        raise ValueError("Expected exactly 23 distinct Table 3 datasets")
    names = {key for key, _ in DEFAULT_SERIES}
    result = {}
    for row in rows:
        if not names.issubset(row):
            raise ValueError(f"Missing scientific series: {row['dataset']}")
        values = {name: float(row[name]) for name in names}
        if any(not math.isfinite(v) or v < 0 for v in values.values()) or values["mmgraph_agent"] <= 0:
            raise ValueError(f"Invalid F1 value: {row['dataset']}")
        result[row["dataset"]] = values
    return result


def source_axis(axis: dict, source: dict) -> dict:
    if "dataset" in axis:
        return source[axis["dataset"]]
    names = axis.get("average_of", [])
    if len(names) < 2 or len(set(names)) != len(names):
        raise ValueError("Aggregate requires two or more distinct datasets")
    return {k: sum(source[n][k] for n in names) / len(names) for k, _ in DEFAULT_SERIES}


def shape_stroke(shape) -> str | None:
    """Read OOXML stroke color without creating missing PowerPoint line nodes.

    Accessing shape.line.color may materialize <a:ln> on shapes without an
    explicit stroke. If the deck is subsequently saved, thousands of previously
    unaffected text/icons can acquire theme-colored outlines. An audit function
    must be non-destructive even when reused inside a correction pipeline.
    """
    nodes = shape._element.xpath("./p:spPr/a:ln/a:solidFill/a:srgbClr")
    if nodes:
        return (nodes[0].get("val") or "").upper() or None
    return None


def shape_vertices(shape) -> list[tuple[float, float]]:
    if shape.shape_type != MSO_SHAPE_TYPE.FREEFORM:
        return []
    paths = shape._element.xpath(".//a:custGeom/a:pathLst/a:path")
    if len(paths) != 1:
        return []
    path = paths[0]
    width, height = float(path.get("w") or 0), float(path.get("h") or 0)
    if width == 0 or height == 0:
        return []
    pts = path.xpath("./a:moveTo/a:pt|./a:lnTo/a:pt")
    if len(pts) != 10:
        return []
    return [
        (shape.left / 914400 + shape.width / 914400 * float(pt.get("x")) / width,
         shape.top / 914400 + shape.height / 914400 * float(pt.get("y")) / height)
        for pt in pts
    ]


def audit_radar(pptx: Path, source_table: Path, manifest: Path,
                *, tolerance: float = .003, angle_tolerance: float = .004) -> dict:
    config = json.loads(Path(manifest).read_text(encoding="utf-8"))
    source = read_source_table(source_table)
    deck = Presentation(pptx)
    if len(deck.slides) != 1:
        raise ValueError("Radar candidate must contain exactly one slide")
    slide = deck.slides[0]
    colors_set = {c for _, c in DEFAULT_SERIES}
    charts = []
    for panel in config["radars"]:
        xmin, ymin, xmax, ymax = panel["bbox_inches"]
        axes = [source_axis(axis, source) for axis in panel["axes"]]
        if len(axes) != 9:
            raise ValueError("This source contains nine axes per radar")
        colors = defaultdict(list)
        for shape in slide.shapes:
            vertices = shape_vertices(shape)
            color = shape_stroke(shape)
            if not vertices or color not in colors_set:
                continue
            x, y, w, h = (v / 914400 for v in (shape.left, shape.top, shape.width, shape.height))
            if xmin <= x and ymin <= y and x + w <= xmax and y + h <= ymax:
                colors[color].append(vertices)
        if not colors.get("EA4335"):
            raise ValueError(f"Missing red reference polygon: {panel['name']}")
        red = colors["EA4335"][0][:9]
        cx = sum(pt[0] for pt in red) / 9
        cy = sum(pt[1] for pt in red) / 9
        radii = [math.dist((cx, cy), pt) for pt in red]
        if any(r < .15 for r in radii) or max(radii) - min(radii) > .003:
            raise ValueError(f"Red polygon must have a regular outer radius: {panel['name']}")
        checks = []
        for name, color in DEFAULT_SERIES:
            if color not in colors:
                raise ValueError(f"Missing {name} curve in {panel['name']}")
            expected = [axis[name] / axis["mmgraph_agent"] for axis in axes]
            worst = 0.0
            angular = 0.0
            for path in colors[color]:
                if math.dist(path[0], path[-1]) > .001:
                    raise ValueError(f"Open polygon: {panel['name']}/{name}")
                for j, point in enumerate(path[:9]):
                    dx, dy = point[0] - cx, point[1] - cy
                    norm = math.hypot(dx, dy)
                    measured = norm / radii[j]
                    worst = max(worst, abs(measured - expected[j]))
                    if norm > 1e-6:
                        ux = (red[j][0] - cx) / radii[j]
                        uy = (red[j][1] - cy) / radii[j]
                        angular = max(angular, abs(dx * uy - dy * ux) / radii[j])
            checks.append({
                "series": name, "color": color, "paths": len(colors[color]),
                "max_absolute_ratio_error": round(worst, 6),
                "max_angular_error": round(angular, 6),
                "passed": worst <= tolerance and angular <= angle_tolerance,
            })
        charts.append({
            "name": panel["name"], "axes": len(axes),
            "center_inches": [round(cx, 5), round(cy, 5)],
            "checks": checks,
            "status": "PASS" if all(s["passed"] for s in checks) else "FAIL",
        })
    return {
        "status": "PASS" if all(c["status"] == "PASS" for c in charts) else "FAIL",
        "source_dataset_count": len(source),
        "source_file_sha256": hashlib.sha256(Path(source_table).read_bytes()).hexdigest(),
        "pptx_file_sha256": hashlib.sha256(Path(pptx).read_bytes()).hexdigest(),
        "charts": charts,
        "validated_scope": "18 radar axes x 9 series: source F1-ratio geometry",
        "unvalidated_scope": [
            "Figure thumbnail artwork", "Author PDF stroke/antialiasing",
            "Small legend typography", "Office 2016 runtime"
        ],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pptx", type=Path)
    ap.add_argument("--table", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--report", type=Path)
    ap.add_argument("--tolerance", type=float, default=.003)
    args = ap.parse_args()
    result = audit_radar(args.pptx, args.table, args.manifest, tolerance=args.tolerance)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "charts": [
            {"name": c["name"], "status": c["status"],
             "max_error": max(s["max_absolute_ratio_error"] for s in c["checks"])}
            for c in result["charts"]
        ]
    }, ensure_ascii=False))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
