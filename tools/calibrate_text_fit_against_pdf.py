#!/usr/bin/env python3
"""Compare fontTools text-fit estimates with glyph-level LibreOffice PDF geometry."""
from __future__ import annotations

import argparse
import itertools
import json
import unicodedata
from pathlib import Path
from typing import Any

import fitz
from pptx import Presentation

from text_layout_metrics import FontMetrics, MissingGlyphError, resolve_font_face

EMU_PER_POINT = 12700.0


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFC", str(value))
    value = value.replace("\u00ad", "").replace("\u00a0", " ")
    return " ".join(value.split())


def _union_bbox(boxes: list[tuple[float, float, float, float]]) -> tuple[float, float, float, float]:
    return (
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    )


def _line_char_records(line: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for span in line.get("spans", []):
        for char in span.get("chars", []):
            value = char.get("c", "")
            if not value:
                continue
            records.append({
                "c": value,
                "bbox": tuple(float(v) for v in char["bbox"]),
                "origin": tuple(float(v) for v in char["origin"]),
                "font": str(span.get("font", "")),
                "size": float(span.get("size", 14.0)),
            })
    records.sort(key=lambda item: (round(item["origin"][1] / 0.75), item["bbox"][0]))

    non_whitespace = [item for item in records if not item["c"].isspace()]
    filtered: list[dict[str, Any]] = []
    for item in records:
        if item["c"].isspace():
            x0, y0, x1, y1 = item["bbox"]
            baseline = item["origin"][1]
            placeholder = any(
                abs(other["origin"][1] - baseline) <= 0.75
                and other["bbox"][0] <= x0 + 0.1
                and other["bbox"][1] <= y0 + 0.1
                and other["bbox"][2] >= x1 - 0.1
                and other["bbox"][3] >= y1 - 0.1
                for other in non_whitespace
            )
            if placeholder:
                continue
        filtered.append(item)
    return filtered


def _collapse_with_map(
    chars: list[dict[str, Any] | None],
) -> tuple[str, list[dict[str, Any] | None]]:
    output: list[str] = []
    mapping: list[dict[str, Any] | None] = []
    pending_space = False
    for item in chars:
        if item is None:
            pending_space = bool(output)
            continue
        value = item["c"].replace("\u00a0", " ")
        if value == "\u00ad":
            continue
        if value.isspace():
            pending_space = bool(output)
            continue
        if pending_space:
            output.append(" ")
            mapping.append(None)
            pending_space = False
        output.append(value)
        mapping.append(item)
    return "".join(output), mapping


def extract_pdf_text_blocks(pdf_path: Path) -> list[list[dict[str, Any]]]:
    """Build one position-preserving text stream per page across blocks and fallback-font runs."""
    document = fitz.open(pdf_path)
    pages: list[list[dict[str, Any]]] = []
    try:
        for page in document:
            spans = [
                span
                for block in page.get_text("rawdict").get("blocks", [])
                if block.get("type") == 0
                for line in block.get("lines", [])
                for span in line.get("spans", [])
            ]
            records = _line_char_records({"spans": spans})
            if not records:
                pages.append([])
                continue
            baseline_groups: dict[int, list[dict[str, Any]]] = {}
            for item in records:
                baseline_key = round(item["origin"][1] / 0.75)
                baseline_groups.setdefault(baseline_key, []).append(item)
            flattened: list[dict[str, Any] | None] = []
            for group_index, baseline_key in enumerate(sorted(baseline_groups)):
                if group_index:
                    flattened.append(None)
                flattened.extend(sorted(
                    baseline_groups[baseline_key],
                    key=lambda item: item["bbox"][0],
                ))
            raw_text, char_map = _collapse_with_map(flattened)
            normalized = normalize_text(raw_text)
            if not normalized:
                pages.append([])
                continue
            pages.append([{
                "block_index": -1,
                "text": raw_text,
                "normalized_text": normalized,
                "char_map": char_map,
                "line_count": len(baseline_groups),
            }])
    finally:
        document.close()
    return pages


def _font_properties(shape, default_font: str) -> tuple[str, float]:
    family = default_font
    size = 14.0
    found = False
    for paragraph in shape.text_frame.paragraphs:
        for run in paragraph.runs:
            if not run.text:
                continue
            if not found:
                family = run.font.name or default_font
                size = float(run.font.size.pt) if run.font.size else 14.0
                found = True
    return family, size


def _frame_bbox_points(
    shape, page_width: float, page_height: float,
    slide_width: int, slide_height: int,
) -> tuple[float, float, float, float]:
    sx = page_width / float(slide_width)
    sy = page_height / float(slide_height)
    return (
        shape.left * sx,
        shape.top * sy,
        (shape.left + shape.width) * sx,
        (shape.top + shape.height) * sy,
    )


def _match_text(
    expected_source: str,
    blocks: list[dict[str, Any]],
    frame_bbox: tuple[float, float, float, float],
) -> tuple[dict[str, Any] | None, str]:
    """Match one- or multi-line source text within a page-wide PDF glyph stream."""
    expected_lines = [
        normalize_text(line)
        for line in str(expected_source).splitlines()
        if normalize_text(line)
    ]
    if not expected_lines:
        expected_lines = [normalize_text(expected_source)]
    frame_x = (frame_bbox[0] + frame_bbox[2]) / 2
    frame_y = (frame_bbox[1] + frame_bbox[3]) / 2

    def occurrences(needle: str) -> list[dict[str, Any]]:
        found: list[dict[str, Any]] = []
        for block in blocks:
            haystack = block["normalized_text"]
            compact_haystack = "".join(
                char for char in haystack if not char.isspace()
            )
            compact_to_source = [
                index for index, char in enumerate(haystack)
                if not char.isspace()
            ]
            compact_needle = "".join(char for char in needle if not char.isspace())

            matches: list[tuple[int, int, bool]] = []
            start = 0
            while True:
                start = haystack.find(needle, start)
                if start < 0:
                    break
                matches.append((start, start + len(needle), False))
                start += len(needle)

            if not matches and compact_needle:
                compact_start = 0
                while True:
                    compact_start = compact_haystack.find(compact_needle, compact_start)
                    if compact_start < 0:
                        break
                    compact_end = compact_start + len(compact_needle)
                    source_start = compact_to_source[compact_start]
                    source_end = compact_to_source[compact_end - 1] + 1
                    first_char = block["char_map"][source_start]
                    last_char = block["char_map"][source_end - 1]

                    def is_same_frame_continuation(compact_index: int, boundary_char: dict[str, Any], side: str) -> bool:
                        source_index = compact_to_source[compact_index]
                        neighbor = block["char_map"][source_index]
                        if neighbor is None or not neighbor["c"].isalnum():
                            return False
                        if abs(neighbor["origin"][1] - boundary_char["origin"][1]) > 0.75:
                            return False
                        left, top, right, bottom = frame_bbox
                        nx0, ny0, nx1, ny1 = neighbor["bbox"]
                        if not (
                            nx1 >= left - 1.5 and nx0 <= right + 1.5
                            and ny1 >= top - 1.5 and ny0 <= bottom + 1.5
                        ):
                            return False
                        bx0, _, bx1, _ = boundary_char["bbox"]
                        if side == "before":
                            return bx0 - nx1 <= 1.5
                        return nx0 - bx1 <= 1.5

                    before_continues = (
                        compact_start > 0
                        and is_same_frame_continuation(compact_start - 1, first_char, "before")
                    )
                    after_continues = (
                        compact_end < len(compact_to_source)
                        and is_same_frame_continuation(compact_end, last_char, "after")
                    )
                    if not (before_continues or after_continues):
                        matches.append((source_start, source_end, True))
                    compact_start += len(compact_needle)

            for source_start, source_end, whitespace_fallback in matches:
                chars = [
                    item for item in block["char_map"][source_start:source_end]
                    if item is not None
                ]
                if not chars:
                    continue
                raw_bbox = _union_bbox([item["bbox"] for item in chars])
                center_x = (raw_bbox[0] + raw_bbox[2]) / 2
                center_y = (raw_bbox[1] + raw_bbox[3]) / 2
                baseline = sum(item["origin"][1] for item in chars) / len(chars)
                distance = abs(center_x - frame_x) + abs(center_y - frame_y)
                found.append({
                    "chars": chars,
                    "raw_bbox": raw_bbox,
                    "block_index": block["block_index"],
                    "baseline": baseline,
                    "distance": distance,
                    "whitespace_fallback": whitespace_fallback,
                })
        return sorted(found, key=lambda item: item["distance"])[:16]

    line_candidates = [occurrences(line) for line in expected_lines]
    if any(not candidates for candidates in line_candidates):
        return None, "not_found"

    if len(line_candidates) == 1:
        selected = line_candidates[0][0]
        match_kind = (
            "whitespace_insensitive_exact"
            if selected["whitespace_fallback"] else "exact_substring"
        )
        selected_lines = [selected]
    else:
        valid: list[tuple[float, list[dict[str, Any]]]] = []
        for combination in itertools.product(*line_candidates):
            baselines = [item["baseline"] for item in combination]
            if any(
                later - earlier <= 0.75
                for earlier, later in zip(baselines, baselines[1:])
            ):
                continue
            centers_x = [
                (item["raw_bbox"][0] + item["raw_bbox"][2]) / 2
                for item in combination
            ]
            if max(centers_x) - min(centers_x) > max(40.0, (frame_bbox[2] - frame_bbox[0]) * 0.35):
                continue
            score = sum(item["distance"] for item in combination)
            valid.append((score, list(combination)))
        if not valid:
            return None, "not_found"
        valid.sort(key=lambda item: item[0])
        selected_lines = valid[0][1]
        match_kind = "linewise_exact"

    chars = [
        char
        for item in selected_lines
        for char in item["chars"]
    ]
    return {
        "chars": chars,
        "raw_bbox": _union_bbox([item["bbox"] for item in chars]),
        "block_index": -1,
        "line_count": len({
            round(item["origin"][1] / 0.75) for item in chars
        }),
        "pdf_fonts": sorted({item["font"] for item in chars if item["font"]}),
    }, match_kind


def _rendered_geometry(
    chars: list[dict[str, Any]],
    metrics: FontMetrics,
    default_size_pt: float,
) -> tuple[tuple[float, float, float, float], int]:
    boxes: list[tuple[float, float, float, float]] = []
    baselines: list[float] = []
    for item in chars:
        char = item["c"]
        if char.isspace():
            continue
        size = float(item.get("size") or default_size_pt)
        baseline_x, baseline_y = item["origin"]
        ink = metrics.glyph_ink_offsets_pt(char, size)
        if ink is not None:
            left, bottom, right, top = ink
            boxes.append((
                float(baseline_x) + left,
                float(baseline_y) - top,
                float(baseline_x) + right,
                float(baseline_y) - bottom,
            ))
        else:
            top_offset, bottom_offset = metrics.glyph_vertical_offsets_pt(char, size)
            x0, _, x1, _ = item["bbox"]
            boxes.append((x0, baseline_y + top_offset, x1, baseline_y + bottom_offset))
        baselines.append(float(baseline_y))
    if not boxes:
        raise ValueError("PDF_MATCH_HAS_NO_VISIBLE_GLYPHS")
    unique_baselines: list[float] = []
    for value in sorted(baselines):
        if not unique_baselines or abs(value - unique_baselines[-1]) > 0.75:
            unique_baselines.append(value)
    return _union_bbox(boxes), len(unique_baselines)


def calibrate(pptx_path: Path, pdf_path: Path, tolerance_pt: float = 1.5) -> dict:
    deck = Presentation(pptx_path)
    pdf_pages = extract_pdf_text_blocks(pdf_path)
    if len(deck.slides) != len(pdf_pages):
        raise ValueError(f"SLIDE_COUNT_MISMATCH:pptx={len(deck.slides)}:pdf={len(pdf_pages)}")

    default_font = "Arial"
    metric_cache: dict[str, FontMetrics] = {}
    results: list[dict[str, Any]] = []
    pdf_document = fitz.open(pdf_path)
    try:
        for slide_index, (slide, blocks) in enumerate(zip(deck.slides, pdf_pages), 1):
            page = pdf_document[slide_index - 1]
            page_width, page_height = float(page.rect.width), float(page.rect.height)
            for shape_index, shape in enumerate(slide.shapes, 1):
                if not getattr(shape, "has_text_frame", False) or not shape.text.strip():
                    continue
                expected = shape.text
                frame = _frame_bbox_points(
                    shape, page_width, page_height, deck.slide_width, deck.slide_height
                )
                matched, match_kind = _match_text(expected, blocks, frame)
                if matched is None:
                    results.append({
                        "slide": slide_index,
                        "shape_index": shape_index,
                        "shape_name": shape.name,
                        "text": shape.text,
                        "match": "not_found",
                        "status": "TEXT_NOT_FOUND_IN_PDF",
                    })
                    continue

                family, font_size = _font_properties(shape, default_font)
                font_path, face_index, resolved_family = resolve_font_face(family)
                cache_key = f"{font_path}#face={face_index}"
                if cache_key not in metric_cache:
                    metric_cache[cache_key] = FontMetrics(font_path, face_index=face_index)
                metrics = metric_cache[cache_key]

                frame_width_in = shape.width / 914400.0
                frame_height_in = shape.height / 914400.0
                margins = tuple(
                    float(value or 0) / EMU_PER_POINT
                    for value in (
                        shape.text_frame.margin_left,
                        shape.text_frame.margin_right,
                        shape.text_frame.margin_top,
                        shape.text_frame.margin_bottom,
                    )
                )
                metric_status = "MEASURED"
                missing_glyph_error = None
                try:
                    estimate = metrics.measure(
                        shape.text, font_size, frame_width_in, frame_height_in, margins_pt=margins
                    )
                    actual, actual_line_count = _rendered_geometry(
                        matched["chars"], metrics, font_size
                    )
                except MissingGlyphError as error:
                    estimate = None
                    actual = matched["raw_bbox"]
                    actual_line_count = matched["line_count"]
                    metric_status = "MISSING_GLYPH_IN_REQUESTED_FACE"
                    missing_glyph_error = str(error)

                inside = (
                    actual[0] >= frame[0] - tolerance_pt
                    and actual[1] >= frame[1] - tolerance_pt
                    and actual[2] <= frame[2] + tolerance_pt
                    and actual[3] <= frame[3] + tolerance_pt
                )
                status = "PASS" if inside else "TEXT_OUTSIDE_FRAME"
                results.append({
                    "slide": slide_index,
                    "shape_index": shape_index,
                    "shape_name": shape.name,
                    "text": shape.text,
                    "match": match_kind,
                    "pdf_block_index": matched["block_index"],
                    "pdf_fonts": matched["pdf_fonts"],
                    "font_family_requested": family,
                    "font_family_resolved": resolved_family or metrics.family_name,
                    "font_face_index": face_index,
                    "font_fallbacks": dict(metrics.fallback_fonts),
                    "font_size_pt": font_size,
                    "metric_status": metric_status,
                    "missing_glyph_error": missing_glyph_error,
                    "estimated_line_count": estimate["line_count"] if estimate else None,
                    "actual_line_count": actual_line_count,
                    "line_count_match": estimate["line_count"] == actual_line_count if estimate else None,
                    "estimated_fits": estimate["fits"] if estimate else None,
                    "frame_bbox_pt": [round(v, 3) for v in frame],
                    "rendered_text_bbox_pt": [round(v, 3) for v in actual],
                    "rendered_text_within_frame": inside,
                    "overflow_tolerance_pt": tolerance_pt,
                    "status": status,
                })
    finally:
        pdf_document.close()
        for metrics in metric_cache.values():
            metrics.close()

    missing = [item for item in results if item["match"] == "not_found"]
    outside = [item for item in results if item.get("status") == "TEXT_OUTSIDE_FRAME"]
    line_mismatch = [item for item in results if item.get("line_count_match") is False]
    metric_unavailable = [item for item in results if item.get("metric_status") != "MEASURED"]
    false_negative = [
        item for item in outside if item.get("estimated_fits") is True
    ]
    false_positive = [
        item for item in results
        if item.get("estimated_fits") is False and item.get("rendered_text_within_frame") is True
    ]
    return {
        "schema_version": "1.1.0",
        "pptx": str(pptx_path),
        "pdf": str(pdf_path),
        "status": "PASS" if not missing and not outside else "FAIL",
        "text_shapes": len(results),
        "pdf_text_matches": len(results) - len(missing),
        "missing_text_count": len(missing),
        "rendered_text_outside_frame_count": len(outside),
        "line_count_mismatch_count": len(line_mismatch),
        "font_metric_unavailable_count": len(metric_unavailable),
        "font_metric_false_negative_overflow_count": len(false_negative),
        "font_metric_false_positive_overflow_count": len(false_positive),
        "method": "Source text is matched within glyph-level PDF character streams; glyph-specific fontTools ascender/descender metrics are applied at PDF character baselines, and the resulting geometry is compared with native PPTX text-frame bounds.",
        "limitations": [
            "LibreOffice PDF text extraction is the measurement source; this is not a Microsoft PowerPoint host test.",
            "Mixed-font text boxes are estimated using their first non-empty source run; per-glyph fallback is recorded and used for vertical glyph extents.",
            "The fontTools estimator is a fast unshaped estimate; PDF baseline positions calibrate its line count and glyph vertical placement.",
            "Text ink geometry is reconstructed from selected font glyph outlines and PDF character baselines; font metrics are used only when an outline is unavailable."
        ],
        "elements": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tolerance-pt", type=float, default=1.5)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    report = calibrate(args.pptx, args.pdf, args.tolerance_pt)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        key: report[key] for key in (
            "status", "text_shapes", "pdf_text_matches", "missing_text_count",
            "rendered_text_outside_frame_count", "line_count_mismatch_count",
            "font_metric_unavailable_count", "font_metric_false_negative_overflow_count",
            "font_metric_false_positive_overflow_count",
        )
    }, ensure_ascii=False, indent=2))
    if args.strict and report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
