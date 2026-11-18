#!/usr/bin/env python3
"""Compare imported PowerPoint text geometry against source PDF glyph spans.

The audit is read-only. It distinguishes source-authored overlaps/clipping from
new geometry errors introduced by the PDF-to-PPTX importer.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import unicodedata

import fitz
from lxml import etree
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.enum.text import MSO_AUTO_SIZE
from pptx.oxml.ns import qn
from pptx.util import Pt

from pdf_figure_import import (
    _normalize_pdf_text, _source_font, _span_visible_fraction,
    MIN_VISIBLE_TEXT_FRACTION,
)
from source_figure_crop import apply_figure_region, drawable_intersects_region
from pdf_text_visibility import TextVisibility
from pdf_source_assets import collect_image_events
from pdf_drawing_events import collect_drawing_paint_orders

EMU_PER_PT = 12700.0
DEFAULT_OVERLAP_THRESHOLD_PT = 2.16


def _walk(shapes):
    for shape in shapes:
        yield shape
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from _walk(shape.shapes)


def _raw_source_spans_for_diagnostics(page):
    """Retain the old denominator only when source event collection fails.

    These rows are diagnostics, never evidence that collection succeeded.
    """
    rows = []
    visibility = TextVisibility(page)
    for block_index, block in enumerate(page.get_text("dict")["blocks"]):
        for line_index, line in enumerate(block.get("lines", [])):
            for span_index, span in enumerate(line["spans"]):
                paint = visibility.classify(span)
                if paint == "hidden":
                    continue
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
                    "paint_visibility": paint,
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


def _source_text_evidence(page, *, strict_crop_edges=False):
    """Collect authoritative paint occurrences; unsupported input stays failed."""
    errors, events, stats = [], [], {}
    try:
        from pdf_text_events import collect_text_events
        events, stats = collect_text_events(page, strict_crop_edges=strict_crop_edges)
        if stats.get("unsupported_count", 0):
            raise ValueError("UNSUPPORTED_SOURCE_TEXT_EVENTS: collector reported unsupported occurrences")
    except (ImportError, AttributeError, KeyError, TypeError, RuntimeError, ValueError) as exc:
        stats = dict(getattr(exc, "stats", stats) or {})
        stats["unsupported_count"] = max(1, stats.get("unsupported_count", 0))
        errors.append(f"{type(exc).__name__}: {exc}")
        rows = _raw_source_spans_for_diagnostics(page)
        return {"events": [], "rows": rows, "stats": stats, "errors": errors,
                "complete": False}

    rows = []
    for event in events:
        span, line = event.span, event.line
        text = _normalize_pdf_text(span.get("text", ""))
        if not text.strip():
            continue
        direction = line.get("dir", (1, 0))
        try:
            quad = fitz.recover_quad(direction, span)
            rect = quad.rect
        except (AttributeError, TypeError, ValueError):
            quad, rect = None, fitz.Rect(span["bbox"])
        rows.append({
            "paint_visibility": "visible", "paint_type": event.paint_type,
            "text": text, "font": str(span.get("font", "")),
            "target_font": _source_font(str(span.get("font", ""))),
            "size_pt": float(span.get("size", 0)),
            "rotation_degrees": math.degrees(math.atan2(direction[1], direction[0])) % 360,
            "rect": tuple(rect), "quad_available": quad is not None,
            "location": event.source_id, "source_id": event.source_id,
            "source_order": event.seqno, "source_seqnos": list(event.source_seqnos),
        })
    return {"events": events, "rows": rows, "stats": stats, "errors": errors,
            "complete": True}


def _source_spans(page):
    """Compatibility entry point returning paint-event rows, not raw text blocks."""
    return _source_text_evidence(page)["rows"]


def _source_vector_order_map(page):
    """Use source IDs and seqnos, applying the source clip stack conservatively."""
    drawings = page.get_drawings(extended=True)
    canonical_orders, stats = collect_drawing_paint_orders(page, drawings=drawings)
    stack, orders = [], {}
    for index, drawing in enumerate(drawings):
        depth = drawing.get("level", 0)
        stack = [(level, box) for level, box in stack if level < depth]
        if drawing["type"] == "clip":
            if drawing.get("scissor") is not None:
                stack.append((depth, fitz.Rect(drawing["scissor"])))
            continue
        if drawing["type"] == "group":
            continue
        if (drawing["type"] == "f" and drawing.get("seqno") == 0
                and drawing["rect"].contains(page.rect) and drawing.get("fill") == (1, 1, 1)):
            continue
        clip_box = fitz.Rect(page.rect)
        for _, rectangle in stack:
            clip_box &= rectangle
        if not clip_box.is_empty and drawable_intersects_region(drawing, clip_box):
            original_seqno = drawing.get("seqno")
            name = f"draw_{original_seqno if original_seqno is not None else index}"
            orders[name] = (canonical_orders[name]["source_order"], -1, index)
    return orders, stats


def _render_signature(shape):
    """Actual native geometry/style/content, excluding all provenance metadata."""
    nodes = []
    for child in shape._element:
        if etree.QName(child).localname in ("spPr", "style", "txBody"):
            nodes.append(etree.tostring(child, method="c14n"))
    return int(shape.shape_type), tuple(nodes)


def _native_paint_matches_source(shape, event):
    """Check source RGB/opacity independently of the importer's reference build."""
    if not getattr(shape, "has_text_frame", False):
        return False
    expected_rgb = f"{int(event.span.get('color', 0)):06X}"
    expected_opacity = float(event.evidence.get("opacity", event.span.get("alpha", 255) / 255))
    observed = False
    for paragraph in shape.text_frame.paragraphs:
        for run in paragraph.runs:
            if not run.text:
                continue
            observed = True
            properties = run._r.rPr
            solid = properties.find(qn("a:solidFill")) if properties is not None else None
            color = solid.find(qn("a:srgbClr")) if solid is not None else None
            if color is None or color.get("val", "").upper() != expected_rgb:
                return False
            alpha_nodes = color.findall(qn("a:alpha"))
            try:
                if len(alpha_nodes) > 1:
                    return False
                opacity = float(alpha_nodes[0].get("val")) / 100000 if alpha_nodes else 1.0
            except (TypeError, ValueError):
                return False
            # span alpha is an 8-bit source API value; preserve that precision
            # while rejecting an absent alpha for a partially transparent run.
            if not math.isfinite(opacity) or abs(opacity - expected_opacity) > 1 / 255 + 1e-5:
                return False
    return observed


