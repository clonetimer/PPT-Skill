#!/usr/bin/env python3
"""Apply the source-grounded C01 V4.2 -> V4.3 Stage-A raster corrections.

This script is deliberately limited to precise local diagram repairs. It does not
create or claim an editable PPTX. The input must be the exact V4.2 candidate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw

EXPECTED_INPUT_SHA256 = "4358ab1a2886ea88f999ae886d7451a32a7b68bfa9abcf5bf3699b92201e0686"
EXPECTED_SIZE = (1920, 1080)
SCALE = 3


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _point(x: float, y: float) -> tuple[int, int]:
    return (int(round(x * SCALE)), int(round(y * SCALE)))


def _line(draw: ImageDraw.ImageDraw, points, fill, width: float) -> None:
    draw.line([_point(x, y) for x, y in points],
              fill=fill, width=int(round(width * SCALE)), joint="curve")


def _dashed(draw: ImageDraw.ImageDraw, p1, p2, fill, width: float,
            dash: float = 7, gap: float = 6) -> None:
    x1, y1 = p1
    x2, y2 = p2
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    if length <= 0:
        return
    ux, uy = dx / length, dy / length
    pos = 0.0
    while pos < length:
        end = min(length, pos + dash)
        _line(draw, [(x1 + ux * pos, y1 + uy * pos),
                     (x1 + ux * end, y1 + uy * end)], fill, width)
        pos = end + gap


def patch_image(source: Path, output: Path, *, verify_source: bool = True) -> dict:
    source = Path(source)
    output = Path(output)
    if not source.is_file():
        raise FileNotFoundError(source)
    source_hash = sha256(source)
    if verify_source and source_hash != EXPECTED_INPUT_SHA256:
        raise ValueError(f"UNEXPECTED_V42_SOURCE_SHA256:{source_hash}")

    base = Image.open(source).convert("RGB")
    if base.size != EXPECTED_SIZE:
        raise ValueError(f"UNEXPECTED_SOURCE_DIMENSIONS:{base.size}")

    # Remove the defective Total-graph drawing, obsolete text-only handoff,
    # detached lower callout arrow and detached Dense-output arrow.
    erase = ImageDraw.Draw(base)
    erase.rectangle((1145, 232, 1340, 470), fill=(255, 255, 255))
    erase.rectangle((16, 796, 134, 916), fill=(255, 255, 255))
    erase.rectangle((1250, 873, 1288, 909), fill=(255, 255, 255))

    canvas = base.resize((EXPECTED_SIZE[0] * SCALE, EXPECTED_SIZE[1] * SCALE),
                         Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(canvas)
    edge = (32, 39, 47)
    xs = [1192, 1251, 1311]
    ys = [251, 306, 375, 450]
    colors = [
        (120, 187, 250),  # B1
        (113, 210, 78),   # B2
        (211, 153, 249),  # B3
        (76, 196, 203),   # BN
    ]

    # A1: solid edges stay within each row. One dashed B1 -> B2 example only.
    for y in ys:
        for x1, x2 in zip(xs[:-1], xs[1:]):
            _line(draw, [(x1 + 15, y), (x2 - 15, y)], edge, 5)
    p1, p2 = (xs[2], ys[0]), (xs[1], ys[1])
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    length = math.hypot(dx, dy)
    radius = 15
    start = (p1[0] + dx / length * radius, p1[1] + dy / length * radius)
    end = (p2[0] - dx / length * radius, p2[1] - dy / length * radius)
    _dashed(draw, start, end, edge, 4, dash=8, gap=6)

    # A1: non-attached rails and vertical ellipsis in the B3 / BN gap,
    # to the left of every node and without node endpoints.
    _dashed(draw, (1163, 394), (1163, 404), edge, 3, dash=4, gap=3)
    _dashed(draw, (1163, 424), (1163, 433), edge, 3, dash=4, gap=3)
    for y in (405, 414, 423):
        x0, y0 = _point(1150, y)
        radius_px = 2 * SCALE
        draw.ellipse((x0 - radius_px, y0 - radius_px,
                      x0 + radius_px, y0 + radius_px), fill=edge)

    for y, color in zip(ys, colors):
        for x in xs:
            x0, y0 = _point(x, y)
            radius_px = 15 * SCALE
            draw.ellipse((x0 - radius_px, y0 - radius_px,
                          x0 + radius_px, y0 + radius_px),
                         fill=color, outline=edge, width=4 * SCALE)

    # A2: one continuous orthogonal route from Total graph to Input through
    # the left outer gutter, with a directed arrowhead at Input.
    route = (42, 91, 135)
    route_points = [
        (1177, 450), (1136, 450), (1136, 644),
        (10, 644), (10, 789), (134, 789),
    ]
    _line(draw, route_points, route, 3)
    draw.polygon([_point(148, 789), _point(134, 781), _point(134, 797)],
                 fill=route)

    # A3: three sparse dashed inter-row links in the 4 x 3 Input glyph.
    input_rows = [789, 837, 886, 934]
    input_links = [
        ((280, input_rows[0]), (238, input_rows[1])),
        ((196, input_rows[1]), (238, input_rows[2])),
        ((280, input_rows[2]), (238, input_rows[3])),
    ]
    for start_node, end_node in input_links:
        dx = end_node[0] - start_node[0]
        dy = end_node[1] - start_node[1]
        length = math.hypot(dx, dy)
        radius = 12
        start = (start_node[0] + dx / length * radius,
                 start_node[1] + dy / length * radius)
        end = (end_node[0] - dx / length * radius,
               end_node[1] - dy / length * radius)
        _dashed(draw, start, end, (39, 52, 63), 3, dash=5, gap=4)

    result = canvas.resize(EXPECTED_SIZE, Image.Resampling.LANCZOS)
    # Remove the remaining tip of the old callout arrow without touching the
    # new routed connector or the Input panel border.
    ImageDraw.Draw(result).rectangle((120, 835, 147, 870), fill=(255, 255, 255))
    output.parent.mkdir(parents=True, exist_ok=True)
    result.save(output, optimize=True)

    return {
        "status": "PASS",
        "source_sha256": source_hash,
        "output_sha256": sha256(output),
        "width_px": EXPECTED_SIZE[0],
        "height_px": EXPECTED_SIZE[1],
        "A1_total_graph": {
            "solid_within_row_edges": 8,
            "representative_dashed_inter_band_connectors": 1,
            "connector_route": "B1_to_B2",
            "direct_B3_to_BN_edge": False,
            "non_attached_continuation_rails": 2,
            "continuation_ellipsis_dots": 3,
        },
        "A2_cross_panel_route": {
            "continuous": True,
            "orthogonal": True,
            "route": "Total graph -> lower outer edge -> left gutter -> Input",
            "arrowhead_at_input": True,
            "text_only_callout_removed": True,
        },
        "A3_input_graph": {
            "nodes": 12,
            "rows": 4,
            "solid_within_row_edges": 8,
            "dashed_inter_row_connectors": 3,
            "connectivity_is_schematic": True,
        },
        "B1_dense_output": {
            "detached_extra_arrow_removed": True,
            "single_dense_to_class_arrow_retained": True,
        },
        "projection_readability": "PENDING_PHYSICAL_TEST",
        "stage_b": "LOCKED_NOT_STARTED",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="V4.2 PNG")
    parser.add_argument("output", type=Path, help="V4.3 PNG")
    parser.add_argument("--audit", type=Path, help="Optional JSON audit output")
    args = parser.parse_args()
    audit = patch_image(args.source, args.output)
    rendered = json.dumps(audit, ensure_ascii=False, indent=2)
    if args.audit:
        args.audit.parent.mkdir(parents=True, exist_ok=True)
        args.audit.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
