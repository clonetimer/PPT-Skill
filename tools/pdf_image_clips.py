"""Preserve PDF path clips on individual source pictures, never diagram art.

The SVG is generated locally by MuPDF from the opened PDF. It is used only for
paint occurrence geometry; original decoded image pixels remain the source.
Unsupported composition fails closed instead of exposing unclipped pixels.
"""
from __future__ import annotations

import base64
from dataclasses import replace
from io import BytesIO
import hashlib
import math
import re
import time

import fitz
from lxml import etree
from PIL import Image, ImageChops
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.reportLabPen import ReportLabPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import parse_path
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

SVG = "http://www.w3.org/2000/svg"
HREF = "{http://www.w3.org/1999/xlink}href"
IDENTITY = (1., 0., 0., 1., 0., 0.)
CLIP_DPI = 576
MAX_IMAGE_PIXELS = 16_000_000
MAX_PAGE_PIXELS = 64_000_000
MAX_CLIP_COMMANDS = 100_000
MAX_PATH_DATA_BYTES = 4_000_000
MAX_SVG_BYTES = 32_000_000
MAX_CLIP_SECONDS = 30


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _matrix(value):
    if not value:
        return IDENTITY
    m = re.fullmatch(r"matrix\(\s*([^()]+)\s*\)", value)
    if not m:
        raise ValueError("UNSUPPORTED_IMAGE_CLIP_TRANSFORM")
    values = tuple(float(v) for v in re.split(r"[\s,]+", m[1].strip()))
    if len(values) != 6 or not all(math.isfinite(v) for v in values):
        raise ValueError("INVALID_IMAGE_CLIP_TRANSFORM")
    return values


def _compose(a, b):
    aa, ab, ac, ad, ae, af = a
    ba, bb, bc, bd, be, bf = b
    return (aa*ba+ac*bb, ab*ba+ad*bb, aa*bc+ac*bd, ab*bc+ad*bd,
            aa*be+ac*bf+ae, ab*be+ad*bf+af)


def _tag(node):
    return etree.QName(node).localname


def _reference(value, definitions):
    m = re.fullmatch(r"url\(#([^()]+)\)", value or "")
    if not m or m[1] not in definitions:
        raise ValueError("UNRESOLVED_IMAGE_CLIP_REFERENCE")
    return definitions[m[1]]


def _image_bytes(node):
    href = node.get(HREF) or node.get("href", "")
    m = re.fullmatch(r"data:image/(?:png|jpeg);base64,(.*)", href, re.S)
    if not m:
        raise ValueError("UNSUPPORTED_IMAGE_CLIP_ASSET_REFERENCE")
    return base64.b64decode(re.sub(r"\s+", "", m[1]), validate=True)


def _occurrences(root, definitions, initial=IDENTITY):
    result = []

    def visit(node, matrix, clips, masks, problems, references=()):
        tag = _tag(node)
        if tag in {"defs", "mask", "clipPath"}:
            return
        if tag not in {"svg", "g", "image", "use"}:
            return  # Native paths/text are never painted by this module.
        matrix = _compose(matrix, _matrix(node.get("transform")))
        bad = list(problems)
        if (node.get("filter") or node.get("style") or
                node.get("opacity", "1") not in {"1", "1.0"}):
            bad.append("UNSUPPORTED_IMAGE_CLIP_COMPOSITING")
        if node.get("clip-path"):
            clips = clips + [(node.get("clip-path"), matrix)]
        if node.get("mask"):
            masks = masks + [(node.get("mask"), matrix)]
        if tag == "use":
            href = node.get(HREF) or node.get("href", "")
            if not href.startswith("#") or href[1:] not in definitions:
                raise ValueError("UNSUPPORTED_IMAGE_CLIP_USE_REFERENCE")
            if href in references or len(references) >= 16:
                raise ValueError("CYCLIC_IMAGE_CLIP_REFERENCE")
            x, y = float(node.get("x", "0")), float(node.get("y", "0"))
            if not all(math.isfinite(v) for v in (x, y)):
                raise ValueError("INVALID_IMAGE_CLIP_USE_POSITION")
            visit(definitions[href[1:]], _compose(matrix, (1,0,0,1,x,y)),
                  clips, masks, bad, references+(href,))
        elif tag == "image":
            a, b, c, d, e, f = matrix
            if abs(b) > 1e-6 or abs(c) > 1e-6 or a <= 0 or d <= 0:
                bad.append("UNSUPPORTED_SOURCE_IMAGE_TRANSFORM")
            w, h = float(node.get("width", "0")), float(node.get("height", "0"))
            if not all(math.isfinite(v) and v > 0 for v in (w, h)):
                raise ValueError("INVALID_IMAGE_CLIP_ASSET_SIZE")
            x, y = float(node.get("x", "0")), float(node.get("y", "0"))
            corners = [(a*px+c*py+e, b*px+d*py+f)
                       for px, py in ((x,y),(x+w,y),(x,y+h),(x+w,y+h))]
            box = fitz.Rect(min(p[0] for p in corners), min(p[1] for p in corners),
                            max(p[0] for p in corners), max(p[1] for p in corners))
            result.append(dict(node=node, bbox=box, clips=clips, masks=masks,
                               problems=bad, size=(int(w),int(h))))
        else:
            for child in node:
                visit(child, matrix, clips, masks, bad, references)

    visit(root, initial, [], [], [])
    return result


