"""Recognize four-Bezier stroked ellipses in an author vector PDF.

Converts only closed geometrically canonical ellipses. Hand-drawn loops,
compound fills, incomplete arcs and clip-dependent curves remain unchanged.
"""
from __future__ import annotations

import math


def ellipse_bounds(drawing: dict, *, tolerance: float = 0.024):
    """Return (left, top, width, height) for a true four-cubic ellipse, else None."""
    if drawing.get("type") != "s" or drawing.get("color") is None:
        return None
    items = drawing.get("items", [])
    if len(items) != 4 or any(x[0] != "c" or len(x) != 5 for x in items):
        return None
    rect = drawing.get("rect")
    if rect is None or rect.width < 8 or rect.height < 8:
        return None
    x0, y0, x1, y1 = rect.x0, rect.y0, rect.x1, rect.y1
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rx, ry = (x1 - x0) / 2, (y1 - y0) / 2
    pts = [item[1] for item in items]
    if math.dist((items[-1][4].x, items[-1][4].y),
                 (pts[0].x, pts[0].y)) > tolerance * min(rx, ry):
        return None
    for left, right in zip(items, items[1:]):
        if math.dist((left[4].x, left[4].y),
                     (right[1].x, right[1].y)) > tolerance * min(rx, ry):
            return None
    cards = [(x1, cy), (cx, y1), (x0, cy), (cx, y0)]
    matched = set()
    for p in pts:
        candidate = min(range(4), key=lambda k: math.dist((p.x, p.y), cards[k]))
        if candidate in matched or math.dist((p.x, p.y), cards[candidate]) > tolerance * max(rx, ry):
            return None
        matched.add(candidate)
    for item in items:
        p0, p1, p2, p3 = item[1:]
        for p, q in ((p0, p1), (p3, p2)):
            if abs(p.x - cx) < tolerance * rx:
                if abs(p.y - q.y) > tolerance * ry:
                    return None
            elif abs(p.y - cy) < tolerance * ry:
                if abs(p.x - q.x) > tolerance * rx:
                    return None
            else:
                return None
    return x0, y0, x1-x0, y1-y0