def _source_built_order(shape, default):
    # This metadata belongs to a newly constructed reference from the source
    # SVG, never to the candidate being audited. Differently colored fill and
    # stroke pieces can represent separate source sequence numbers.
    for node in shape._element.iter():
        if node.tag.endswith("}cNvPr"):
            data = json.loads(node.get("descr", "{}"))
            return data.get("source_order", default)
    return default


def _union_shape_rects(shapes):
    if not shapes:
        return None
    boxes = [_candidate_rect_pt(shape) for shape in shapes]
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def _audit_source_text_paint(page, slide, *, strict_crop_edges=False, image_events=None):
    """Shared source-grounded text and cross-class physical paint-order audit.

    Source text outlines are rebuilt from the original PDF and compared with
    actual native paths and styles. Candidate descriptions never authorize a
    label or determine its source order.
    """
    result = _source_text_evidence(page, strict_crop_edges=strict_crop_edges)
    rows, events = result["rows"], result["events"]
    shapes = list(_walk(slide.shapes))
    by_name = defaultdict(list)
    for shape in shapes:
        by_name[shape.name].append(shape)
    native_text = [s for s in shapes if getattr(s, "has_text_frame", False) and s.text.strip()]
    candidate_text = Counter(s.text.replace("\v", "\n").rstrip("\n") for s in native_text)
    try:
        orders, drawing_stats = _source_vector_order_map(page)
    except (AttributeError, KeyError, TypeError, RuntimeError, ValueError) as exc:
        orders, drawing_stats = {}, dict(getattr(exc, "stats", {}) or {})
        drawing_stats["unsupported_count"] = max(1, drawing_stats.get("unsupported_count", 0))
        result["errors"].append(f"{type(exc).__name__}: {exc}")
    result["drawing_stats"] = drawing_stats
    classes = {name: "vector" for name in orders}
    if image_events is None:
        image_events, image_stats = collect_image_events(page, page.parent)
        if image_stats.get("unresolved_visible_events", 0):
            result["errors"].append("UNRESOLVED_SOURCE_IMAGES: paint order cannot be fully established")
    for image in image_events:
        orders[f"image_{image.seqno}"] = (image.seqno, -1, 0)
        classes[f"image_{image.seqno}"] = "image"

    expected_native_names, expected_outline_names = set(), set()
    matches, render_mismatches, identity_errors = [], [], []
    reference = Presentation()
    reference.slide_width, reference.slide_height = Pt(page.rect.width), Pt(page.rect.height)
    reference_slide = reference.slides.add_slide(reference.slide_layouts[6])
    events_by_id = {event.source_id: event for event in events}
    if len(events_by_id) != len(events):
        result["errors"].append("DUPLICATE_SOURCE_TEXT_EVENT_ID")
    for index, row in enumerate(rows):
        event = events_by_id.get(row.get("source_id"))
        expected = []
        if event is not None:
            try:
                from pdf_figure_import import _add_text_event
                expected = _add_text_event(reference_slide, page, event)
                if not expected:
                    raise ValueError("EMPTY_SOURCE_TEXT_REFERENCE")
            except (ImportError, AttributeError, KeyError, TypeError, RuntimeError, ValueError) as exc:
                result["errors"].append(f"{row['source_id']}: {type(exc).__name__}: {exc}")
        is_outline = row.get("paint_type") == "fill_stroke"
        actual, valid = [], bool(expected)
        for piece_index, source_shape in enumerate(expected):
            name = source_shape.name
            orders[name] = (_source_built_order(source_shape, event.seqno), index, piece_index)
            classes[name] = "text_outline" if is_outline else "text"
            (expected_outline_names if is_outline else expected_native_names).add(name)
            candidates = by_name.get(name, [])
            if len(candidates) != 1:
                identity_errors.append({"source_id": name, "candidate_count": len(candidates),
                                        "reason": "source occurrence must have exactly one native shape"})
                valid = False
            if len(candidates) == 1:
                shape = candidates[0]
                actual.append(shape)
                source_style_matches = is_outline or _native_paint_matches_source(shape, event)
                if _render_signature(shape) != _render_signature(source_shape) or not source_style_matches:
                    valid = False
                    render_mismatches.append({"source_id": name, "paint_type": row.get("paint_type", "fill"),
                                              "reason": ("native geometry, style or text differs from source reference"
                                                         if source_style_matches else "font color or opacity differs from source paint")})
        # Failed source collection still reports the legacy candidate positions
        # and label denominator. It never becomes a successful fallback path.
        if event is None and index < len(native_text):
            actual = [native_text[index]]
        shape = actual[0] if actual and not is_outline else None
        text = (shape.text.replace("\v", "\n").rstrip("\n")
                if shape is not None and getattr(shape, "has_text_frame", False) else None)
        if is_outline and valid:
            text = row["text"]
            candidate_text[text] += 1
        matches.append({"shape": shape, "shapes": actual, "rect": _union_shape_rects(actual),
                        "text": text, "verified": valid, "outline": is_outline})

    if result["complete"]:
        for shape in native_text:
            if shape.name not in expected_native_names:
                identity_errors.append({"candidate_id": shape.name,
                                        "reason": "unexpected or unbound native text occurrence"})
    actual_order, unknown_nontext = [], []
    for shape in shapes:
        name = shape.name
        if name in orders:
            actual_order.append((name, orders[name]))
            object_class = classes[name]
            if (object_class == "image" and shape.shape_type != MSO_SHAPE_TYPE.PICTURE or
                    object_class == "text" and not (getattr(shape, "has_text_frame", False) and shape.text.strip()) or
                    object_class in ("vector", "text_outline") and shape.shape_type not in (
                        MSO_SHAPE_TYPE.FREEFORM, MSO_SHAPE_TYPE.LINE, MSO_SHAPE_TYPE.AUTO_SHAPE)):
                identity_errors.append({"candidate_id": name, "reason": "source object class mismatch"})
        elif not (getattr(shape, "has_text_frame", False) and shape.text.strip()):
            bounds = _candidate_rect_pt(shape)
            unknown_nontext.append({"candidate_id": name, "shape_type": int(shape.shape_type),
                                    "overlaps_source_text": any(_overlap(bounds, row["rect"], 0) for row in rows)})
    order_mismatches = []
    for (previous, previous_key), (current, current_key) in zip(actual_order, actual_order[1:]):
        if previous_key > current_key:
            order_mismatches.append({"previous_shape": previous, "current_shape": current,
                                     "source_orders": [previous_key[0], current_key[0]]})
    duplicate_known_ids = [name for name, count in Counter(name for name, _ in actual_order).items() if count > 1]
    for name in duplicate_known_ids:
        identity_errors.append({"candidate_id": name, "reason": "duplicate source object ID"})
    paint_order_status = ("FAIL" if order_mismatches or result["errors"] or identity_errors
                          else "NEEDS_REVIEW" if unknown_nontext else "PASS")
    result.update({
        "matches": matches, "source_text": Counter(row["text"] for row in rows),
        "candidate_text": candidate_text,
        "text_paints": (Counter(row["paint_visibility"] for row in rows) if not result["complete"] else
                        Counter(visible=len(rows), hidden=result["stats"].get("hidden_trace_count", 0))),
        "candidate_native_text_count": len(native_text),
        "candidate_outline_shape_count": sum(len(by_name.get(name, [])) for name in expected_outline_names),
        "outline_shape_names": expected_outline_names,
        "candidate_event_count": len(native_text) + sum(m["outline"] and bool(m["shapes"]) for m in matches),
        "render_mismatches": render_mismatches, "identity_errors": identity_errors,
        "paint_order_mismatches": order_mismatches, "paint_order_status": paint_order_status,
        "unknown_nontext_shapes": unknown_nontext,
    })
    return result