def _same_box(a, b):
    return max(abs(x-y) for x,y in zip(a,b)) < .03


def _verify_pixels(occurrence, raw_png):
    source = Image.open(BytesIO(raw_png)).convert("RGBA")
    embedded = Image.open(BytesIO(_image_bytes(occurrence["node"]))).convert("RGB")
    if source.size != embedded.size or source.size != occurrence["size"]:
        raise ValueError("IMAGE_CLIP_OCCURRENCE_SIZE_MISMATCH")
    # Compare premultiplied color so the source decoder's unpremultiplication
    # rounding at very small alpha cannot cause a false correspondence failure.
    alpha = source.getchannel("A")
    alpha_rgb = Image.merge("RGB", (alpha,alpha,alpha))
    difference = ImageChops.difference(ImageChops.multiply(source.convert("RGB"), alpha_rgb),
                                      ImageChops.multiply(embedded, alpha_rgb))
    if any(high > 2 for _, high in difference.getextrema()):
        raise ValueError("IMAGE_CLIP_OCCURRENCE_PIXELS_MISMATCH")
    return source


def _verify_mask(occurrence, source, definitions):
    if not occurrence["masks"]:
        return False
    if len(occurrence["masks"]) != 1:
        raise ValueError("UNSUPPORTED_IMAGE_CLIP_GROUP_MASK")
    value, matrix = occurrence["masks"][0]
    mask = _reference(value, definitions)
    if _tag(mask) != "mask" or set(mask.attrib) - {"id"}:
        raise ValueError("UNSUPPORTED_IMAGE_CLIP_GROUP_MASK")
    # MuPDF emits a single grayscale image for an image's decoded SMask.
    # Verify the complete mask content and its placement; an arbitrary group
    # mask must not be mistaken for source-image alpha.
    if any(_tag(n) not in {"mask","g","image","use"} for n in mask.iter()):
        raise ValueError("UNSUPPORTED_IMAGE_CLIP_GROUP_MASK")
    wrapper = etree.Element("{"+SVG+"}g")
    import copy
    for child in mask:
        wrapper.append(copy.deepcopy(child))
    matches = _occurrences(wrapper, definitions, matrix)
    if (len(matches) != 1 or matches[0]["clips"] or matches[0]["masks"] or
            matches[0]["problems"] or not _same_box(matches[0]["bbox"], occurrence["bbox"])):
        raise ValueError("UNSUPPORTED_IMAGE_CLIP_GROUP_MASK")
    mask_image = Image.open(BytesIO(_image_bytes(matches[0]["node"]))).convert("L")
    alpha = source.getchannel("A")
    if mask_image.size != alpha.size or ImageChops.difference(mask_image, alpha).getbbox():
        raise ValueError("IMAGE_CLIP_SOURCE_ALPHA_MISMATCH")
    return True


class _BoundedRecordingPen(RecordingPen):
    """Stop expansions while parsing, rather than after building a huge path."""
    def _record(self, operation, arguments):
        if len(self.value) >= MAX_CLIP_COMMANDS:
            raise ValueError("IMAGE_CLIP_PATH_BUDGET")
        self.value.append((operation, arguments))

    def moveTo(self, pt): self._record("moveTo", (pt,))
    def lineTo(self, pt): self._record("lineTo", (pt,))
    def curveTo(self, *points): self._record("curveTo", points)
    def qCurveTo(self, *points): self._record("qCurveTo", points)
    def closePath(self): self._record("closePath", ())
    def endPath(self): self._record("endPath", ())


