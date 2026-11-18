"""Recover a bounded subset of painted PDF text as editable native polygons.

Only source-bound fill+stroke text made from simple, closed, straight-line
glyph contours is supported. MuPDF's source SVG supplies the embedded glyph
outline and affine matrix; its native paint device supplies the actual stroke
state and CTM. No installed font or Unicode substitute supplies geometry.
Stroke CTMs must be similarity transforms; text matrices can be anisotropic.
Opaque, solid miter/butt strokes and non-intersecting single contours are the
finite supported subset. Unsupported cases fail before returning shapes.
"""
from __future__ import annotations

import hashlib
import math
import re

import fitz
from fontTools.pens.recordingPen import RecordingPen
from fontTools.svgLib.path import parse_path
from lxml import etree

from pdf_image_clips import IDENTITY, HREF, MAX_SVG_BYTES, _clip_geometry, _compose, _matrix

MAX_GLYPHS = 64
MAX_POLYGON_POINTS = 128
MAX_GLYPH_PATH_BYTES = 32768


def _fail(reason):
    raise ValueError("UNSUPPORTED_SOURCE_TEXT_OUTLINE_" + reason)


def _cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def _area(points):
    return sum(_cross(p, points[(i + 1) % len(points)]) for i, p in enumerate(points)) / 2


def _inside(point, polygon):
    x, y = point
    inside = False
    for i, a in enumerate(polygon):
        b = polygon[(i + 1) % len(polygon)]
        if (a[1] > y) != (b[1] > y):
            if x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]:
                inside = not inside
    return inside


def _validate_polygon(points):
    if not 3 <= len(points) <= MAX_POLYGON_POINTS or abs(_area(points)) < 1e-12:
        _fail("POLYGON")
    if not all(math.isfinite(v) for p in points for v in p):
        _fail("POLYGON")
    # Proper intersections and non-adjacent contacts are outside this subset.
    for i, a in enumerate(points):
        b = points[(i + 1) % len(points)]
        if math.dist(a, b) < 1e-12:
            _fail("POLYGON")
        for j in range(i + 1, len(points)):
            if j in {i + 1, len(points) - 1 if i == 0 else -1}:
                continue
            c, d = points[j], points[(j + 1) % len(points)]
            ab = (b[0] - a[0], b[1] - a[1])
            cd = (d[0] - c[0], d[1] - c[1])
            den = _cross(ab, cd)
            if abs(den) < 1e-12:
                continue
            ac = (c[0] - a[0], c[1] - a[1])
            t, u = _cross(ac, cd) / den, _cross(ac, ab) / den
            if -1e-10 <= t <= 1 + 1e-10 and -1e-10 <= u <= 1 + 1e-10:
                _fail("SELF_INTERSECTION")


def _polygon(path):
    if set(path.attrib) - {"id", "d"}:
        _fail("GLYPH_STYLE")
    data = path.get("d", "")
    if len(data) > MAX_GLYPH_PATH_BYTES:
        _fail("BUDGET")
    pen = RecordingPen()
    try:
        parse_path(data, pen)
    except (ValueError, TypeError, IndexError) as error:
        _fail("PATH_PARSE: " + str(error))
    if any(op not in {"moveTo", "lineTo", "closePath"} for op, _ in pen.value):
        _fail("CURVED_GLYPH")
    if (sum(op == "moveTo" for op, _ in pen.value) != 1 or
            sum(op == "closePath" for op, _ in pen.value) != 1):
        _fail("MULTI_OR_OPEN_CONTOUR")
    points = [tuple(args[0]) for op, args in pen.value if op in {"moveTo", "lineTo"}]
    if points and points[-1] == points[0]:
        points.pop()
    _validate_polygon(points)
    return points, data


def _offset(points, distance, miter_limit):
    """Exact polygon offset for SVG miter joins with bevel fallback."""
    orientation = 1 if _area(points) > 0 else -1
    edges, normals = [], []
    for i, p in enumerate(points):
        q = points[(i + 1) % len(points)]
        dx, dy = q[0] - p[0], q[1] - p[1]
        length = math.hypot(dx, dy)
        direction = (dx / length, dy / length)
        edges.append(direction)
        normals.append((direction[1] * orientation, -direction[0] * orientation))
    result = []
    for i, p in enumerate(points):
        first, second = edges[i - 1], edges[i]
        n1, n2 = normals[i - 1], normals[i]
        a = (p[0] + distance * n1[0], p[1] + distance * n1[1])
        b = (p[0] + distance * n2[0], p[1] + distance * n2[1])
        turn = _cross(first, second)
        if abs(turn) < 1e-12:
            _fail("COLLINEAR_CORNER")
        t = _cross((b[0] - a[0], b[1] - a[1]), second) / turn
        intersection = (a[0] + t * first[0], a[1] + t * first[1])
        ratio = math.dist(intersection, p) / abs(distance)
        is_join = turn * orientation * (1 if distance > 0 else -1) > 0
        if is_join and ratio > miter_limit + 1e-9:
            result.extend([a, b])
        else:
            result.append(intersection)
    _validate_polygon(result)
    if _area(result) * _area(points) <= 0:
        _fail("COLLAPSED_STROKE")
    if distance < 0 and not all(_inside(p, points) for p in result):
        _fail("COLLAPSED_STROKE")
    return result


