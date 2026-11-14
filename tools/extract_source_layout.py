#!/usr/bin/env python3
"""Extract source-observed layout, style and relation candidates from a PDF figure."""
from __future__ import annotations

from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path
import re

import fitz

from pdf_source_assets import collect_image_events


def _hex_rgb(value):
    if value is None:
        return None
    return "#{:02X}{:02X}{:02X}".format(
        *(max(0, min(255, round(float(channel) * 255))) for channel in value[:3])
    )


def _text_color(value):
    if value is None:
        return "#000000"
    return "#{:06X}".format(int(value) & 0xFFFFFF)


def _normalized(rect, region):
    rect = fitz.Rect(rect) & fitz.Rect(region)
    if rect.is_empty or rect.width <= 0 or rect.height <= 0:
        return None
    return [
        round((rect.x0 - region.x0) / region.width, 6),
        round((rect.y0 - region.y0) / region.height, 6),
        round(rect.width / region.width, 6),
        round(rect.height / region.height, 6),
    ]


def _bbox(rect):
    return [round(float(v), 3) for v in (rect.x0, rect.y0, rect.x1, rect.y1)]


def _rect_item(drawing):
    items = drawing.get("items", [])
    return len(items) == 1 and items[0][0] == "re"


def _panel_label(text):
    # Require explicit panel punctuation. A standalone one-letter span is
    # common in equations and prose and must not be promoted to panel (a).
    match = re.fullmatch(r"(?:\(([A-Za-z])\)|([A-Za-z])[.)])", text.strip())
    if not match:
        return None
    return (match.group(1) or match.group(2)).lower()


def _line_segments(drawing, region):
    for item in drawing.get("items", []):
        if item[0] != "l":
            continue
        start, end = item[1], item[2]
        if not (region.contains(start) and region.contains(end)):
            continue
        yield start, end