def _preflight_path(data):
    # fontTools materializes its token stream before invoking the pen. Bound
    # both source bytes and streamed tokens first, including implicit commands.
    if len(data) > MAX_PATH_DATA_BYTES:
        raise ValueError("IMAGE_CLIP_PATH_BUDGET")
    token_pattern = r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?|[A-Za-z]"
    for index, _ in enumerate(re.finditer(token_pattern, data), 1):
        if index > MAX_CLIP_COMMANDS*8:
            raise ValueError("IMAGE_CLIP_PATH_BUDGET")


def _clip_geometry(value, matrix, definitions):
    clip = _reference(value, definitions)
    if (_tag(clip) != "clipPath" or len(clip) != 1 or _tag(clip[0]) != "path" or
            clip.get("clipPathUnits", "userSpaceOnUse") != "userSpaceOnUse" or
            set(clip.attrib) - {"id","clipPathUnits","transform"}):
        raise ValueError("UNSUPPORTED_IMAGE_CLIP_GEOMETRY")
    path = clip[0]
    if set(path.attrib) - {"d","transform","clip-rule","fill-rule"}:
        raise ValueError("UNSUPPORTED_IMAGE_CLIP_PATH_STYLE")
    rule = path.get("clip-rule", "nonzero")
    if rule not in {"nonzero","evenodd"}:
        raise ValueError("UNSUPPORTED_IMAGE_CLIP_RULE")
    transform = _compose(_compose(matrix, _matrix(clip.get("transform"))),
                         _matrix(path.get("transform")))
    data = path.get("d", "")
    _preflight_path(data)
    record = _BoundedRecordingPen()
    parse_path(data, TransformPen(record, transform))
    bounds = BoundsPen(None); record.replay(bounds)
    if bounds.bounds is None:
        return dict(id=clip.get("id"), record=record, bbox=fitz.Rect(), rule=rule, rectangle=False)
    box = fitz.Rect(bounds.bounds)
    points = [args[0] for op,args in record.value if op in {"moveTo","lineTo"}]
    rectangle = (len(record.value) in {5,6} and
                 all(op in {"moveTo","lineTo","closePath","endPath"} for op,_ in record.value) and
                 {tuple(p) for p in points} == {(box.x0,box.y0),(box.x1,box.y0),(box.x1,box.y1),(box.x0,box.y1)} and
                 all(abs(a[0]-b[0]) < 1e-6 or abs(a[1]-b[1]) < 1e-6
                     for a,b in zip(points, points[1:]+points[:1])))
    return dict(id=clip.get("id"), record=record, bbox=box, rule=rule, rectangle=rectangle)


class _ClipPen(ReportLabPen):
    def _closePath(self):
        self.path.close()


def _render(raw_png, image_box, box, clips, dpi):
    pdf_bytes = BytesIO()
    # MuPDF 1.26 treats a PDF MediaBox with either extent below one point as
    # 1x1pt. Enlarge the coordinate system, then compensate in the render matrix.
    # Changing only the page dimensions would stretch/crop the original image.
    coordinate_scale = max(1., 2./box.width, 2./box.height)
    pdf = canvas.Canvas(pdf_bytes, pagesize=(box.width*coordinate_scale, box.height*coordinate_scale), invariant=1)
    pdf.scale(coordinate_scale, coordinate_scale)
    pdf.translate(-box.x0, box.y1); pdf.scale(1, -1)
    for clip in clips:
        path = pdf.beginPath()
        clip["record"].replay(_ClipPen(None, path))
        pdf.clipPath(path, stroke=0, fill=0, fillMode=0 if clip["rule"] == "evenodd" else 1)
    pdf.translate(image_box.x0, image_box.y1); pdf.scale(1, -1)
    pdf.drawImage(ImageReader(BytesIO(raw_png)), 0, 0, image_box.width, image_box.height, mask="auto")
    pdf.showPage(); pdf.save()
    with fitz.open(stream=pdf_bytes.getvalue(), filetype="pdf") as document:
        scale = dpi/72/coordinate_scale
        pix = document[0].get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=True)
        expected = (math.ceil(box.width*dpi/72), math.ceil(box.height*dpi/72))
        if any(abs(actual-wanted) > 1 for actual,wanted in zip((pix.width,pix.height),expected)):
            raise ValueError("IMAGE_CLIP_RENDER_SIZE_MISMATCH")
        return pix.tobytes("png"), (pix.width,pix.height)


