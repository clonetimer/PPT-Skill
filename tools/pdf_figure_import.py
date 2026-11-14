#!/usr/bin/env python3
"""Import author-provided vector PDF figures as native, editable PPTX objects.

The source PDF is an input, not an artifact bundled with the public Skill.
Curves are sampled into freeform vertices; mathematical typography and
multi-contour fills require visual review after export.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from io import BytesIO
import json
import math
import os
from pathlib import Path
import re
import time

import fitz
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.oxml.ns import qn
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches, Pt

from render_figure_spec import clean_theme, nofx
from pdf_ellipse_recognition import ellipse_bounds
from pdf_source_assets import collect_image_events, manifest_events
from pdf_import_budget import (
    preflight_drawing_budget, assert_budget,
    DEFAULT_MAX_DRAWINGS, DEFAULT_MAX_SOURCE_SEGMENTS,
    DEFAULT_MAX_VERTICES, DEFAULT_MAX_SECONDS,
)
from source_figure_crop import apply_figure_region, drawable_intersects_region


def _color(value):
    if value is None:
        return None
    return RGBColor(*(max(0, min(255, round(c * 255))) for c in value[:3]))


def _pt_in(value):
    return Inches(float(value) / 72.0)


def _apply_opacity(shape, opacity, *, stroke=False):
    if opacity is None or abs(opacity - 1) < 1e-6:
        return
    node = shape._element.spPr
    if stroke:
        node = node.find(qn("a:ln"))
    solid = node.find(qn("a:solidFill")) if node is not None else None
    rgb_node = solid.find(qn("a:srgbClr")) if solid is not None else None
    if rgb_node is not None:
        alpha = OxmlElement("a:alpha")
        alpha.set("val", str(round(max(0, min(1, opacity)) * 100000)))
        rgb_node.append(alpha)


def _near(p, q, tolerance=0.035):
    return math.dist((p.x, p.y), (q.x, q.y)) < tolerance


def _bezier_points(p0, p1, p2, p3):
    """Bound curve approximation by source segment length, capped at 24."""
    rough = math.dist(p0, p1) + math.dist(p1, p2) + math.dist(p2, p3)
    steps = max(6, min(24, math.ceil(rough / 8)))
    return [
        fitz.Point(
            (1-t)**3*p0.x + 3*(1-t)**2*t*p1.x + 3*(1-t)*t*t*p2.x + t**3*p3.x,
            (1-t)**3*p0.y + 3*(1-t)**2*t*p1.y + 3*(1-t)*t*t*p2.y + t**3*p3.y,
        )
        for t in (k / steps for k in range(1, steps + 1))
    ]


def _subpaths(items):
    paths = []
    current = []

    def append_segment(start, end_points):
        nonlocal current
        if current and not _near(current[-1], start):
            paths.append(current)
            current = []
        if not current:
            current.append(start)
        current.extend(end_points)

    for item in items:
        opcode = item[0]
        if opcode == "l":
            append_segment(item[1], [item[2]])
        elif opcode == "c":
            append_segment(item[1], _bezier_points(*item[1:5]))
        elif opcode == "re":
            r = item[1]
            if current:
                paths.append(current)
                current = []
            paths.append([
                fitz.Point(r.x0, r.y0), fitz.Point(r.x1, r.y0),
                fitz.Point(r.x1, r.y1), fitz.Point(r.x0, r.y1),
                fitz.Point(r.x0, r.y0),
            ])
        elif opcode == "qu":
            q = item[1]
            if current:
                paths.append(current)
                current = []
            paths.append([q.ul, q.ur, q.lr, q.ll, q.ul])
        else:
            raise ValueError(f"PDF drawing opcode not supported: {opcode}")
    if current:
        paths.append(current)
    return paths


def _clip_line_segment(a, b, rectangle):
    """Liang–Barsky clip of a line segment to a rectangular PDF scissor."""
    dx, dy = b.x - a.x, b.y - a.y
    lower, upper = 0.0, 1.0
    for p, q in (
        (-dx, a.x - rectangle.x0), (dx, rectangle.x1 - a.x),
        (-dy, a.y - rectangle.y0), (dy, rectangle.y1 - a.y),
    ):
        if abs(p) < 1e-12:
            if q < 0:
                return None
        else:
            t = q / p
            if p < 0:
                lower = max(lower, t)
            else:
                upper = min(upper, t)
            if lower > upper:
                return None
    return (
        fitz.Point(a.x + lower * dx, a.y + lower * dy),
        fitz.Point(a.x + upper * dx, a.y + upper * dy),
    )


def _clip_polyline(points, rectangle):
    paths, current = [], []
    for a, b in zip(points, points[1:]):
        section = _clip_line_segment(a, b, rectangle)
        if section is None:
            if current:
                paths.append(current)
                current = []
            continue
        first, last = section
        if current and not _near(current[-1], first):
            paths.append(current)
            current = []
        if not current:
            current.append(first)
        current.append(last)
    if current:
        paths.append(current)
    return paths


def _clip_polygon(points, rectangle):
    """Clip a possibly concave filled contour against a convex rectangle."""
    vertices = points[:-1] if len(points) > 1 and _near(points[0], points[-1]) else points[:]
    for axis, value, keep_greater in (
        (0, rectangle.x0, True), (0, rectangle.x1, False),
        (1, rectangle.y0, True), (1, rectangle.y1, False),
    ):
        if not vertices:
            break
        output = []

        def coord(p):
            return p.x if axis == 0 else p.y

        def inside(p):
            return coord(p) >= value - 1e-6 if keep_greater else coord(p) <= value + 1e-6

        def intersection(p, q):
            denominator = coord(q) - coord(p)
            t = (value - coord(p)) / denominator if abs(denominator) > 1e-12 else 0
            t = max(0, min(1, t))
            return fitz.Point(p.x + t * (q.x - p.x), p.y + t * (q.y - p.y))

        previous = vertices[-1]
        for current in vertices:
            if inside(current):
                if not inside(previous):
                    output.append(intersection(previous, current))
                output.append(current)
            elif inside(previous):
                output.append(intersection(previous, current))
            previous = current
        vertices = output
    if len(vertices) < 3:
        return []
    vertices.append(vertices[0])
    return [vertices]


def _clip_paths(paths, drawing, rectangle):
    clipped = []
    filled = drawing["type"] in ("f", "fs")
    for points in paths:
        if len(points) < 2:
            continue
        clipped.extend(
            _clip_polygon(points, rectangle) if filled else _clip_polyline(points, rectangle)
        )
    return clipped


def _shape_from_paths(slide, paths, drawing, page_rect):
    # The source PDFs sometimes paint a bleed-area white background.
    # Page clipping is represented by the slide background, not an overflow.
    if not paths:
        return None
    bounded_paths = []
    for points in paths:
        bounded = [
            fitz.Point(max(0, min(page_rect.width, p.x)), max(0, min(page_rect.height, p.y)))
            for p in points
        ]
        if len(bounded) > 1 and not all(_near(bounded[0], p) for p in bounded):
            bounded_paths.append(bounded)
    if not bounded_paths:
        return None
    start = bounded_paths[0][0]
    builder = slide.shapes.build_freeform(
        start_x=round(start.x / 72 * 10000),
        start_y=round(start.y / 72 * 10000),
        # Float scale avoids quantizing 91.44 EMUs/unit to 91 EMUs/unit.
        # Quantization drift becomes several PDF points across a wide figure.
        scale=Inches(1) / 10000,
    )
    filled = drawing["type"] in ("f", "fs") and drawing.get("fill") is not None
    for index, bounded in enumerate(bounded_paths):
        if index:
            builder.move_to(round(bounded[0].x / 72 * 10000), round(bounded[0].y / 72 * 10000))
        closed = _near(bounded[-1], bounded[0]) or filled
        builder.add_line_segments(
            [(round(p.x / 72 * 10000), round(p.y / 72 * 10000)) for p in bounded[1:]],
            close=closed,
        )
    shape = builder.convert_to_shape()
    if filled:
        shape.fill.solid()
        shape.fill.fore_color.rgb = _color(drawing["fill"])
        _apply_opacity(shape, drawing.get("fill_opacity"))
    else:
        shape.fill.background()
    if drawing["type"] in ("s", "fs") and drawing.get("color") is not None:
        shape.line.color.rgb = _color(drawing["color"])
        shape.line.width = Pt(max(.1, drawing.get("width") or .7))
        _apply_opacity(shape, drawing.get("stroke_opacity"), stroke=True)
        if drawing.get("dashes") not in (None, "[] 0", "[] 0.0"):
            shape.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    else:
        shape.line.fill.background()
    nofx(shape)
    return shape


def _add_straight_line(slide, points, drawing):
    p0, p1 = points
    s = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT,
        _pt_in(p0.x), _pt_in(p0.y), _pt_in(p1.x), _pt_in(p1.y),
    )
    s.line.color.rgb = _color(drawing.get("color") or (0, 0, 0))
    s.line.width = Pt(max(.1, drawing.get("width") or .7))
    _apply_opacity(s, drawing.get("stroke_opacity"), stroke=True)
    if drawing.get("dashes") not in (None, "[] 0", "[] 0.0"):
        s.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    nofx(s)
    return s


def _add_drawing(slide, drawing, page_rect, warnings, clip_rect=None):
    # Matplotlib/PGF PDF backends sometimes encode non-rendering or clipped
    # stroke widths of thousands of points. pptx rejects > 1584 pt, and
    # clamping would paint an enormous unrelated blot over nearby content.
    if drawing["type"] in ("s", "fs") and (drawing.get("width") or 0) > 1584:
        warnings.append(
            f"unrepresentable PDF stroke width {drawing['width']:g} pt omitted at {drawing['rect']}"
        )
        return 0
    if drawing["type"] == "f" and drawing["rect"].contains(page_rect) and drawing.get("fill") == (1, 1, 1):
        return 0  # already represented by the white page background
    # Source-canonical circles and ellipses are safer as native PowerPoint
    # ovals than as sampled open Bézier freeforms. Never reshape clipped or
    # noncanonical loops (e.g., hypergraph enclosures) into perfect circles.
    bounds = ellipse_bounds(drawing)
    if bounds is not None and (clip_rect is None or clip_rect.contains(drawing["rect"])):
        x, y, w, h = bounds
        shape = slide.shapes.add_shape(
            MSO_SHAPE.OVAL, _pt_in(x), _pt_in(y), _pt_in(w), _pt_in(h),
        )
        shape.fill.background()
        shape.line.color.rgb = _color(drawing["color"])
        shape.line.width = Pt(max(.1, drawing.get("width") or .7))
        _apply_opacity(shape, drawing.get("stroke_opacity"), stroke=True)
        if drawing.get("dashes") not in (None, "[] 0", "[] 0.0"):
            shape.line.dash_style = MSO_LINE_DASH_STYLE.DASH
        nofx(shape)
        return 1
    pieces = _subpaths(drawing["items"])
    if clip_rect is not None and not clip_rect.contains(drawing["rect"]):
        pieces = _clip_paths(pieces, drawing, clip_rect)
        if not pieces:
            return 0
    if len(pieces) > 30 and drawing["type"] in ("f", "fs"):
        warnings.append(f"filled drawing has {len(pieces)} disjoint contours; inspect holes and dashed geometry")
    if len(pieces) == 1 and len(pieces[0]) == 2 and drawing["type"] == "s":
        _add_straight_line(slide, pieces[0], drawing)
        return 1
    return int(_shape_from_paths(slide, pieces, drawing, page_rect) is not None)


def _source_font(name):
    name = re.sub(r"^[A-Z]{6}\+", "", name)
    compact = re.sub(r"[^a-z0-9]", "", name.casefold())
    if name.startswith("Georgia"):
        return "Georgia"
    if name.startswith("Times") or compact.startswith(("texgyretermes", "linlibertine")):
        return "Times New Roman"
    if name.startswith(("Helvetica", "Arial")) or compact in ("unnamedt3", "arialmt"):
        return "Arial"
    if compact.startswith("comicsansms"):
        return "Comic Sans MS"
    if compact.startswith(("calis", "calistomt")):
        return "Calisto MT"
    if compact.startswith(("latinmodernmath", "stix", "xitsmath", "cmmi", "cmsy", "cmr")):
        return "Cambria Math"
    if re.fullmatch(r"font[0-9a-f]{8,}", name, flags=re.IGNORECASE):
        # Opaque PDF resource IDs are not usable Windows font family names.
        return "Arial"
    return name.replace("-Bold", "").replace("-Italic", "").replace(" Regular", "")


def _normalize_pdf_text(text):
    # PyMuPDF decodes discretionary PDF hyphens as U+00AD. PowerPoint drops
    # them unless at a wrap point, erasing visible source names like Zero-API.
    # NUL/control characters from damaged PDF ToUnicode maps are not valid
    # PowerPoint text. Keep the location visible and require manual review.
    return (text.replace("\u00ad", "-").replace("\u00a0", " ")
            .replace("\x00", "□"))


def _span_visible_fraction(span, page_rect):
    """Fraction of a PDF text span's axis-aligned bounds visible in the page crop."""
    bbox = fitz.Rect(span["bbox"])
    if bbox.is_empty or bbox.width <= 0 or bbox.height <= 0:
        return 0.0
    visible = bbox & fitz.Rect(page_rect)
    if visible.is_empty:
        return 0.0
    return max(0.0, min(1.0, (visible.width * visible.height) / (bbox.width * bbox.height)))


