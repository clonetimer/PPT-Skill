#!/usr/bin/env python3
"""Compare imported PowerPoint text geometry against source PDF glyph spans.

The audit is read-only. It distinguishes source-authored overlaps/clipping from
new geometry errors introduced by the PDF-to-PPTX importer.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import unicodedata

import fitz
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.enum.text import MSO_AUTO_SIZE

from pdf_figure_import import (
    _normalize_pdf_text, _source_font, _span_visible_fraction,
    MIN_VISIBLE_TEXT_FRACTION,
)
from source_figure_crop import apply_figure_region

EMU_PER_PT = 12700.0
DEFAULT_OVERLAP_THRESHOLD_PT = 2.16


def _walk(shapes):
    for shape in shapes:
        yield shape
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from _walk(shape.shapes)


def _source_spans(page):
    rows = []
    for block_index, block in enumerate(page.get_text("dict")["blocks"]):
        for line_index, line in enumerate(block.get("lines", [])):
            for span_index, span in enumerate(line["spans"]):
                if _span_visible_fraction(span, page.rect) < MIN_VISIBLE_TEXT_FRACTION:
                    continue
                text = _normalize_pdf_text(span.get("text", ""))
                if not text.strip():
                    continue
                try:
                    quad = fitz.recover_quad(line.get("dir", (1, 0)), span)
                    rect = quad.rect
                except (AttributeError, TypeError, ValueError):
                    quad = None
                    rect = fitz.Rect(span["bbox"])
                rows.append({
                    "text": text,
                    "font": str(span.get("font", "")),
                    "target_font": _source_font(str(span.get("font", ""))),
                    "size_pt": float(span.get("size", 0)),
                    "rotation_degrees": math.degrees(math.atan2(
                        line.get("dir", (1, 0))[1], line.get("dir", (1, 0))[0]
                    )) % 360,
                    "rect": (rect.x0, rect.y0, rect.x1, rect.y1),
                    "quad_available": quad is not None,
                    "location": [block_index, line_index, span_index],
                })
    return rows


def _candidate_text_shapes(slide):
    return [shape for shape in _walk(slide.shapes)
            if getattr(shape, "has_text_frame", False) and shape.text.strip()]


def _candidate_rect_pt(shape):
    import math
    angle = math.radians(float(shape.rotation))
    width = abs(math.cos(angle)) * shape.width + abs(math.sin(angle)) * shape.height
    height = abs(math.sin(angle)) * shape.width + abs(math.cos(angle)) * shape.height
    center_x = shape.left + shape.width / 2
    center_y = shape.top + shape.height / 2
    return ((center_x - width / 2) / EMU_PER_PT,
            (center_y - height / 2) / EMU_PER_PT,
            (center_x + width / 2) / EMU_PER_PT,
            (center_y + height / 2) / EMU_PER_PT)


def _overlap(a, b, threshold_pt):
    intersection_width = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    intersection_height = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    return intersection_width > threshold_pt and intersection_height > threshold_pt


def _out_of_bounds(rect, page_rect, tolerance_pt=0.1):
    return (rect[0] < page_rect[0] - tolerance_pt or
            rect[1] < page_rect[1] - tolerance_pt or
            rect[2] > page_rect[2] + tolerance_pt or
            rect[3] > page_rect[3] + tolerance_pt)


def _shape_font(shape):
    for paragraph in shape.text_frame.paragraphs:
        for run in paragraph.runs:
            if run.font.name:
                return run.font.name
    return None


def _shape_font_sizes(shape):
    return [float(run.font.size.pt) for paragraph in shape.text_frame.paragraphs
            for run in paragraph.runs if run.font.size is not None]


def _unicode_findings(text):
    suspicious = []
    math_glyphs = []
    for char in text:
        codepoint = f"U+{ord(char):04X}"
        category = unicodedata.category(char)
        name = unicodedata.name(char, "UNNAMED")
        if (char in ("\ufffd", "□") or category in ("Co", "Cs", "Cn") or
                (category == "Cc" and char not in "\t\n\r")):
            suspicious.append({"char": char, "codepoint": codepoint,
                               "unicode_name": name, "category": category})
        if any(token in name for token in (
            "GREEK", "SUBSCRIPT", "SUPERSCRIPT", "ARROW", "MATHEMATICAL",
            "INTEGRAL", "SUMMATION", "PARTIAL", "INFINITY", "ELEMENT OF",
            "MULTIPLICATION", "MINUS SIGN", "RADICAL",
        )):
            math_glyphs.append({"char": char, "codepoint": codepoint,
                                "unicode_name": name})
    return suspicious, math_glyphs


def audit_text_geometry(source_pdf: Path, candidate_pptx: Path, *,
                        page_index: int = 0,
                        figure_region: tuple[float, float, float, float] | None = None,
                        overlap_threshold_pt: float = DEFAULT_OVERLAP_THRESHOLD_PT) -> dict:
    source_pdf, candidate_pptx = Path(source_pdf), Path(candidate_pptx)
    if overlap_threshold_pt < 0:
        raise ValueError("overlap_threshold_pt must be non-negative")
    with fitz.open(source_pdf) as source_doc:
        page = source_doc[page_index]
        selected_region = apply_figure_region(page, figure_region)
        source_rect = (0.0, 0.0, float(page.rect.width), float(page.rect.height))
        spans = _source_spans(page)
    deck = Presentation(candidate_pptx)
    if len(deck.slides) != 1:
        raise ValueError("text geometry audit expects exactly one slide")
    shapes = _candidate_text_shapes(deck.slides[0])
    candidate_rects = [_candidate_rect_pt(shape) for shape in shapes]
    source_rects = [row["rect"] for row in spans]
    matched = min(len(spans), len(shapes))

    mismatches = []
    font_mismatches = []
    font_size_mismatches = []
    rotation_mismatches = []
    autofit_mismatches = []
    font_mappings = {}
    suspicious_glyphs = []
    math_glyphs = []
    for index in range(matched):
        expected = spans[index]["text"]
        actual = shapes[index].text.replace("\v", "\n").rstrip("\n")
        if actual != expected:
            mismatches.append({"index": index, "source": expected,
                               "candidate": actual})
        expected_angle = spans[index]["rotation_degrees"]
        actual_angle = float(shapes[index].rotation)
        angle_error = abs((actual_angle - expected_angle + 180) % 360 - 180)
        if angle_error > 0.1:
            rotation_mismatches.append({
                "index": index, "source_degrees": expected_angle,
                "candidate_degrees": actual_angle, "error_degrees": angle_error,
            })
        if shapes[index].text_frame.auto_size != MSO_AUTO_SIZE.NONE:
            autofit_mismatches.append({
                "index": index, "candidate_auto_size": str(shapes[index].text_frame.auto_size),
                "expected": "NONE", "reason": "source geometry must not be host-reflowed",
            })
        expected_font = spans[index]["target_font"]
        actual_font = _shape_font(shapes[index])
        font_mappings[spans[index]["font"]] = expected_font
        if actual_font and actual_font != expected_font:
            font_mismatches.append({"index": index,
                                    "source_font": spans[index]["font"],
                                    "expected_target_font": expected_font,
                                    "candidate_font": actual_font})
        actual_sizes = _shape_font_sizes(shapes[index])
        expected_size = spans[index]["size_pt"]
        if not actual_sizes or any(abs(value - expected_size) > 0.05 for value in actual_sizes):
            font_size_mismatches.append({
                "index": index, "source_size_pt": expected_size,
                "candidate_run_sizes_pt": actual_sizes, "tolerance_pt": 0.05,
            })
        bad, math_chars = _unicode_findings(expected)
        suspicious_glyphs.extend({**item, "span_index": index} for item in bad)
        math_glyphs.extend({**item, "span_index": index} for item in math_chars)

    source_overlaps = []
    candidate_overlaps = []
    introduced_overlaps = []
    resolved_source_overlaps = []
    for i in range(matched):
        for j in range(i + 1, matched):
            source_hit = _overlap(source_rects[i], source_rects[j], overlap_threshold_pt)
            candidate_hit = _overlap(candidate_rects[i], candidate_rects[j], overlap_threshold_pt)
            pair = {"source_indices": [i, j],
                    "source_text": [spans[i]["text"], spans[j]["text"]],
                    "candidate_text": [shapes[i].text, shapes[j].text]}
            if source_hit:
                source_overlaps.append(pair)
            if candidate_hit:
                candidate_overlaps.append(pair)
            if candidate_hit and not source_hit:
                introduced_overlaps.append(pair)
            if source_hit and not candidate_hit:
                resolved_source_overlaps.append(pair)

    source_oob = [_out_of_bounds(rect, source_rect) for rect in source_rects]
    candidate_oob = [_out_of_bounds(rect, source_rect) for rect in candidate_rects]
    source_oob_count = sum(source_oob)
    candidate_oob_count = sum(candidate_oob)
    introduced_oob = sum(candidate_oob[i] and not source_oob[i] for i in range(matched))
    inherited_oob = sum(candidate_oob[i] and source_oob[i] for i in range(matched))

    count_mismatch = len(spans) != len(shapes)
    introduced_overlap_count = len(introduced_overlaps)
    mismatch_count = len(mismatches)
    if (count_mismatch or mismatch_count or introduced_overlap_count or introduced_oob
            or font_mismatches or font_size_mismatches or rotation_mismatches or autofit_mismatches):
        status = "FAIL"
    elif suspicious_glyphs:
        status = "NEEDS_REVIEW"
    else:
        status = "PASS"

    return {
        "status": status,
        "source_sha256": hashlib.sha256(source_pdf.read_bytes()).hexdigest(),
        "candidate_sha256": hashlib.sha256(candidate_pptx.read_bytes()).hexdigest(),
        "page_size_pt": [source_rect[2], source_rect[3]],
        "figure_region_pt": selected_region,
        "source_text_span_count": len(spans),
        "candidate_text_shape_count": len(shapes),
        "matched_text_count": matched,
        "text_mismatch_count": mismatch_count,
        "text_mismatches": mismatches,
        "source_overlap_count": len(source_overlaps),
        "candidate_overlap_count": len(candidate_overlaps),
        "introduced_overlap_count": introduced_overlap_count,
        "resolved_source_overlap_count": len(resolved_source_overlaps),
        "introduced_out_of_bounds_count": introduced_oob,
        "source_out_of_bounds_count": source_oob_count,
        "candidate_out_of_bounds_count": candidate_oob_count,
        "inherited_out_of_bounds_count": inherited_oob,
        "rotation_mismatch_count": len(rotation_mismatches),
        "rotation_mismatches": rotation_mismatches,
        "rotation_tolerance_degrees": 0.1,
        "autofit_mismatch_count": len(autofit_mismatches),
        "autofit_mismatches": autofit_mismatches,
        "font_mappings": font_mappings,
        "font_mismatch_count": len(font_mismatches),
        "font_mismatches": font_mismatches,
        "font_size_mismatch_count": len(font_size_mismatches),
        "font_size_mismatches": font_size_mismatches,
        "font_size_tolerance_pt": 0.05,
        "math_glyph_count": len(math_glyphs),
        "math_glyphs": math_glyphs,
        "suspicious_glyph_count": len(suspicious_glyphs),
        "glyph_substitution_count": sum(item["char"] == "□" for item in suspicious_glyphs),
        "suspicious_glyphs": suspicious_glyphs,
        "overlap_threshold_pt": overlap_threshold_pt,
        "read_only": True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_pdf", type=Path)
    parser.add_argument("candidate_pptx", type=Path)
    parser.add_argument("--page", type=int, default=0, help="zero-based PDF page index")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = audit_text_geometry(args.source_pdf, args.candidate_pptx, page_index=args.page)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    if result["status"] == "FAIL":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
