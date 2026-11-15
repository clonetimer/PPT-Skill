"""Validate and apply one source-figure crop consistently across PDF readers.

Regions use PDF points in the original selected page's unrotated visible
coordinate system. The page is modified only in the in-memory opened document;
the original PDF on disk remains untouched.
"""
from __future__ import annotations

import math

import fitz


def validate_figure_region(
    page: fitz.Page,
    figure_region: tuple[float, float, float, float] | None,
) -> list[float] | None:
    """Return exactly validated source bounds without modifying the page.

    Rotated pages require a separate coordinate transform and are explicitly
    unsupported for a selected subregion. Silently cropping the wrong region
    would undermine source-grounded scientific fidelity.
    """
    if figure_region is None:
        return None
    if page.rotation:
        raise ValueError("UNSUPPORTED_ROTATED_SOURCE_CROP")
    if (not isinstance(figure_region, (tuple, list)) or len(figure_region) != 4 or
            any(isinstance(v, bool) or not isinstance(v, (float, int)) or
                not math.isfinite(float(v)) for v in figure_region)):
        raise ValueError("INVALID_FIGURE_REGION: four finite PDF-point coordinates required")

    x0, y0, x1, y1 = [float(v) for v in figure_region]
    visible = page.rect
    if (x0 < 0 or y0 < 0 or x1 > visible.width or y1 > visible.height or
            x1 <= x0 or y1 <= y0):
        raise ValueError("INVALID_FIGURE_REGION: outside selected source page")

    return [x0, y0, x1, y1]


def apply_figure_region(
    page: fitz.Page,
    figure_region: tuple[float, float, float, float] | None,
) -> list[float] | None:
    """Validate and apply an in-memory crop; original source bytes are safe."""
    bounds = validate_figure_region(page, figure_region)
    if bounds is None:
        return None
    x0, y0, x1, y1 = bounds
    # Page.cropbox may already be offset from the media box. The public API
    # consumes coordinates relative to page.rect, while set_cropbox requires
    # coordinates relative to the original unrotated media box.
    origin = page.cropbox
    page.set_cropbox(fitz.Rect(origin.x0 + x0, origin.y0 + y0,
                               origin.x0 + x1, origin.y0 + y1))
    return bounds


def drawable_intersects_region(drawing: dict, region: fitz.Rect) -> bool:
    """Include zero-height strokes and their visible width in crop preflight.

    PyMuPDF Rect.intersects returns False for horizontal/vertical lines since
    their centerline bounding rectangle has zero area. For strokes, account
    conservatively for half the line width as well.
    """
    bounds = fitz.Rect(drawing["rect"])
    thickness = float(drawing.get("width") or 0)
    pad = max(0.0, thickness / 2) if drawing.get("type") in ("s", "fs") else 0.0
    return (bounds.x0 - pad <= region.x1 and bounds.x1 + pad >= region.x0 and
            bounds.y0 - pad <= region.y1 and bounds.y1 + pad >= region.y0)