def _transform(point, matrix):
    a, b, c, d, e, f = matrix
    return (a * point[0] + c * point[1] + e, b * point[0] + d * point[1] + f)


def _inverse(matrix):
    a, b, c, d, e, f = matrix
    det = a * d - b * c
    if not math.isfinite(det) or abs(det) < 1e-9:
        _fail("STROKE_MATRIX")
    return (d / det, -b / det, -c / det, a / det,
            (c * f - d * e) / det, (b * e - a * f) / det)


def _stroke_state(page, wanted_seqno, chars):
    """Capture actual PDF stroke state; texttrace.linewidth can be stale.

    MuPDF's SVG normalizes stroke width using a geometric-mean text scale.
    Under anisotropic matrices it is not an exact stroke-geometry source.
    This single bounded device callback avoids interpreting PDF operators.
    """
    try:
        m = fitz.mupdf

        class Capture(m.FzDevice2):
            def __init__(self):
                super().__init__()
                self.seqno, self.matches = 0, []
                for name in ("fill_path", "stroke_path", "fill_text", "stroke_text", "ignore_text",
                             "fill_shade", "fill_image", "fill_image_mask"):
                    getattr(self, "use_virtual_" + name)()

            def increase(self, *args):
                self.seqno += 1

            fill_path = stroke_path = fill_text = ignore_text = fill_shade = fill_image = fill_image_mask = increase

            def stroke_text(self, ctx, text, stroke, ctm, colorspace, color, alpha, params):
                if self.seqno == wanted_seqno:
                    matrix = (ctm.a, ctm.b, ctm.c, ctm.d, ctm.e, ctm.f)
                    observed, span = [], text.head
                    while span:
                        wrapped = m.FzTextSpan(span)
                        for i in range(span.len):
                            item = wrapped.items(i)
                            observed.append((item.ucs, item.gid, _transform((item.x, item.y), matrix)))
                        span = span.next
                    self.matches.append({
                        "matrix": matrix, "chars": observed, "width": stroke.linewidth,
                        "miterlimit": stroke.miterlimit, "linejoin": stroke.linejoin,
                        "start_cap": stroke.start_cap, "end_cap": stroke.end_cap,
                        "dash_len": stroke.dash_len,
                    })
                self.seqno += 1

        device = Capture()
        try:
            m.fz_run_page(page.this, device, m.FzMatrix(), m.FzCookie())
        finally:
            m.fz_close_device(device)
        if len(device.matches) != 1:
            _fail("STROKE_IDENTITY")
        state = device.matches[0]
    except (AttributeError, TypeError, RuntimeError) as error:
        _fail("DEVICE_API: " + str(error))
    if (len(state["chars"]) != len(chars) or any(
            a[:2] != b[:2] or math.dist(a[2], b[2]) > .002
            for a, b in zip(state["chars"], chars))):
        _fail("STROKE_IDENTITY")
    a, b, c, d, _, _ = state["matrix"]
    xscale2, yscale2 = a * a + b * b, c * c + d * d
    tolerance = max(xscale2, yscale2) * 1e-6
    if (not all(math.isfinite(v) for v in state["matrix"]) or
            min(xscale2, yscale2) <= 1e-12 or
            abs(xscale2 - yscale2) > tolerance or abs(a * c + b * d) > tolerance):
        # Text and path rasterization do not agree for non-similarity stroke
        # CTMs in the supported MuPDF renderer. An anisotropic *text matrix*
        # remains supported; the real UCFNet operators use that combination.
        _fail("NON_SIMILARITY_STROKE_CTM")
    if (state["linejoin"] != 0 or state["start_cap"] != 0 or state["end_cap"] != 0 or
            state["dash_len"] != 0 or not math.isfinite(state["width"]) or state["width"] <= 0 or
            not math.isfinite(state["miterlimit"]) or state["miterlimit"] < 1):
        _fail("STROKE_STYLE")
    return state