MIN_VISIBLE_TEXT_FRACTION = 0.20


def _span_local_geometry(span, line):
    """Recover the oriented PDF glyph quad instead of rotating its AABB twice."""
    direction = line.get("dir", (1.0, 0.0))
    try:
        quad = fitz.recover_quad(direction, span)
        width = quad.ul.distance_to(quad.ur)
        height = quad.ul.distance_to(quad.ll)
        center = fitz.Point(
            (quad.ul.x + quad.ur.x + quad.ll.x + quad.lr.x) / 4,
            (quad.ul.y + quad.ur.y + quad.ll.y + quad.lr.y) / 4,
        )
    except (AttributeError, TypeError, ValueError):
        bbox = fitz.Rect(span["bbox"])
        width, height = bbox.width, bbox.height
        center = fitz.Point((bbox.x0 + bbox.x1) / 2, (bbox.y0 + bbox.y1) / 2)
    size = float(span["size"])
    # Minimal padding avoids PowerPoint clipping while not expanding adjacent
    # source spans into new collisions. The source glyph quad remains the anchor.
    pad_x = max(.05, size * .01)
    pad_y = max(.05, size * .01)
    width += 2 * pad_x
    height += 2 * pad_y
    return center.x - width / 2, center.y - height / 2, width, height


def _add_text(slide, span, line, page_rect=None):
    if page_rect is not None and _span_visible_fraction(span, page_rect) < MIN_VISIBLE_TEXT_FRACTION:
        return False
    content = _normalize_pdf_text(span.get("text", ""))
    if not content.strip():
        return False
    x, y, w, h = _span_local_geometry(span, line)
    shape = slide.shapes.add_textbox(_pt_in(x), _pt_in(y), _pt_in(w), _pt_in(h))
    frame = shape.text_frame
    frame.clear()
    frame.word_wrap = False
    frame.margin_left = frame.margin_right = 0
    frame.margin_top = frame.margin_bottom = 0
    frame.vertical_anchor = MSO_ANCHOR.TOP
    paragraph = frame.paragraphs[0]
    paragraph.space_after = paragraph.space_before = Pt(0)
    run = paragraph.add_run()
    run.text = content
    run.font.name = _source_font(span["font"])
    run.font.size = Pt(float(span["size"]))
    run.font.bold = bool(span.get("flags", 0) & 16) or "Bold" in span["font"]
    run.font.italic = bool(span.get("flags", 0) & 2) or "Italic" in span["font"]
    color = span.get("color")
    run.font.color.rgb = _color(((color >> 16 & 255) / 255,
                                 (color >> 8 & 255) / 255,
                                 (color & 255) / 255) if color is not None else (0, 0, 0))
    direction = line.get("dir", (1, 0))
    if abs(direction[0] - 1) > .001 or abs(direction[1]) > .001:
        shape.rotation = math.degrees(math.atan2(-direction[1], direction[0]))
    nofx(shape)
    return True



