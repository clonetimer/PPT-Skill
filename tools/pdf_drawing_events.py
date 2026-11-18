"""Reconcile vector records with the authoritative PDF paint ledger.

Some MuPDF line-art extractors omit empty paths without advancing their seqno,
while bboxlog, image events and texttrace count those paints. Legacy drawing
seqnos remain object IDs only. Ordered path occurrences and verified geometry
establish actual paint order without assuming a version-specific offset.
"""
from __future__ import annotations

import math

import fitz

GEOMETRY_TOLERANCE_PT = .01
_PATH_KINDS = {"fill-path", "stroke-path"}


class DrawingPaintOrderError(ValueError):
    def __init__(self, reason, stats):
        super().__init__("UNSUPPORTED_SOURCE_DRAWING_" + reason)
        self.stats = dict(stats)


def _fail(reason, stats):
    stats["unsupported_count"] += 1
    raise DrawingPaintOrderError(reason, stats)


def _path_bounds(drawing, stats):
    # drawing['rect'] can omit an endpoint of a later subpath. The actual
    # l/c/re/qu records retain every point needed for the source path bounds.
    points = []
    try:
        for item in drawing["items"]:
            kind = item[0]
            if kind == "re":
                rectangle = fitz.Rect(item[1])
                points.extend((rectangle.tl, rectangle.tr, rectangle.bl, rectangle.br))
            elif kind == "qu":
                points.extend(fitz.Quad(item[1]))
            elif kind in ("l", "c"):
                points.extend(item[1:])
            else:
                _fail("PATH_OPCODE", stats)
        if not points or not all(math.isfinite(float(v)) for p in points for v in p):
            _fail("PATH_GEOMETRY", stats)
        return (min(p[0] for p in points), min(p[1] for p in points),
                max(p[0] for p in points), max(p[1] for p in points))
    except (KeyError, TypeError, OverflowError) as exc:
        _fail("PATH_GEOMETRY: " + str(exc), stats)


def _geometry_matches(path_bounds, paint_bounds, kind):
    if kind == "fill-path":
        return max(abs(a - b) for a, b in zip(path_bounds, paint_bounds)) <= GEOMETRY_TOLERANCE_PT
    pads = (path_bounds[0] - paint_bounds[0], path_bounds[1] - paint_bounds[1],
            paint_bounds[2] - path_bounds[2], paint_bounds[3] - path_bounds[3])
    # A stroke's bounds expand the path bounds. The native bounding device's
    # expansion is symmetric per axis; cap/miter/CTM can change its magnitude.
    return (min(pads) >= -GEOMETRY_TOLERANCE_PT
            and abs(pads[0] - pads[2]) <= GEOMETRY_TOLERANCE_PT
            and abs(pads[1] - pads[3]) <= GEOMETRY_TOLERANCE_PT)


def collect_drawing_paint_orders(page, *, drawings=None):
    """Return ``(orders, stats)``; orders is keyed by legacy ``draw_<seq>``.

    Values are dictionaries with source_order, source_seqnos, original_seqno,
    drawing_index and source_item_bbox_pt. Input drawing records are not changed.
    Every nonempty source path paint must be consumed in order. A merged fs
    record spanning another paint cannot be emitted as one native shape, so it
    is rejected. Only proven-empty path operations may intervene.
    """
    stats = {"drawing_records": 0, "source_path_paints": 0, "nonempty_path_paints": 0,
             "empty_path_paint_seqnos": [], "fill_stroke_drawings": 0,
             "remapped_drawings": 0, "unsupported_count": 0}
    if page.rotation:
        _fail("PAGE_ROTATION", stats)
    if drawings is None:
        drawings = page.get_drawings(extended=True)
    paints, empty = [], set()
    for seqno, (kind, bounds) in enumerate(page.get_bboxlog()):
        if kind not in _PATH_KINDS:
            continue
        stats["source_path_paints"] += 1
        if len(bounds) != 4 or not all(math.isfinite(float(v)) for v in bounds):
            _fail("BBOXLOG_GEOMETRY", stats)
        # An invalid/reversed MuPDF bounds sentinel proves there are no path
        # points. Do not use Rect.is_empty(): zero-width hairlines are valid.
        if bounds[2] < bounds[0] or bounds[3] < bounds[1]:
            empty.add(seqno)
            continue
        paints.append((seqno, kind, tuple(bounds)))
    stats["empty_path_paint_seqnos"] = sorted(empty)
    stats["nonempty_path_paints"] = len(paints)
    orders, cursor = {}, 0
    for drawing_index, drawing in enumerate(drawings):
        kind = drawing.get("type")
        if kind in ("clip", "group"):
            continue
        if kind not in ("f", "s", "fs"):
            _fail("PATH_TYPE", stats)
        stats["drawing_records"] += 1
        wanted = {"f": ("fill-path",), "s": ("stroke-path",),
                  "fs": ("fill-path", "stroke-path")}[kind]
        selected = paints[cursor:cursor + len(wanted)]
        if tuple(p[1] for p in selected) != wanted:
            _fail("PAINT_SEQUENCE", stats)
        if kind == "fs":
            stats["fill_stroke_drawings"] += 1
            if any(seqno not in empty for seqno in range(selected[0][0] + 1, selected[1][0])):
                _fail("MERGED_PAINT_ORDER", stats)
        bounds = _path_bounds(drawing, stats)
        if any(not _geometry_matches(bounds, p[2], p[1]) for p in selected):
            _fail("PAINT_GEOMETRY", stats)
        original_seqno = drawing.get("seqno")
        if original_seqno is not None and (isinstance(original_seqno, bool) or not isinstance(original_seqno, int)):
            _fail("LEGACY_ID", stats)
        source_id = f"draw_{original_seqno if original_seqno is not None else drawing_index}"
        if source_id in orders:
            _fail("DUPLICATE_LEGACY_ID", stats)
        source_seqnos = [p[0] for p in selected]
        orders[source_id] = {
            "source_order": source_seqnos[0], "source_seqnos": source_seqnos,
            "original_seqno": original_seqno, "drawing_index": drawing_index,
            "source_item_bbox_pt": list(bounds),
        }
        stats["remapped_drawings"] += int(original_seqno != source_seqnos[0])
        cursor += len(wanted)
    if cursor != len(paints):
        _fail("UNCONSUMED_PATH_PAINTS", stats)
    return orders, stats
