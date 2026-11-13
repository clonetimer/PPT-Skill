"""Recover paint-ordered, crop-aware PDF image occurrences as independent assets.

Do not rely exclusively on page.get_text('dict') image blocks: cropped figure
pages can have visible XRef image paint events while returning no such blocks.
No page rasterization is used for a recoverable XRef.
"""
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import hashlib

import fitz
from PIL import Image


@dataclass(frozen=True)
class ImageEvent:
    seqno: int
    xref: int
    bbox: fitz.Rect
    visible_bbox: fitz.Rect
    png: bytes
    source_kind: str
    transform: tuple[float, ...]


def _rms_distance(left: fitz.Rect, right: fitz.Rect) -> float:
    return sum(abs(a-b) for a, b in zip(left, right))


def _best_match(pool, rect: fitz.Rect, used: set[int], max_error: float = 5.0):
    choices = [(_rms_distance(fitz.Rect(item["bbox"]), rect), i)
               for i, item in enumerate(pool) if i not in used]
    if not choices:
        return None
    err, index = min(choices)
    if err > max_error:
        return None
    used.add(index)
    return pool[index]


def _png_for_xref(doc: fitz.Document, xref: int, smasks: dict[int, int]) -> bytes:
    pix = fitz.Pixmap(doc, xref)
    if pix.colorspace and pix.colorspace.n != 3:
        pix = fitz.Pixmap(fitz.csRGB, pix)
    smask = smasks.get(xref, 0)
    if smask:
        mask = fitz.Pixmap(doc, smask)
        pix = fitz.Pixmap(pix, mask)
    return pix.tobytes("png")


def _block_to_png(block: dict) -> bytes:
    image = Image.open(BytesIO(block["image"])).convert("RGBA")
    if block.get("mask"):
        mask = Image.open(BytesIO(block["mask"])).convert("L")
        image.putalpha(mask)
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _crop_asset(png: bytes, bbox: fitz.Rect, visible: fitz.Rect) -> bytes:
    if bbox == visible:
        return png
    im = Image.open(BytesIO(png))
    if bbox.width <= 0 or bbox.height <= 0:
        raise ValueError("INVALID_IMAGE_BBOX")
    fx0 = max(0, min(1, (visible.x0-bbox.x0)/bbox.width))
    fy0 = max(0, min(1, (visible.y0-bbox.y0)/bbox.height))
    fx1 = max(0, min(1, (visible.x1-bbox.x0)/bbox.width))
    fy1 = max(0, min(1, (visible.y1-bbox.y0)/bbox.height))
    box = (max(0, round(fx0*im.width)), max(0, round(fy0*im.height)),
           min(im.width, round(fx1*im.width)), min(im.height, round(fy1*im.height)))
    if box[2] <= box[0] or box[3] <= box[1]:
        raise ValueError("EMPTY_IMAGE_AFTER_CROP")
    output = BytesIO()
    im.crop(box).save(output, format="PNG")
    return output.getvalue()


def collect_image_events(page: fitz.Page, document: fitz.Document,
                         *, image_blocks: list[dict] | None = None
                         ) -> tuple[list[ImageEvent], dict]:
    """Match bboxlog paint events to image blocks or xrefs; exclude off-page assets.

    The ordered result uses source graphics sequence numbers, not image-block
    enumeration. Missing get_text blocks are backed by get_image_info xrefs.
    """
    if image_blocks is None:
        image_blocks = [b for b in page.get_text("dict")["blocks"] if b["type"] == 1]
    infos = page.get_image_info(xrefs=True)
    smasks = {int(entry[0]): int(entry[1]) for entry in page.get_images(full=True)}
    used_blocks: set[int] = set()
    used_infos: set[int] = set()
    events: list[ImageEvent] = []
    stats = dict(source_paint_events=0, recovered_xrefs=0,
                 from_dict_blocks=0, off_page_image_events=0,
                 unresolved_visible_events=0, warnings=[])
    for seqno, (kind, coords) in enumerate(page.get_bboxlog()):
        if kind != "fill-image":
            continue
        stats["source_paint_events"] += 1
        bbox = fitz.Rect(coords)
        visible = bbox & page.rect
        if visible.is_empty or visible.width <= 0 or visible.height <= 0:
            stats["off_page_image_events"] += 1
            continue
        info = _best_match(infos, bbox, used_infos)
        block = _best_match(image_blocks, bbox, used_blocks)
        xref = int(info.get("xref") or 0) if info else 0
        transform = tuple(info.get("transform", ())) if info else ()
        if not block and not xref:
            stats["unresolved_visible_events"] += 1
            stats["warnings"].append(f"visible image at paint event {seqno} has no extractable XRef or image block")
            continue
        try:
            if block is not None:
                png = _block_to_png(block)
                origin = "dict-block"
                stats["from_dict_blocks"] += 1
            else:
                png = _png_for_xref(document, xref, smasks)
                origin = "xref-fallback"
                stats["recovered_xrefs"] += 1
            # XRef coordinates can be translated/rotated. Cropping a rotated
            # image as if it were axis-aligned is unsafe; report this explicitly.
            rotated = len(transform) == 6 and (abs(transform[1]) > .01 or abs(transform[2]) > .01)
            if rotated:
                stats["warnings"].append(f"paint event {seqno}: rotated/skewed image requires transform review")
            else:
                png = _crop_asset(png, bbox, visible)
            events.append(ImageEvent(seqno, xref, bbox, visible, png, origin, transform))
        except (ValueError, RuntimeError, OSError) as exc:
            stats["unresolved_visible_events"] += 1
            stats["warnings"].append(f"paint event {seqno}: {type(exc).__name__}: {exc}")
    return events, stats


def manifest_events(events: list[ImageEvent]) -> list[dict]:
    return [dict(seqno=e.seqno, xref=e.xref, source_kind=e.source_kind,
                 original_bbox=list(e.bbox), placed_bbox=list(e.visible_bbox),
                 image_png_sha256=hashlib.sha256(e.png).hexdigest(),
                 transform=list(e.transform)) for e in events]