def _annotate_source_shape(shape, source_object_id, source_order, object_class):
    """Attach stable SourceLayout provenance without changing rendered geometry."""
    shape.name = str(source_object_id)
    metadata = json.dumps({
        "source_object_id": str(source_object_id),
        "source_order": source_order,
        "object_class": object_class,
        "provenance": "source_pdf_import",
    }, sort_keys=True, separators=(",", ":"))
    nonvisual_nodes = shape._element.xpath(".//p:cNvPr")
    if not nonvisual_nodes:
        raise ValueError("UNSUPPORTED_SHAPE_PROVENANCE_CONTAINER")
    nonvisual_nodes[0].set("descr", metadata)


def _image_block_bytes(block):
    if not block.get("mask"):
        return block["image"]
    # The PDF image and its soft mask are separate byte streams. Keep the
    # author's original transparency instead of painting a solid icon box.
    base = Image.open(BytesIO(block["image"])).convert("RGBA")
    alpha = Image.open(BytesIO(block["mask"])).convert("L")
    base.putalpha(alpha)
    result = BytesIO()
    base.save(result, format="PNG")
    return result.getvalue()


def _add_image(slide, block, warnings):
    bbox = fitz.Rect(block["bbox"])
    if bbox.is_empty:
        return False
    transform = block.get("transform", ())
    if len(transform) == 6 and (abs(transform[1]) > .01 or abs(transform[2]) > .01):
        warnings.append("a rotated or skewed raster asset was placed using its bounding box")
    slide.shapes.add_picture(
        BytesIO(_image_block_bytes(block)),
        _pt_in(bbox.x0), _pt_in(bbox.y0),
        width=_pt_in(bbox.width), height=_pt_in(bbox.height),
    )
    return True