def _context(node):
    matrix = IDENTITY
    clips, style = [], {}
    for ancestor in [*reversed(list(node.iterancestors())), node]:
        matrix = _compose(matrix, _matrix(ancestor.get("transform")))
        if any(ancestor.get(k) for k in ("filter", "mask", "style")):
            style["unsupported"] = True
        if float(ancestor.get("opacity", "1")) != 1:
            style["unsupported"] = True
        if ancestor.get("clip-path"):
            clips.append((ancestor.get("clip-path"), matrix))
        for key in ("fill", "stroke", "fill-opacity", "stroke-opacity", "stroke-width",
                    "stroke-linecap", "stroke-linejoin", "stroke-miterlimit", "stroke-dasharray"):
            if ancestor.get(key) is not None:
                style[key] = ancestor.get(key)
    if node.get("x") or node.get("y"):
        matrix = _compose(matrix, (1, 0, 0, 1, float(node.get("x", "0")), float(node.get("y", "0"))))
    return matrix, clips, style


def _rgb(value):
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        _fail("COLOR")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (1, 3, 5))


def _trace_color(trace):
    color = trace["color"]
    if trace["colorspace"] == 1:
        return (float(color),) * 3 if isinstance(color, (int, float)) else tuple(color) * 3
    if trace["colorspace"] != 3 or len(color) != 3:
        _fail("COLORSPACE")
    return tuple(color)


def _same_chars(a, b):
    return len(a) == len(b) and all(
        x[:2] == y[:2] and math.dist(x[2], y[2]) < 1e-4 and
        max(abs(u - v) for u, v in zip(x[3], y[3])) < 1e-4
        for x, y in zip(a, b))


