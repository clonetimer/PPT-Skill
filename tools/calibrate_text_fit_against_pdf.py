#!/usr/bin/env python3
"""Compare fontTools text-fit estimates with actual LibreOffice PDF text geometry."""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import fitz
from pptx import Presentation

from text_layout_metrics import FontMetrics, resolve_font_face

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


def extract_pdf_text_blocks(pdf_path: Path) -> list[list[dict[str, Any]]]:
    document = fitz.open(pdf_path)
    pages: list[list[dict[str, Any]]] = []
    try:
        for page in document:
            page_blocks = []
            for block in page.get_text("dict").get("blocks", []):
                if block.get("type") != 0:
                    continue
                lines = block.get("lines", [])
                spans = [span for line in lines for span in line.get("spans", [])]
                text = "\n".join(
                    "".join(span.get("text", "") for span in line.get("spans", []))
                    for line in lines
                )
                boxes = [tuple(float(v) for v in span["bbox"]) for span in spans if span.get("text", "").strip()]
                if not normalize_text(text) or not boxes:
                    continue
                page_blocks.append({
                    "text": text,
                    "normalized_text": normalize_text(text),
                    "bbox": _union_bbox(boxes),
                    "line_count": len([line for line in lines if any(span.get("text", "").strip() for span in line.get("spans", []))]),
                    "span_count": len(spans),
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
            elif run.font.name and run.font.name != family:
                # Mixed-font text is reported using the first run; its mixed style remains visible in the report.
                pass
    return family, size


def _frame_bbox_points(shape, page_width: float, page_height: float,
                       slide_width: int, slide_height: int) -> tuple[float, float, float, float]:
    sx = page_width / float(slide_width)
    sy = page_height / float(slide_height)
    return (
        shape.left * sx,
        shape.top * sy,
        (shape.left + shape.width) * sx,
        (shape.top + shape.height) * sy,
    )


def _match_block(expected: str, blocks: list[dict[str, Any]], used: set[int],
                 frame_bbox: tuple[float, float, float, float]) -> tuple[int | None, str]:
    exact = [
        (index, block) for index, block in enumerate(blocks)
        if index not in used and block["normalized_text"] == expected
    ]
    if exact:
        x = (frame_bbox[0] + frame_bbox[2]) / 2
        y = (frame_bbox[1] + frame_bbox[3]) / 2
        selected = min(
            exact,
            key=lambda item: abs((item[1]["bbox"][0] + item[1]["bbox"][2]) / 2 - x)
            + abs((item[1]["bbox"][1] + item[1]["bbox"][3]) / 2 - y),
        )
        return selected[0], "exact"
    partial = [
        (index, block) for index, block in enumerate(blocks)
        if index not in used and expected and (
            expected in block["normalized_text"] or block["normalized_text"] in expected
        )
    ]
    if partial:
        return partial[0][0], "partial"
    return None, "not_found"


def calibrate(pptx_path: Path, pdf_path: Path, tolerance_pt: float = 1.5) -> dict:
    deck = Presentation(pptx_path)
    pdf_pages = extract_pdf_text_blocks(pdf_path)
    if len(deck.slides) != len(pdf_pages):
        raise ValueError(f"SLIDE_COUNT_MISMATCH:pptx={len(deck.slides)}:pdf={len(pdf_pages)}")

    default_font = deck.slide_master.text_styles.title_style.font.name or "Arial"
    metric_cache: dict[str, FontMetrics] = {}
    results: list[dict[str, Any]] = []
    try:
        for slide_index, (slide, blocks) in enumerate(zip(deck.slides, pdf_pages), 1):
            page = fitz.open(pdf_path)[slide_index - 1]
            page_width, page_height = float(page.rect.width), float(page.rect.height)
            page.close()
            used_blocks: set[int] = set()
            for shape_index, shape in enumerate(slide.shapes, 1):
                if not getattr(shape, "has_text_frame", False) or not shape.text.strip():
                    continue
                expected = normalize_text(shape.text)
                frame = _frame_bbox_points(
                    shape, page_width, page_height, deck.slide_width, deck.slide_height
                )
                block_index, match_kind = _match_block(expected, blocks, used_blocks, frame)
                if block_index is None:
                    results.append({
                        "slide": slide_index,
                        "shape_index": shape_index,
                        "shape_name": shape.name,
                        "text": shape.text,
                        "match": "not_found",
                        "status": "TEXT_NOT_FOUND_IN_PDF",
                    })
                    continue

                used_blocks.add(block_index)
                block = blocks[block_index]
                actual = block["bbox"]
                inside = (
                    actual[0] >= frame[0] - tolerance_pt
                    and actual[1] >= frame[1] - tolerance_pt
                    and actual[2] <= frame[2] + tolerance_pt
                    and actual[3] <= frame[3] + tolerance_pt
                )
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
                estimate = metrics.measure(
                    shape.text, font_size, frame_width_in, frame_height_in, margins_pt=margins
                )
                status = "PASS" if inside else "TEXT_OUTSIDE_FRAME"
                results.append({
                    "slide": slide_index,
                    "shape_index": shape_index,
                    "shape_name": shape.name,
                    "text": shape.text,
                    "match": match_kind,
                    "font_family_requested": family,
                    "font_family_resolved": resolved_family or metrics.family_name,
                    "font_face_index": face_index,
                    "font_size_pt": font_size,
                    "estimated_line_count": estimate["line_count"],
                    "actual_line_count": block["line_count"],
                    "line_count_match": estimate["line_count"] == block["line_count"],
                    "estimated_fits": estimate["fits"],
                    "frame_bbox_pt": [round(v, 3) for v in frame],
                    "rendered_text_bbox_pt": [round(v, 3) for v in actual],
                    "rendered_text_within_frame": inside,
                    "overflow_tolerance_pt": tolerance_pt,
                    "status": status,
                })
    finally:
        for metrics in metric_cache.values():
            metrics.close()

    missing = [item for item in results if item["match"] == "not_found"]
    outside = [item for item in results if item.get("status") == "TEXT_OUTSIDE_FRAME"]
    line_mismatch = [item for item in results if item.get("line_count_match") is False]
    false_negative = [
        item for item in outside if item.get("estimated_fits") is True
    ]
    false_positive = [
        item for item in results
        if item.get("estimated_fits") is False and item.get("rendered_text_within_frame") is True
    ]
    return {
        "schema_version": "1.0.0",
        "pptx": str(pptx_path),
        "pdf": str(pdf_path),
        "status": "PASS" if not missing and not outside else "FAIL",
        "text_shapes": len(results),
        "pdf_text_matches": len(results) - len(missing),
        "missing_text_count": len(missing),
        "rendered_text_outside_frame_count": len(outside),
        "line_count_mismatch_count": len(line_mismatch),
        "font_metric_false_negative_overflow_count": len(false_negative),
        "font_metric_false_positive_overflow_count": len(false_positive),
        "method": "PDF text-span bounding boxes compared with native PPTX text-frame geometry; fontTools estimate compared against extracted rendered line count.",
        "limitations": [
            "LibreOffice PDF text extraction is the measurement source; this is not a Microsoft PowerPoint host test.",
            "Mixed-font text boxes are estimated using their first non-empty run; the full text and actual PDF bounding box remain recorded.",
            "Exact text matching may report a miss when the PDF renderer changes Unicode normalization or splits a single source box into multiple PDF text blocks.",
            "The fontTools estimator is a fast unshaped estimate; this report measures its disagreement with the rendered PDF rather than assuming equivalence."
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
            "font_metric_false_negative_overflow_count", "font_metric_false_positive_overflow_count",
        )
    }, ensure_ascii=False, indent=2))
    if args.strict and report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
