#!/usr/bin/env python3
"""Compare fontTools text-fit estimates with glyph-level LibreOffice PDF geometry."""
from __future__ import annotations

import argparse
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
    records.sort(key=lambda item: (item["bbox"][0], item["bbox"][1]))

    non_whitespace = [item for item in records if not item["c"].isspace()]
    filtered: list[dict[str, Any]] = []
    for item in records:
        if item["c"].isspace():
            x0, y0, x1, y1 = item["bbox"]
            placeholder = any(
                min(x1, other["bbox"][2]) - max(x0, other["bbox"][0]) > 0.5
                and min(y1, other["bbox"][3]) - max(y0, other["bbox"][1]) > 0.5
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
    """Keep character positions so adjacent text boxes and fallback glyphs remain separable."""
    document = fitz.open(pdf_path)
    pages: list[list[dict[str, Any]]] = []
    try:
        for page in document:
            page_blocks: list[dict[str, Any]] = []
            for block_index, block in enumerate(page.get_text("rawdict").get("blocks", [])):
                if block.get("type") != 0:
                    continue
                line_records = [
                    records for line in block.get("lines", [])
                    if (records := _line_char_records(line))
                ]
                if not line_records:
                    continue
                flattened: list[dict[str, Any] | None] = []
                for line_index, records in enumerate(line_records):
                    if line_index:
                        flattened.append(None)
                    flattened.extend(records)
                raw_text, char_map = _collapse_with_map(flattened)
                normalized = normalize_text(raw_text)
                if not normalized:
                    continue
                page_blocks.append({
                    "block_index": block_index,
                    "text": raw_text,
                    "normalized_text": normalized,
                    "char_map": char_map,
                    "line_count": len(line_records),
                })
            pages.append(page_blocks)
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
    expected: str,
    blocks: list[dict[str, Any]],
    frame_bbox: tuple[float, float, float, float],
) -> tuple[dict[str, Any] | None, str]:
    """Find the exact source text inside a PDF block and return only its glyph records."""
    candidates: list[tuple[float, dict[str, Any]]] = []
    frame_x = (frame_bbox[0] + frame_bbox[2]) / 2
    frame_y = (frame_bbox[1] + frame_bbox[3]) / 2
    for block in blocks:
        haystack = block["normalized_text"]
        start = 0
        while True:
            start = haystack.find(expected, start)
            if start < 0:
                break
            end = start + len(expected)
            chars = [item for item in block["char_map"][start:end] if item is not None]
            if chars:
                raw_bbox = _union_bbox([item["bbox"] for item in chars])
                center_x = (raw_bbox[0] + raw_bbox[2]) / 2
                center_y = (raw_bbox[1] + raw_bbox[3]) / 2
                distance = abs(center_x - frame_x) + abs(center_y - frame_y)
                candidates.append((distance, {
                    "chars": chars,
                    "raw_bbox": raw_bbox,
                    "block_index": block["block_index"],
                    "line_count": len({
                        round(item["origin"][1] / 0.75) for item in chars
                    }),
                    "pdf_fonts": sorted({item["font"] for item in chars if item["font"]}),
                }))
            start = end
    if not candidates:
        return None, "not_found"
    candidates.sort(key=lambda item: item[0])
    return candidates[0][1], "exact_substring"


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
        top_offset, bottom_offset = metrics.glyph_vertical_offsets_pt(char, size)
        x0, _, x1, _ = item["bbox"]
        baseline_y = float(item["origin"][1])
        boxes.append((x0, baseline_y + top_offset, x1, baseline_y + bottom_offset))
        baselines.append(baseline_y)
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
                expected = normalize_text(shape.text)
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
            "PDF character x extents are retained while vertical extents are reconstructed from the selected font face metrics to avoid oversized font-wide PDF bounding boxes."
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
