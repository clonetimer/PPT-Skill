"""Fail-closed budgets for native PDF figure import, without partial files."""
from __future__ import annotations
import time

DEFAULT_MAX_DRAWINGS = 10000
DEFAULT_MAX_SOURCE_SEGMENTS = 100000
DEFAULT_MAX_VERTICES = 250000
DEFAULT_MAX_SECONDS = 60.0


def assert_budget(clock_start: float, max_seconds: float) -> None:
    if max_seconds <= 0:
        raise ValueError("RESOURCE_LIMIT: time budget must be > 0")
    if time.monotonic() - clock_start > max_seconds:
        raise ValueError(f"RESOURCE_LIMIT: time exceeded {max_seconds:g} seconds")


def preflight_drawing_budget(drawings: list[dict], *, clock_start: float,
                            max_drawings: int = DEFAULT_MAX_DRAWINGS,
                            max_source_segments: int = DEFAULT_MAX_SOURCE_SEGMENTS,
                            max_vertices: int = DEFAULT_MAX_VERTICES,
                            max_seconds: float = DEFAULT_MAX_SECONDS) -> dict:
    if any(x <= 0 for x in (max_drawings, max_source_segments, max_vertices, max_seconds)):
        raise ValueError("RESOURCE_LIMIT: all resource budgets must be positive")
    assert_budget(clock_start, max_seconds)
    candidates = [d for d in drawings if d.get("type") in ("f", "fs", "s")]
    count = len(candidates)
    if count > max_drawings:
        raise ValueError(f"RESOURCE_LIMIT: drawings {count} > {max_drawings}")
    items = sum(len(d.get("items", [])) for d in candidates)
    if items > max_source_segments:
        raise ValueError(f"RESOURCE_LIMIT: source_segments {items} > {max_source_segments}")
    # Conservative estimate for cubic sampling, matching _bezier_points(max=24).
    estimate = 0
    for d in candidates:
        estimate += 1
        for item in d.get("items", []):
            estimate += 25 if item[0] == "c" else 5 if item[0] in ("re", "qu") else 2
            if estimate > max_vertices:
                raise ValueError(f"RESOURCE_LIMIT: estimated_vertices > {max_vertices}")
    assert_budget(clock_start, max_seconds)
    return dict(drawings=count, source_segments=items, estimated_vertices=estimate,
                max_drawings=max_drawings, max_source_segments=max_source_segments,
                max_vertices=max_vertices, max_seconds=max_seconds)