def _add_recovered_image(slide, event, warnings):
    if len(event.transform) == 6 and (abs(event.transform[1]) > .01 or abs(event.transform[2]) > .01):
        warnings.append(f"image paint event {event.seqno}: source transform requires visual verification")
    b = event.visible_bbox
    shape = slide.shapes.add_picture(
        BytesIO(event.png), _pt_in(b.x0), _pt_in(b.y0),
        width=_pt_in(b.width), height=_pt_in(b.height),
    )
    _annotate_source_shape(shape, f"image_{event.seqno}", event.seqno, "image")
    return 1


def convert_pdf_page(pdf_path: Path, pptx_path: Path, *, page_index: int = 0,
                     max_drawings: int = DEFAULT_MAX_DRAWINGS,
                     max_source_segments: int = DEFAULT_MAX_SOURCE_SEGMENTS,
                     max_vertices: int = DEFAULT_MAX_VERTICES,
                     max_seconds: float = DEFAULT_MAX_SECONDS,
                     figure_region: tuple[float, float, float, float] | None = None) -> dict:
    pdf_path, pptx_path = Path(pdf_path), Path(pptx_path)
    if page_index < 0:
        raise ValueError("INVALID_SOURCE_PAGE_INDEX: zero-based page index must be non-negative")
    if (pdf_path.resolve() == pptx_path.resolve() or
        (pptx_path.exists() and os.path.samefile(pdf_path, pptx_path))):
        raise ValueError("REFUSE_TO_OVERWRITE_SOURCE_PDF")
    source_sha256 = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    clock_start = time.monotonic()
    document = fitz.open(pdf_path)
    try:
        page = document[page_index]
        selected_region = apply_figure_region(page, figure_region)
        width_pt, height_pt = float(page.rect.width), float(page.rect.height)
        if min(width_pt, height_pt) < 72:
            raise ValueError("UNSUPPORTED_SOURCE_CROP_SIZE: PowerPoint slide must be at least 1 inch per axis")
        deck = Presentation()
        deck.slide_width, deck.slide_height = _pt_in(width_pt), _pt_in(height_pt)
        slide = deck.slides.add_slide(deck.slide_layouts[6])
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = RGBColor(255, 255, 255)
        extended = page.get_drawings(extended=True)
        # Preflight the selected figure, not unrelated diagrams or plots on
        # the same paper page. Keep all records for paint-order and clip-stack
        # reconstruction below; only drawable candidates count against budget.
        visible_drawings = [
            d for d in extended
            if d.get("type") not in ("f", "fs", "s") or
               drawable_intersects_region(d, page.rect)
        ]
        resource_profile = preflight_drawing_budget(
            visible_drawings, clock_start=clock_start, max_drawings=max_drawings,
            max_source_segments=max_source_segments, max_vertices=max_vertices,
            max_seconds=max_seconds,
        )
        warnings = []
        page_blocks = page.get_text("dict")["blocks"]
        if selected_region is not None:
            for block in page_blocks:
                for line in block.get("lines", []):
                    for span in line["spans"]:
                        if not _normalize_pdf_text(span.get("text", "")).strip():
                            continue
                        bbox = fitz.Rect(span["bbox"])
                        if (bbox.x0 < page.rect.x0 - .1 or bbox.y0 < page.rect.y0 - .1 or
                            bbox.x1 > page.rect.x1 + .1 or bbox.y1 > page.rect.y1 + .1):
                            raise ValueError("UNSUPPORTED_SOURCE_CROP_EDGE_TEXT: glyph clipping requires manual reconstruction")

        images, source_image_stats = collect_image_events(
            page, document,
            image_blocks=[b for b in page_blocks if b["type"] == 1],
        )
        if selected_region is not None and any(
            len(event.transform) == 6 and
            (abs(event.transform[1]) > .01 or abs(event.transform[2]) > .01)
            for event in images
        ):
            raise ValueError("UNSUPPORTED_SOURCE_IMAGE_TRANSFORM: cropped rotated/skewed image needs manual reconstruction")
        warnings.extend(source_image_stats["warnings"])
        picture_events = iter(images)
        next_image = next(picture_events, None)
        picture_count = native_count = 0
        clip_stack = []
        for drawing_index, drawing in enumerate(extended):
            assert_budget(clock_start, max_seconds)
            current_seqno = drawing.get("seqno")
            if current_seqno is not None:
                while next_image is not None and next_image.seqno < current_seqno:
                    picture_count += _add_recovered_image(slide, next_image, warnings)
                    next_image = next(picture_events, None)
            level = drawing.get("level", 0)
            clip_stack = [(depth, rect) for depth, rect in clip_stack if depth < level]
            if drawing["type"] == "clip":
                scissor = drawing.get("scissor")
                if scissor is not None:
                    clip_stack.append((level, fitz.Rect(scissor)))
                continue
            if drawing["type"] == "group":
                continue
            clip_region = fitz.Rect(page.rect)
            for _, rect in clip_stack:
                clip_region &= rect
            if clip_region.is_empty or not drawable_intersects_region(drawing, clip_region):
                continue
            if selected_region is not None and drawing.get("type") in ("s", "fs"):
                box = fitz.Rect(drawing["rect"])
                centerline_in_crop = (
                    box.x0 <= clip_region.x1 and box.x1 >= clip_region.x0 and
                    box.y0 <= clip_region.y1 and box.y1 >= clip_region.y0
                )
                if not centerline_in_crop:
                    raise ValueError("UNSUPPORTED_SOURCE_CROP_EDGE_STROKE: line width enters crop without centerline")
            added = _add_drawing(slide, drawing, page.rect, warnings, clip_region)
            native_count += added
            if added:
                seqno = drawing.get("seqno")
                source_id = f"draw_{seqno if seqno is not None else drawing_index}"
                _annotate_source_shape(slide.shapes[-1], source_id, seqno, "vector")
        while next_image is not None:
            picture_count += _add_recovered_image(slide, next_image, warnings)
            next_image = next(picture_events, None)

        text_count, font_counts = 0, Counter()
        for block_index, block in enumerate(page_blocks):
            for line_index, line in enumerate(block.get("lines", [])):
                for span_index, span in enumerate(line["spans"]):
                    added_text = _add_text(slide, span, line, page.rect)
                    text_count += int(added_text)
                    if added_text:
                        source_id = f"text_{block_index}_{line_index}_{span_index}"
                        _annotate_source_shape(slide.shapes[-1], source_id, None, "text")
                    font_counts[_source_font(span["font"])] += 1

        assert_budget(clock_start, max_seconds)
        if source_image_stats["unresolved_visible_events"]:
            raise ValueError(
                f"UNRESOLVED_SOURCE_IMAGES: {source_image_stats['unresolved_visible_events']}"
            )
        if not any((native_count, text_count, picture_count)):
            raise ValueError("NO_VISIBLE_SOURCE_CONTENT")

        resource_profile["elapsed_seconds"] = round(time.monotonic() - clock_start, 6)
        pptx_path.parent.mkdir(parents=True, exist_ok=True)
        deck.save(pptx_path)
        clean_theme(pptx_path)
        return {
            "page_size_pt": [width_pt, height_pt],
            "figure_region_pt": selected_region,
            "source_sha256": source_sha256,
            "native_shapes": native_count,
            "text_shapes": text_count,
            "picture_shapes": picture_count,
            "source_fonts": dict(font_counts),
            "warnings": warnings,
            "recovered_image_xrefs": source_image_stats["recovered_xrefs"],
            "source_image_events": source_image_stats["source_paint_events"],
            "off_page_image_events": source_image_stats["off_page_image_events"],
            "image_assets": manifest_events(images),
            "resource_profile": resource_profile,
            "reconstruction_class": (
                "source_picture_only" if picture_count and not (native_count or text_count)
                else "mixed_native_picture" if picture_count else "native_only"
            ),
        }
    finally:
        document.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_pdf", type=Path)
    parser.add_argument("output_pptx", type=Path)
    parser.add_argument("--page", type=int, default=1, help="1-based source PDF page")
    parser.add_argument("--report", type=Path, help="Optional JSON audit summary")
    args = parser.parse_args()
    report = convert_pdf_page(args.source_pdf, args.output_pptx, page_index=args.page - 1)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