def recover_text_outlines(page, event):
    """Return native fill records, or reject an unsupported entire text event.

    ``event`` carries seqno, source_seqnos, chars, span, line, paint_type, and
    evidence. Actual source traces independently validate the supplied identity.
    Different fill/stroke colors stay in their original two paint layers.
    """
    if page.rotation:
        _fail("ROTATED_PAGE")
    if event.paint_type != "fill_stroke" or not 0 < len(event.chars) <= MAX_GLYPHS:
        _fail("EVENT")
    seqnos = tuple(event.source_seqnos)
    if len(seqnos) != 2 or event.seqno != seqnos[0] or seqnos[1] != seqnos[0] + 1:
        _fail("EVENT_ORDER")
    trace_list = page.get_texttrace()
    if any(sum(t["seqno"] == s for t in trace_list) != 1 for s in seqnos):
        _fail("AMBIGUOUS_TRACE")
    traces = {t["seqno"]: t for t in trace_list}
    if any(s not in traces for s in seqnos):
        _fail("EVENT_IDENTITY")
    fill_trace, stroke_trace = (traces[s] for s in seqnos)
    if (fill_trace["type"] != 0 or stroke_trace["type"] != 1 or
            not _same_chars(fill_trace["chars"], stroke_trace["chars"]) or
            not _same_chars(event.chars, fill_trace["chars"]) or
            event.span["font"] != fill_trace["font"] or
            math.dist(event.line["dir"], fill_trace["dir"]) > 1e-5):
        _fail("EVENT_IDENTITY")
    if fill_trace["opacity"] != 1 or stroke_trace["opacity"] != 1:
        # PDF transparency knockout for a fill/stroke text object differs from
        # ordinary source-over blending of two native filled shapes.
        _fail("TRANSPARENT_COMPOSITING")
    state = _stroke_state(page, seqnos[1], event.chars)
    stroke_matrix = state["matrix"]
    stroke_inverse = _inverse(stroke_matrix)
    svg_bytes = page.get_svg_image(text_as_path=True).encode()
    if len(svg_bytes) > MAX_SVG_BYTES:
        _fail("BUDGET")
    root = etree.fromstring(svg_bytes, etree.XMLParser(resolve_entities=False, no_network=True))
    definitions = {n.get("id"): n for n in root.iter() if n.get("id")}
    uses = [n for n in root.iter() if etree.QName(n).localname == "use"]
    fills, strokes = [], []
    fill_color, stroke_color = _trace_color(fill_trace), _trace_color(stroke_trace)
    fill_alpha, stroke_alpha = fill_trace["opacity"], stroke_trace["opacity"]
    for char_index, (codepoint, glyph_id, origin, _) in enumerate(event.chars):
        matches = []
        for use in uses:
            href = use.get(HREF, "")
            if (use.get("data-text") != chr(codepoint) or
                    not href.endswith("_" + str(glyph_id))):
                continue
            matrix, clips, style = _context(use)
            if math.dist(matrix[4:], origin) < .002:
                matches.append((use, matrix, clips, style))
        if len(matches) != 2:
            _fail("AMBIGUOUS_OCCURRENCE")
        fill_use, stroke_use = matches
        fnode, matrix, fclips, fstyle = fill_use
        snode, smatrix, sclips, sstyle = stroke_use
        if (fstyle.get("stroke", "none") != "none" or sstyle.get("fill") != "none" or
                fnode.get(HREF) != snode.get(HREF) or matrix != smatrix or fclips != sclips):
            _fail("PAINT_PAIR")
        if fstyle.get("unsupported") or sstyle.get("unsupported"):
            _fail("COMPOSITING")
        a, b, c, d, _, _ = matrix
        norm = math.hypot(a, b)
        if (abs(a * d - b * c) < 1e-9 or abs(norm - fill_trace["size"]) > .002 or
                math.dist((a / norm, b / norm), fill_trace["dir"]) > 1e-4):
            _fail("MATRIX")
        if (max(abs(x - y) for x, y in zip(_rgb(fstyle.get("fill", "#000000")), fill_color)) > .004 or
                max(abs(x - y) for x, y in zip(_rgb(sstyle.get("stroke", "")), stroke_color)) > .004 or
                abs(float(fstyle.get("fill-opacity", "1")) - fill_alpha) > .001 or
                abs(float(sstyle.get("stroke-opacity", "1")) - stroke_alpha) > .001):
            _fail("PAINT_MISMATCH")
        if (sstyle.get("stroke-linejoin", "miter") != "miter" or
                sstyle.get("stroke-linecap", "butt") != "butt" or
                sstyle.get("stroke-dasharray", "none") != "none"):
            _fail("STROKE_STYLE")
        svg_width = float(sstyle.get("stroke-width", "0"))
        width, limit = state["width"], state["miterlimit"]
        if (not math.isfinite(svg_width) or svg_width <= 0 or
                abs(float(sstyle.get("stroke-miterlimit", "4")) - limit) > 1e-5):
            _fail("STROKE_STYLE")
        path = definitions.get(fnode.get(HREF, "")[1:])
        if path is None or etree.QName(path).localname != "path":
            _fail("GLYPH_REFERENCE")
        points, path_data = _polygon(path)
        page_points = [_transform(p, matrix) for p in points]
        stroke_points = [_transform(p, stroke_inverse) for p in page_points]
        outer = _offset(stroke_points, width / 2, limit)
        transformed_outer = [_transform(p, stroke_matrix) for p in outer]
        box = fitz.Rect(min(p[0] for p in transformed_outer), min(p[1] for p in transformed_outer),
                        max(p[0] for p in transformed_outer), max(p[1] for p in transformed_outer))
        for value, cmatrix in fclips:
            try:
                clip = _clip_geometry(value, cmatrix, definitions)
            except ValueError as error:
                _fail("CLIP: " + str(error))
            if not clip["rectangle"] or not (clip["bbox"] + (-.001, -.001, .001, .001)).contains(box):
                _fail("CLIP")
        if not (page.rect + (-.001, -.001, .001, .001)).contains(box):
            _fail("PAGE_EDGE")
        provenance = {
            "provenance": "source_pdf_embedded_glyph_outline",
            "source_font": fill_trace["font"], "source_glyph_id": glyph_id,
            "source_codepoint": codepoint, "source_char_index": char_index,
            "source_origin": tuple(origin), "source_seqnos": seqnos,
            "source_svg_glyph_id": path.get("id"),
            "source_path_sha256": hashlib.sha256(path_data.encode()).hexdigest(),
            "source_matrix": matrix, "stroke_width_user_units": width,
            "stroke_ctm": stroke_matrix, "svg_normalized_stroke_width": svg_width,
            "stroke_linejoin": "miter", "stroke_miterlimit": limit,
            "geometry_method": "source glyph outline expanded in actual stroke user coordinates, then source stroke CTM",
            "stroke_state_source": "MuPDF FzDevice2.stroke_text callback validated against event identity",
            "text_editability": "native editable freeform outline",
        }
        def record(paths, color, alpha, role):
            record_seqnos = ((seqnos[0],) if role == "fill" else
                             (seqnos[1],) if role == "stroke_ring" else seqnos)
            return {"paths": paths, "fill": color, "opacity": alpha,
                    "source_seqnos": record_seqnos,
                    "provenance": {**provenance, "paint_role": role}}
        if fill_color == stroke_color and fill_alpha == stroke_alpha == 1:
            fills.append(record([transformed_outer], fill_color, 1., "opaque_fill_stroke_union"))
        else:
            inner = _offset(stroke_points, -width / 2, limit)
            fills.append(record([page_points], fill_color, fill_alpha, "fill"))
            strokes.append(record([transformed_outer, [_transform(p, stroke_matrix) for p in reversed(inner)]],
                                  stroke_color, stroke_alpha, "stroke_ring"))
    return fills + strokes
