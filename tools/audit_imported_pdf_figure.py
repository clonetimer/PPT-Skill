#!/usr/bin/env python3
"""Audit source-text fidelity and native editability of a converted PDF figure.

This checks that the slide was not flattened and that labels were not lost.
It does not replace a visual comparison on the target presentation application.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import fitz
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from pdf_source_assets import collect_image_events
from source_figure_crop import apply_figure_region, drawable_intersects_region
from audit_text_geometry import _audit_source_text_paint, _text_paint_report


def _count_visible_source_drawings(page):
    """Count source marks after their bounding clip/scissor regions are applied.

    This is a conservative axis-aligned approximation. It can still count
    invisible paths inside a nonrectangular mask; visual review is mandatory.
    """
    stack, visible = [], 0
    for drawing in page.get_drawings(extended=True):
        depth = drawing.get("level", 0)
        stack = [(level, box) for level, box in stack if level < depth]
        if drawing["type"] == "clip":
            scissor = drawing.get("scissor")
            if scissor is not None:
                stack.append((depth, fitz.Rect(scissor)))
            continue
        if drawing["type"] == "group":
            continue
        if (drawing["type"] == "f" and drawing.get("seqno") == 0 and drawing["rect"].contains(page.rect)
                and drawing.get("fill") == (1, 1, 1)):
            continue
        clip_box = fitz.Rect(page.rect)
        for _, rectangle in stack:
            clip_box &= rectangle
        if not clip_box.is_empty and drawable_intersects_region(drawing, clip_box):
            visible += 1
    return visible


def audit_figure(source_pdf: Path, candidate_pptx: Path, *, page_index: int = 0,
                 figure_region: tuple[float, float, float, float] | None = None) -> dict:
    source_pdf, candidate_pptx = Path(source_pdf), Path(candidate_pptx)
    deck = Presentation(candidate_pptx)
    if len(deck.slides) != 1:
        raise ValueError("figure import must contain exactly one slide")
    slide = deck.slides[0]
    with fitz.open(source_pdf) as document:
        page = document[page_index]
        selected_region = apply_figure_region(page, figure_region)
        src_width, src_height = page.rect.width, page.rect.height
        source_vectors = len(page.get_drawings())
        visible_vectors = _count_visible_source_drawings(page)
        # Image dictionaries can include off-crop assets and can omit visible
        # XRefs. Count crop-visible paint occurrences (including repeated use
        # of one XRef), using the same recovery path as the importer.
        image_events, image_stats = collect_image_events(page, document)
        unresolved_images = image_stats["unresolved_visible_events"]
        source_pictures = len(image_events) + unresolved_images
        evidence = _audit_source_text_paint(page, slide,
                                           strict_crop_edges=selected_region is not None,
                                           image_events=image_events)
        text_paints, source_text = evidence["text_paints"], evidence["source_text"]

    vector_shapes = [
        shape for shape in slide.shapes
        if shape.shape_type in (MSO_SHAPE_TYPE.FREEFORM, MSO_SHAPE_TYPE.LINE, MSO_SHAPE_TYPE.AUTO_SHAPE)
        and shape.name not in evidence["outline_shape_names"]
    ]
    picture_shapes = [
        shape for shape in slide.shapes if shape.shape_type == MSO_SHAPE_TYPE.PICTURE
    ]
    candidate_text = evidence["candidate_text"]
    missing_text = source_text - candidate_text
    extra_text = candidate_text - source_text
    full_page_pictures = sum(
        shape.width >= deck.slide_width * .9 and shape.height >= deck.slide_height * .9
        for shape in picture_shapes
    )
    raw_ratio = len(vector_shapes) / visible_vectors if visible_vectors else 1.0
    ratio = min(1.0, raw_ratio)
    dims_match = (
        abs(deck.slide_width.pt - src_width) < .02
        and abs(deck.slide_height.pt - src_height) < .02
    )
    checks = {
        "labels_preserved": not missing_text,
        "source_text_paint_supported": (
            text_paints["unsupported"] == 0 and evidence["complete"] and not evidence["errors"]),
        "source_text_rendering_preserved": not evidence["render_mismatches"] and not evidence["identity_errors"],
        "source_paint_order_preserved": not evidence["paint_order_mismatches"],
        "native_vectors_preserved": ratio >= .9,
        "not_flattened": full_page_pictures == 0,
        "aspect_ratio_and_dimensions_preserved": dims_match,
        "source_pictures_retained": (
            unresolved_images == 0 and len(picture_shapes) >= source_pictures
        ),
    }
    status = ("FAIL" if not all(checks.values()) else
              "NEEDS_REVIEW" if evidence["paint_order_status"] == "NEEDS_REVIEW" else "PASS")
    return {
        "status": status,
        "checks": checks,
        "source_sha256": hashlib.sha256(source_pdf.read_bytes()).hexdigest(),
        "source_drawings": source_vectors,
        "visible_source_drawings": visible_vectors,
        "native_vectors": len(vector_shapes),
        "vector_retention_ratio": round(ratio, 5),
        "source_text_spans": sum(source_text.values()),
        "source_text_visibility": dict(text_paints),
        "candidate_text_shapes": sum(candidate_text.values()),
        "missing_text": dict(missing_text),
        "extra_text": dict(extra_text),
        "source_pictures": source_pictures,
        "source_image_paint_events": image_stats["source_paint_events"],
        "unresolved_source_image_events": unresolved_images,
        "image_extraction": image_stats,
        "picture_shapes": len(picture_shapes),
        "full_page_pictures": full_page_pictures,
        "source_page_pt": [round(src_width, 3), round(src_height, 3)],
        "figure_region_pt": selected_region,
        "candidate_page_pt": [round(deck.slide_width.pt, 3), round(deck.slide_height.pt, 3)],
        **_text_paint_report(evidence),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_pdf", type=Path)
    parser.add_argument("candidate_pptx", type=Path)
    parser.add_argument("--page", type=int, default=1, help="1-based source PDF page")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    summary = audit_figure(args.source_pdf, args.candidate_pptx, page_index=args.page - 1)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if summary["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