def _geometric_panel_candidates(rectangle_candidates, region):
    """Return review-only enclosure/alignment candidates; never confirm panels."""
    region = fitz.Rect(region)
    raw = []
    for item in rectangle_candidates:
        rect = fitz.Rect(item["rect"])
        area_fraction = rect.width * rect.height / (region.width * region.height)
        if area_fraction < .04 or area_fraction > .65:
            continue
        if rect.width < region.width * .18 or rect.height < region.height * .045:
            continue
        if any(all(abs(a-b) <= .75 for a, b in zip(rect, old["rect"]))
               for old in raw):
            continue
        raw.append({
            "rect": rect,
            "area_fraction": area_fraction,
            "source_order": item.get("seqno"),
        })

    raw.sort(key=lambda item: (item["rect"].y0, item["rect"].x0, -item["area_fraction"]))
    candidates = []
    for index, item in enumerate(raw):
        rect = item["rect"]
        parents = [
            (parent["rect"].width * parent["rect"].height, parent_index, parent)
            for parent_index, parent in enumerate(raw)
            if parent_index != index
            and parent["rect"].width * parent["rect"].height > rect.width * rect.height * 1.15
            and parent["rect"].contains(rect)
        ]
        parent_id = None
        if parents:
            _, parent_index, _ = min(parents, key=lambda value: value[0])
            parent_id = f"rect_candidate_{parent_index + 1:02d}"
        candidate_id = f"rect_candidate_{index + 1:02d}"
        candidates.append({
            "id": candidate_id,
            "candidate_type": "nested_source_enclosure" if parent_id else "source_enclosure",
            "bbox_pt": _bbox(rect),
            "bbox_normalized": _normalized(rect, region),
            "area_fraction": round(item["area_fraction"], 5),
            "source_order": item["source_order"],
            "parent_candidate_id": parent_id,
            "confidence": "medium" if item["area_fraction"] >= .08 else "low",
            "confidence_basis": "source PDF rectangular path; visual enclosure only, not proof of a scientific panel",
            "review_status": "needs_human_review",
        })

    by_id = {item["id"]: item for item in candidates}
    groups = []
    group_specs = (
        ("vertical_stack", lambda a, b:
         abs(a.x0-b.x0) <= region.width*.03 and
         abs(a.x1-b.x1) <= region.width*.03 and
         (a.y1 <= b.y0 or b.y1 <= a.y0)),
        ("horizontal_row", lambda a, b:
         abs(a.y0-b.y0) <= region.height*.03 and
         abs(a.y1-b.y1) <= region.height*.03 and
         (a.x1 <= b.x0 or b.x1 <= a.x0)),
    )
    for axis, predicate in group_specs:
        remaining = {item["id"]: fitz.Rect(item["bbox_pt"]) for item in candidates}
        while remaining:
            seed_id = next(iter(remaining))
            component = {seed_id}
            frontier = [seed_id]
            while frontier:
                current_id = frontier.pop()
                current = remaining[current_id]
                for other_id, other in remaining.items():
                    if other_id in component:
                        continue
                    if predicate(current, other):
                        component.add(other_id)
                        frontier.append(other_id)
            if len(component) >= 2:
                member_ids = sorted(
                    component,
                    key=lambda cid: (
                        fitz.Rect(by_id[cid]["bbox_pt"]).y0 if axis == "vertical_stack"
                        else fitz.Rect(by_id[cid]["bbox_pt"]).x0
                    ),
                )
                group_id = f"alignment_{axis}_{len(groups) + 1:02d}"
                groups.append({
                    "id": group_id,
                    "axis": axis,
                    "member_candidate_ids": member_ids,
                    "confidence": "medium",
                    "confidence_basis": "source rectangles have repeated aligned extents and non-overlapping intervals",
                    "review_status": "needs_human_review",
                })
                for cid in member_ids:
                    by_id[cid]["alignment_group_id"] = group_id
            for cid in component:
                remaining.pop(cid, None)

    interstitial = []
    for group in groups:
        members = [fitz.Rect(by_id[cid]["bbox_pt"]) for cid in group["member_candidate_ids"]]
        for first, second in zip(members, members[1:]):
            if group["axis"] == "vertical_stack":
                top, bottom = (first, second) if first.y0 <= second.y0 else (second, first)
                gap = bottom.y0 - top.y1
                x0, x1 = max(top.x0, bottom.x0), min(top.x1, bottom.x1)
                if gap < 5 or x1 <= x0 or gap > region.height*.4:
                    continue
                rect = fitz.Rect(x0, top.y1, x1, bottom.y0)
            else:
                left, right = (first, second) if first.x0 <= second.x0 else (second, first)
                gap = right.x0 - left.x1
                y0, y1 = max(left.y0, right.y0), min(left.y1, right.y1)
                if gap < 5 or y1 <= y0 or gap > region.width*.4:
                    continue
                rect = fitz.Rect(left.x1, y0, right.x0, y1)
            interstitial.append({
                "id": f"interstitial_{len(interstitial) + 1:02d}",
                "candidate_type": "interstitial_band",
                "bbox_pt": _bbox(rect),
                "bbox_normalized": _normalized(rect, region),
                "between_candidate_ids": group["member_candidate_ids"],
                "alignment_group_id": group["id"],
                "confidence": "low",
                "confidence_basis": "unbounded gap between aligned source enclosures; candidate only, no source border",
                "review_status": "needs_human_review",
            })

    return candidates + interstitial, groups