def _text_paint_report(evidence):
    """Public JSON-safe additions shared by both existing report formats."""
    return {
        "source_text_collection_complete": evidence["complete"],
        "source_text_event_stats": evidence["stats"],
        "source_text_event_errors": evidence["errors"],
        "source_text_event_count": len(evidence["rows"]),
        "source_drawing_event_stats": evidence["drawing_stats"],
        "candidate_native_text_shape_count": evidence["candidate_native_text_count"],
        "candidate_text_outline_shape_count": evidence["candidate_outline_shape_count"],
        "text_render_mismatch_count": len(evidence["render_mismatches"]),
        "text_render_mismatches": evidence["render_mismatches"],
        "source_identity_error_count": len(evidence["identity_errors"]),
        "source_identity_errors": evidence["identity_errors"],
        "paint_order_status": evidence["paint_order_status"],
        "paint_order_mismatch_count": len(evidence["paint_order_mismatches"]),
        "paint_order_mismatches": evidence["paint_order_mismatches"],
        "unverified_nontext_shape_count": len(evidence["unknown_nontext_shapes"]),
        "unverified_nontext_shapes": evidence["unknown_nontext_shapes"],
    }


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
    deck = Presentation(candidate_pptx)
    if len(deck.slides) != 1:
        raise ValueError("text geometry audit expects exactly one slide")
    with fitz.open(source_pdf) as source_doc:
        page = source_doc[page_index]
        selected_region = apply_figure_region(page, figure_region)
        source_rect = (0.0, 0.0, float(page.rect.width), float(page.rect.height))
        evidence = _audit_source_text_paint(page, deck.slides[0],
                                           strict_crop_edges=selected_region is not None)
    spans, matches = evidence["rows"], evidence["matches"]
    candidate_rects = [match["rect"] for match in matches]
    source_rects = [row["rect"] for row in spans]
    matched = sum(bool(match["shapes"]) for match in matches)

    mismatches = []
    font_mismatches = []
    font_size_mismatches = []
    rotation_mismatches = []
    autofit_mismatches = []
    font_mappings = {}
    suspicious_glyphs = []
    math_glyphs = []
    for index in range(len(spans)):
        expected = spans[index]["text"]
        actual = matches[index]["text"]
        if actual != expected:
            mismatches.append({"index": index, "source": expected,
                               "candidate": actual})
        bad, math_chars = _unicode_findings(expected)
        suspicious_glyphs.extend({**item, "span_index": index} for item in bad)
        math_glyphs.extend({**item, "span_index": index} for item in math_chars)
        expected_font = spans[index]["target_font"]
        font_mappings[spans[index]["font"]] = expected_font
        shape = matches[index]["shape"]
        if shape is None or not getattr(shape, "has_text_frame", False):
            # An outline is checked against actual source-built native paths,
            # not font metadata that a path does not possess.
            continue
        expected_angle = spans[index]["rotation_degrees"]
        actual_angle = float(shape.rotation)
        angle_error = abs((actual_angle - expected_angle + 180) % 360 - 180)
        if angle_error > 0.1:
            rotation_mismatches.append({
                "index": index, "source_degrees": expected_angle,
                "candidate_degrees": actual_angle, "error_degrees": angle_error,
            })
        if shape.text_frame.auto_size != MSO_AUTO_SIZE.NONE:
            autofit_mismatches.append({
                "index": index, "candidate_auto_size": str(shape.text_frame.auto_size),
                "expected": "NONE", "reason": "source geometry must not be host-reflowed",
            })
        actual_font = _shape_font(shape)
        if actual_font != expected_font:
            font_mismatches.append({"index": index,
                                    "source_font": spans[index]["font"],
                                    "expected_target_font": expected_font,
                                    "candidate_font": actual_font})
        actual_sizes = _shape_font_sizes(shape)
        expected_size = spans[index]["size_pt"]
        if not actual_sizes or any(abs(value - expected_size) > 0.05 for value in actual_sizes):
            font_size_mismatches.append({
                "index": index, "source_size_pt": expected_size,
                "candidate_run_sizes_pt": actual_sizes, "tolerance_pt": 0.05,
            })

    source_overlaps = []
    candidate_overlaps = []
    introduced_overlaps = []
    resolved_source_overlaps = []
    for i in range(len(spans)):
        for j in range(i + 1, len(spans)):
            source_hit = _overlap(source_rects[i], source_rects[j], overlap_threshold_pt)
            both_present = candidate_rects[i] is not None and candidate_rects[j] is not None
            candidate_hit = both_present and _overlap(candidate_rects[i], candidate_rects[j], overlap_threshold_pt)
            pair = {"source_indices": [i, j],
                    "source_text": [spans[i]["text"], spans[j]["text"]],
                    "candidate_text": [matches[i]["text"], matches[j]["text"]]}
            if source_hit:
                source_overlaps.append(pair)
            if candidate_hit:
                candidate_overlaps.append(pair)
            if candidate_hit and not source_hit:
                introduced_overlaps.append(pair)
            if source_hit and both_present and not candidate_hit:
                resolved_source_overlaps.append(pair)

    source_oob = [_out_of_bounds(rect, source_rect) for rect in source_rects]
    candidate_oob = [rect is not None and _out_of_bounds(rect, source_rect) for rect in candidate_rects]
    source_oob_count = sum(source_oob)
    candidate_oob_count = sum(candidate_oob)
    introduced_oob = sum(candidate_oob[i] and not source_oob[i] for i in range(len(spans)))
    inherited_oob = sum(candidate_oob[i] and source_oob[i] for i in range(len(spans)))

    count_mismatch = len(spans) != evidence["candidate_event_count"]
    introduced_overlap_count = len(introduced_overlaps)
    mismatch_count = len(mismatches)
    unsupported_text_paint_count = max(
        sum(row["paint_visibility"] == "unsupported" for row in spans),
        evidence["stats"].get("unsupported_count", 0), len(evidence["errors"]),
    )
    if (count_mismatch or mismatch_count or introduced_overlap_count or introduced_oob
            or font_mismatches or font_size_mismatches or rotation_mismatches or autofit_mismatches
            or unsupported_text_paint_count or evidence["render_mismatches"]
            or evidence["identity_errors"] or evidence["paint_order_mismatches"]):
        status = "FAIL"
    elif suspicious_glyphs or evidence["paint_order_status"] == "NEEDS_REVIEW":
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
        "unsupported_source_text_paint_count": unsupported_text_paint_count,
        "candidate_text_shape_count": evidence["candidate_event_count"],
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
        **_text_paint_report(evidence),
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