def preserve_image_clips(page, events, source_pngs):
    """Return updated events and diagnostics, retaining failures in the count."""
    diagnostics = dict(clipped_image_events=0, fully_clipped_image_events=0,
                       unresolved_visible_events=0, clip_render_pixels=0, warnings=[])
    if not events:
        return events, diagnostics
    started = time.monotonic()
    try:
        svg_bytes = page.get_svg_image(text_as_path=False).encode("utf-8")
        if len(svg_bytes) > MAX_SVG_BYTES:
            raise ValueError("IMAGE_CLIP_SVG_BUDGET")
        root = etree.fromstring(svg_bytes, etree.XMLParser(resolve_entities=False, no_network=True))
        definitions = {n.get("id"):n for n in root.iter() if n.get("id")}
        occurrences = [o for o in _occurrences(root, definitions) if o["bbox"].intersects(page.rect)]
        if len(occurrences) != len(events):
            raise ValueError("IMAGE_CLIP_OCCURRENCE_COUNT_MISMATCH")
    except (ValueError, RuntimeError, AttributeError, etree.XMLSyntaxError) as exc:
        diagnostics["unresolved_visible_events"] = len(events)
        diagnostics["warnings"].append(str(exc))
        return [], diagnostics
    result = []
    for event, occurrence in zip(events, occurrences):
        try:
            if time.monotonic()-started > MAX_CLIP_SECONDS:
                raise ValueError("IMAGE_CLIP_TIME_BUDGET")
            if occurrence["problems"]:
                raise ValueError(occurrence["problems"][0])
            if not _same_box(event.bbox, occurrence["bbox"]):
                raise ValueError("IMAGE_CLIP_OCCURRENCE_GEOMETRY_MISMATCH")
            raw_png = source_pngs[event.seqno]
            source = _verify_pixels(occurrence, raw_png)
            mask_verified = _verify_mask(occurrence, source, definitions)
            clips = [_clip_geometry(value, matrix, definitions) for value,matrix in occurrence["clips"]]
            box = fitz.Rect(event.visible_bbox)
            for clip in clips:
                box &= clip["bbox"]
            if box.is_empty:
                diagnostics["fully_clipped_image_events"] += 1
                continue
            # A rectangular source clip covering the visible image is a proven
            # identity. No resampling is needed for ordinary unmodified images.
            active = [c for c in clips if not (c["rectangle"] and c["bbox"].contains(event.visible_bbox))]
            if not active:
                result.append(event)
                continue
            # Small high-resolution source icons must not be downsampled by the
            # repair. The same pixel budget applies to the resulting density.
            image_box = occurrence["bbox"]
            dpi = max(CLIP_DPI, source.width*72/image_box.width, source.height*72/image_box.height)
            expected_size = (math.ceil(box.width*dpi/72), math.ceil(box.height*dpi/72))
            # Reserve a one-pixel rounding margin on each dimension before the
            # renderer allocates. Provenance records the actual result below.
            reserved_pixels = (expected_size[0]+1)*(expected_size[1]+1)
            if reserved_pixels > MAX_IMAGE_PIXELS or diagnostics["clip_render_pixels"]+reserved_pixels > MAX_PAGE_PIXELS:
                raise ValueError("IMAGE_CLIP_PIXEL_BUDGET")
            png, actual_size = _render(raw_png, image_box, box, clips, dpi)
            pixels = actual_size[0]*actual_size[1]
            diagnostics["clip_render_pixels"] += pixels
            if not Image.open(BytesIO(png)).getchannel("A").getbbox():
                diagnostics["fully_clipped_image_events"] += 1
                continue
            provenance = dict(method="source_image_only_original_path_clips", source_svg_sha256=_sha(svg_bytes),
                              source_unclipped_png_sha256=_sha(raw_png), clipped_png_sha256=_sha(png),
                              clip_ids=[c["id"] for c in clips],
                              clip_geometry_sha256=_sha(repr([(c["record"].value,c["rule"]) for c in clips]).encode()),
                              source_bbox_pt=list(event.bbox), clipped_bbox_pt=list(box),
                              source_pixel_size=list(source.size), output_dpi=dpi,
                              output_pixels=pixels, actual_pixel_size=list(actual_size),
                              expected_pixel_size=list(expected_size), source_alpha_verified=mask_verified,
                              diagram_vectors_and_text_rasterized=False)
            result.append(replace(event, png=png, visible_bbox=box, clip_provenance=provenance))
            diagnostics["clipped_image_events"] += 1
        except (ValueError, RuntimeError, OSError, KeyError, TypeError) as exc:
            diagnostics["unresolved_visible_events"] += 1
            diagnostics["warnings"].append(f"paint event {event.seqno}: {exc}")
    return result, diagnostics