def extract_source_layout(source_pdf: Path, *, page_index: int = 0,
                          figure_region: tuple[float, float, float, float] | None = None) -> dict:
    """Extract observable PDF geometry; inferred panels and graph edges remain candidates."""
    source_pdf = Path(source_pdf)
    with fitz.open(source_pdf) as document:
        page = document[page_index]
        page_rect = fitz.Rect(page.rect)
        region = fitz.Rect(figure_region) if figure_region else fitz.Rect(page_rect)
        region &= page_rect
        if region.is_empty or region.width <= 0 or region.height <= 0:
            raise ValueError("figure_region must intersect the selected source page")

        drawings = page.get_drawings(extended=True)
        blocks = page.get_text("dict")["blocks"]
        image_blocks = [block for block in blocks if block["type"] == 1]
        image_events, image_stats = collect_image_events(
            page, document, image_blocks=image_blocks
        )

        layout_elements = []
        rectangle_candidates = []
        stroke_segment_candidates = []
        clipping_regions = []
        palette = Counter()
        stroke_widths = Counter()
        dash_patterns = Counter()
        font_families = Counter()
        font_sizes = Counter()
        drawing_seq_to_bbox = {}

        clip_stack = []
        for drawing in drawings:
            level = int(drawing.get("level", 0))
            clip_stack = [(depth, rect) for depth, rect in clip_stack if depth < level]
            if drawing["type"] == "clip":
                scissor = drawing.get("scissor")
                if scissor is not None:
                    clip = fitz.Rect(scissor) & region
                    if not clip.is_empty:
                        clipping_regions.append({
                            "source_order": drawing.get("seqno"),
                            "bbox_pt": _bbox(clip),
                            "bbox_normalized": _normalized(clip, region),
                            "confidence": "high",
                            "evidence": "PDF clipping path scissor",
                        })
                    clip_stack.append((level, fitz.Rect(scissor)))
                continue
            if drawing["type"] == "group":
                continue

            rect = fitz.Rect(drawing.get("rect", page_rect)) & region
            for _, clip in clip_stack:
                rect &= clip
            if rect.width < 0 or rect.height < 0 or (rect.width == 0 and rect.height == 0):
                continue
            # Horizontal/vertical strokes have a zero-height/width PDF bbox.
            # Preserve them with a minimal geometry envelope rather than
            # discarding the source relation candidate as an empty object.
            if rect.width == 0:
                rect.x0 -= .01
                rect.x1 += .01
            if rect.height == 0:
                rect.y0 -= .01
                rect.y1 += .01

            seqno = drawing.get("seqno")
            color = _hex_rgb(drawing.get("color"))
            fill = _hex_rgb(drawing.get("fill"))
            width = float(drawing.get("width") or 0)
            dashes = str(drawing.get("dashes") or "")
            if color:
                palette[color] += 1
            if fill:
                palette[fill] += 1
            if width:
                stroke_widths[round(width, 3)] += 1
            if dashes:
                dash_patterns[dashes] += 1

            element = {
                "id": f"draw_{seqno if seqno is not None else len(layout_elements)}",
                "kind": "filled_path" if drawing.get("fill") is not None else "stroke_path",
                "source_order": seqno,
                "bbox_pt": _bbox(rect),
                "bbox_normalized": _normalized(rect, region),
                "source_type": drawing.get("type"),
                "style": {
                    "stroke": color,
                    "fill": fill,
                    "stroke_width_pt": round(width, 3) if width else None,
                    "dash_pattern": dashes or None,
                    "stroke_opacity": drawing.get("stroke_opacity"),
                    "fill_opacity": drawing.get("fill_opacity"),
                },
                "semantic_role": "unclassified_source_primitive",
                "confidence": "high",
                "confidence_basis": "direct PDF drawing record and clipped bounding box",
            }
            layout_elements.append(element)
            if _rect_item(drawing) and rect.width * rect.height >= region.width * region.height * 0.04:
                rectangle_candidates.append({
                    "seqno": seqno,
                    "rect": rect,
                    "bbox_pt": _bbox(rect),
                    "bbox_normalized": _normalized(rect, region),
                    "area_fraction": round(rect.width * rect.height / (region.width * region.height), 5),
                })

            for start, end in _line_segments(drawing, region):
                stroke_segment_candidates.append({
                    "id": f"stroke_segment_candidate_{seqno}_{len(stroke_segment_candidates)}",
                    "source_order": seqno,
                    "start_pt": [round(start.x, 3), round(start.y, 3)],
                    "end_pt": [round(end.x, 3), round(end.y, 3)],
                    "start_normalized": [
                        round((start.x - region.x0) / region.width, 6),
                        round((start.y - region.y0) / region.height, 6),
                    ],
                    "end_normalized": [
                        round((end.x - region.x0) / region.width, 6),
                        round((end.y - region.y0) / region.height, 6),
                    ],
                    "stroke": color,
                    "stroke_width_pt": round(width, 3) if width else None,
                    "directedness": "undetermined",
                    "direction_evidence": [],
                    "confidence": "low",
                    "confidence_basis": "line geometry alone does not prove graph direction or scientific relation",
                })

        text_markers = []
        for block_index, block in enumerate(blocks):
            for line_index, line in enumerate(block.get("lines", [])):
                direction = line.get("dir", (1, 0))
                for span_index, span in enumerate(line.get("spans", [])):
                    try:
                        quad = fitz.recover_quad(direction, span)
                        rect = quad.rect
                    except (AttributeError, TypeError, ValueError):
                        rect = fitz.Rect(span["bbox"])
                    visible = rect & region
                    if visible.is_empty or visible.width <= 0 or visible.height <= 0:
                        continue
                    text = str(span.get("text", ""))
                    font = str(span.get("font", ""))
                    size = float(span.get("size", 0))
                    color = _text_color(span.get("color"))
                    font_families[font] += 1
                    font_sizes[round(size, 2)] += 1
                    palette[color] += 1
                    item = {
                        "id": f"text_{block_index}_{line_index}_{span_index}",
                        "kind": "text_span",
                        "source_order": None,
                        "text": text,
                        "font_family": font,
                        "font_size_pt": round(size, 3),
                        "font_flags": int(span.get("flags", 0)),
                        "color": color,
                        "direction": [round(float(direction[0]), 6), round(float(direction[1]), 6)],
                        "bbox_pt": _bbox(visible),
                        "bbox_normalized": _normalized(visible, region),
                        "semantic_role": "unclassified_source_text",
                        "confidence": "high",
                        "confidence_basis": "direct PDF text span and recovered glyph quad",
                    }
                    layout_elements.append(item)
                    label = _panel_label(text)
                    if label:
                        text_markers.append({
                            "label": label,
                            "text": text,
                            "rect": visible,
                            "bbox_pt": _bbox(visible),
                            "reading_order": (visible.y0, visible.x0, block_index, line_index, span_index),
                        })

        unlabeled_panel_candidates, alignment_groups = _geometric_panel_candidates(
            rectangle_candidates, region
        )
        panels = []
        unresolved_markers = []
        used_boundaries = set()
        # Group labels into approximate visual rows before left-to-right
        # ordering. Font metrics can shift a larger "(b)" above "(a)" by a
        # couple of points even when both labels share the same panel row.
        ordered_markers = []
        marker_rows = []
        row_tolerance = max(3.0, region.height * .04)
        for marker in sorted(text_markers, key=lambda item: item["rect"].y0):
            if not marker_rows or marker["rect"].y0 - marker_rows[-1][0]["rect"].y0 > row_tolerance:
                marker_rows.append([marker])
            else:
                marker_rows[-1].append(marker)
        for row in marker_rows:
            ordered_markers.extend(sorted(row, key=lambda item: item["rect"].x0))
        for marker in ordered_markers:
            center = fitz.Point((marker["rect"].x0 + marker["rect"].x1) / 2,
                                (marker["rect"].y0 + marker["rect"].y1) / 2)
            matches = [
                (candidate["rect"].width * candidate["rect"].height, index, candidate)
                for index, candidate in enumerate(rectangle_candidates)
                if candidate["rect"].contains(center)
            ]
            if not matches:
                unresolved_markers.append({
                    "label": marker["label"],
                    "text": marker["text"],
                    "bbox_pt": marker["bbox_pt"],
                    "confidence": "low",
                    "confidence_basis": "explicit panel-like punctuation but no enclosing source boundary",
                })
                continue
            _, boundary_index, boundary = min(matches, key=lambda item: item[0])
            used_boundaries.add(boundary_index)
            panel_rect = boundary["rect"]
            panels.append({
                "id": f"panel_{marker['label']}",
                "label": marker["label"],
                "order": len(panels) + 1,
                "bbox_pt": _bbox(panel_rect),
                "bbox_normalized": _normalized(panel_rect, region),
                "boundary_source": "explicit rectangular PDF path containing panel label",
                "confidence": "high",
                "confidence_basis": "explicit panel marker enclosed by a source PDF rectangle",
            })

        image_assets = []
        for event in image_events:
            visible = event.visible_bbox & region
            if visible.is_empty or visible.width <= 0 or visible.height <= 0:
                continue
            center = fitz.Point((visible.x0 + visible.x1) / 2, (visible.y0 + visible.y1) / 2)
            containing = [
                panel for panel in panels
                if fitz.Rect(panel["bbox_pt"]).contains(center)
            ]
            panel_candidate = containing[0]["id"] if len(containing) == 1 else None
            image_assets.append({
                "id": f"image_{event.seqno}",
                "source_order": event.seqno,
                "xref": event.xref,
                "source_kind": "xref" if event.source_kind == "xref-fallback" else "image_block",
                "sha256": hashlib.sha256(event.png).hexdigest(),
                "bbox_pt": _bbox(visible),
                "bbox_normalized": _normalized(visible, region),
                "transform": list(event.transform),
                "panel_candidate": panel_candidate,
                "confidence": "high",
            })
            layout_elements.append({
                "id": f"image_{event.seqno}",
                "kind": "image",
                "source_order": event.seqno,
                "bbox_pt": _bbox(visible),
                "bbox_normalized": _normalized(visible, region),
                "semantic_role": "unclassified_source_image",
                "confidence": "high",
                "confidence_basis": "PDF image paint event with recoverable XRef",
            })

        return {
            "schema_version": "1.0.0",
            "source": {
                "filename": source_pdf.name,
                "sha256": hashlib.sha256(source_pdf.read_bytes()).hexdigest(),
                "page_index": page_index,
            },
            "page": {
                "width_pt": round(page_rect.width, 3),
                "height_pt": round(page_rect.height, 3),
                "aspect_ratio": round(page_rect.width / page_rect.height, 6),
            },
            "figure_region_pt": _bbox(region),
            "figure_region_source": "explicit_user_crop" if figure_region is not None else "full_page_default",
            "coordinate_system": {
                "units": "PDF points",
                "origin": "top-left",
                "normalized_region": "[x, y, width, height] in 0..1 relative to figure_region_pt",
            },
            "panel_detection": {
                "status": (
                    "PARTIAL_PANEL_BOUNDARIES" if panels and unresolved_markers
                    else "EXPLICIT_MARKERS_FOUND" if panels
                    else "NO_CONFIRMED_PANEL_BOUNDARIES" if unresolved_markers
                    else "NO_EXPLICIT_PANEL_MARKERS"
                ),
                "marker_count": len(text_markers),
                "panels": panels,
                "unresolved_markers": unresolved_markers,
                "unmatched_large_rectangles": [
                    item["bbox_pt"] for index, item in enumerate(rectangle_candidates)
                    if index not in used_boundaries
                ],
                "candidate_status": "CANDIDATES_FOUND" if unlabeled_panel_candidates else "NO_GEOMETRIC_CANDIDATES",
                "unlabeled_panel_candidates": unlabeled_panel_candidates,
                "alignment_groups": alignment_groups,
            },
            "layout_elements": layout_elements,
            "stroke_segment_candidates": stroke_segment_candidates,
            "clipping_regions": clipping_regions,
            "image_assets": image_assets,
            "image_extraction": image_stats,
            "style_profile": {
                "palette": [{"color": color, "occurrences": count}
                            for color, count in palette.most_common(12)],
                "font_families": dict(font_families),
                "font_size_tiers_pt": sorted(font_sizes),
                "stroke_widths_pt": sorted(stroke_widths),
                "dash_patterns": dict(dash_patterns),
            },
            "warnings": image_stats.get("warnings", []),
            "requires_human_review": True,
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_pdf", type=Path)
    parser.add_argument("--page", type=int, default=1, help="1-based PDF page number")
    parser.add_argument("--region", type=float, nargs=4, metavar=("X0", "Y0", "X1", "Y1"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.page < 1:
        parser.error("--page must be a 1-based positive page number")
    layout = extract_source_layout(args.source_pdf, page_index=args.page - 1,
                                   figure_region=tuple(args.region) if args.region else None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(layout, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": layout["panel_detection"]["status"],
        "panels": len(layout["panel_detection"]["panels"]),
        "layout_elements": len(layout["layout_elements"]),
        "stroke_segment_candidates": len(layout["stroke_segment_candidates"]),
        "output": str(args.output),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
