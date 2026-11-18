"""Collect native PDF text by paint occurrence, with conservative layout evidence.

``get_text('dict')`` is a reading-order view, not a display-list ledger: it can
merge different baselines or discard repeated text.  The trace is authoritative
for occurrences, color and paint order.  A uniquely matched raw span may supply
its familiar source ID, font metrics and the ordinary effective font size.

This module does not render text, infer missing Unicode, or discard occluded
text.  A paired fill/stroke event requires a caller that preserves its stroke;
the complete stroke trace is retained for that purpose.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import math
import re

import fitz

from pdf_text_visibility import TextVisibility


ORIGIN_TOLERANCE_PT = 0.02
SIZE_RELATIVE_TOLERANCE = 0.015
# These source ligatures can be decomposed by rawdict's default text flags.
# They are matching evidence only: the emitted trace Unicode is not NFKC'd.
_RAW_LIGATURE_EXPANSIONS = {
    "\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi",
    "\ufb04": "ffl", "\ufb05": "st", "\ufb06": "st",
}


@dataclass(frozen=True)
class TextPaintEvent:
    source_id: str
    seqno: int
    source_seqnos: tuple[int, ...]
    span: dict
    line: dict
    paint_type: str
    chars: tuple
    evidence: dict


class TextEventError(ValueError):
    """Unsupported source evidence; callers must not reinterpret it as PASS."""

    def __init__(self, message, stats):
        super().__init__(message)
        self.stats = dict(stats)


def _stats():
    return dict.fromkeys((
        "trace_count", "visible_trace_count", "hidden_trace_count",
        "outside_trace_count", "outside_glyph_count", "event_count",
        "segmented_trace_count", "fill_stroke_pair_count",
        "trace_only_event_count", "trace_only_char_count", "raw_matched_char_count",
        "raw_ambiguous_char_count", "raw_size_correction_event_count",
        "whitespace_only_segment_count", "unsupported_count",
    ), 0)


def _fail(stats, reason, detail=""):
    stats["unsupported_count"] += 1
    raise TextEventError(reason + (": " + detail if detail else ""), stats)


def _finite(values):
    return all(isinstance(v, (int, float)) and not isinstance(v, bool)
               and math.isfinite(v) for v in values)


def _near(a, b, tolerance=ORIGIN_TOLERANCE_PT):
    return len(a) == len(b) and all(abs(x-y) <= tolerance for x, y in zip(a, b))


def _color_int(trace, stats):
    color = trace.get("color")
    if isinstance(color, (int, float)):
        color = (color,)
    if not isinstance(color, (tuple, list)) or not _finite(color):
        _fail(stats, "UNSUPPORTED_SOURCE_TEXT_COLOR")
    if any(v < -1e-6 or v > 1.000001 for v in color):
        _fail(stats, "UNSUPPORTED_SOURCE_TEXT_COLOR")
    if trace.get("colorspace") == 1 and len(color) == 1:
        color = color * 3
    elif trace.get("colorspace") != 3 or len(color) != 3:
        _fail(stats, "UNSUPPORTED_SOURCE_TEXT_COLORSPACE", str(trace.get("colorspace")))
    rgb = [max(0, min(255, round(float(v)*255))) for v in color]
    return (rgb[0] << 16) | (rgb[1] << 8) | rgb[2]


def _checked_trace(trace, index, stats):
    try:
        seqno = trace["seqno"]
        direction = tuple(trace["dir"])
        size = trace["size"]
        opacity = trace["opacity"]
        if (isinstance(seqno, bool) or not isinstance(seqno, int) or seqno < 0 or
                len(direction) != 2 or not _finite(direction) or
                abs(math.hypot(*direction)-1) > .002 or
                not _finite((size, opacity, trace["ascender"], trace["descender"])) or
                size <= 0 or opacity < 0 or opacity > 1 or
                not isinstance(trace["font"], str) or not trace["font"]):
            raise ValueError("invalid trace scalar or transform")
        if trace.get("wmode", 0) != 0:
            _fail(stats, "UNSUPPORTED_SOURCE_TEXT_WRITING_MODE", f"trace {index}")
        chars = []
        for char in trace["chars"]:
            codepoint, gid, origin, box = char
            if (not isinstance(codepoint, int) or not 0 <= codepoint <= 0x10ffff or
                    0xd800 <= codepoint <= 0xdfff or
                    not isinstance(gid, int) or gid < -1 or
                    len(origin) != 2 or len(box) != 4 or
                    not _finite((*origin, *box))):
                raise ValueError("invalid glyph evidence")
            chars.append((codepoint, gid, tuple(origin), tuple(box)))
        return {**trace, "dir": direction, "chars": tuple(chars)}
    except TextEventError:
        raise
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        _fail(stats, "UNSUPPORTED_SOURCE_TEXT_TRACE", f"trace {index}: {exc}")


def _same_glyph_sequence(fill, stroke):
    if (fill.get("type") != 0 or stroke.get("type") != 1 or
            stroke["seqno"] != fill["seqno"]+1 or
            fill["font"] != stroke["font"] or
            abs(fill["size"]-stroke["size"]) > 1e-4 or
            fill.get("flags") != stroke.get("flags") or
            fill.get("wmode", 0) != stroke.get("wmode", 0) or
            not _near(fill["dir"], stroke["dir"], 1e-5) or
            len(fill["chars"]) != len(stroke["chars"])):
        return False
    return all(a[:2] == b[:2] and _near(a[2], b[2], 1e-4)
               and _near(a[3], b[3], 1e-4)
               for a, b in zip(fill["chars"], stroke["chars"]))


def _glyph_groups(trace, stats):
    groups = []
    for char in trace["chars"]:
        if char[1] == -1:
            # A ToUnicode continuation belongs to the preceding source glyph.
            # Its rawdict origin can be moved to that glyph's right edge.
            if not groups or not _near(char[2], groups[-1]["chars"][0][2]):
                _fail(stats, "UNSUPPORTED_SOURCE_TEXT_CONTINUATION")
            groups[-1]["chars"].append(char)
        else:
            groups.append({"chars": [char], "raw": None, "candidates": []})
    for group in groups:
        group["chars"] = tuple(group["chars"])
    return groups


class _RawEvidence:
    """Spatially indexed raw characters; never an occurrence-count authority."""

    def __init__(self, raw):
        self.rows = []
        self.index = defaultdict(list)
        for bi, block in enumerate(raw["blocks"]):
            for li, line in enumerate(block.get("lines", [])):
                for si, span in enumerate(line["spans"]):
                    row_index = len(self.rows)
                    row = {"source_id": f"text_{bi}_{li}_{si}",
                           "span": span, "line": line, "chars": span["chars"]}
                    self.rows.append(row)
                    for ci, char in enumerate(span["chars"]):
                        if char.get("synthetic"):
                            continue
                        x, y = char["origin"]
                        key = (span["font"], math.floor(x/ORIGIN_TOLERANCE_PT),
                               math.floor(y/ORIGIN_TOLERANCE_PT))
                        self.index[key].append((row_index, ci))

    @staticmethod
    def _text_match(group, row, start):
        chars = group["chars"]
        wanted = "".join(chr(c[0]) for c in chars)
        raw_chars = row["chars"]
        if (len(chars) == 1 and chars[0][0] == 0xfffd and chars[0][1] == 0
                and raw_chars[start]["c"] == "\x00"):
            return 1, "source_notdef_raw_nul"
        candidates = [(wanted, "exact")]
        if wanted in _RAW_LIGATURE_EXPANSIONS:
            candidates.append((_RAW_LIGATURE_EXPANSIONS[wanted], "source_ligature_expansion"))
        for expected, kind in candidates:
            selected = raw_chars[start:start+len(expected)]
            if len(selected) != len(expected) or any(c.get("synthetic") for c in selected):
                continue
            observed = "".join(c["c"] for c in selected)
            if observed.replace("\u00a0", " ") != expected.replace("\u00a0", " "):
                continue
            if len(chars) > 1:
                # A continuation has no independent advance in rawdict.
                dx, dy = row["line"].get("dir", (1, 0))
                if any((abs(c["bbox"][2]-c["bbox"][0]) > .02 if abs(dx) >= abs(dy)
                        else abs(c["bbox"][3]-c["bbox"][1]) > .02)
                       for c in selected[1:]):
                    continue
                kind = "multichar_tounicode"
            return len(expected), kind
        return None

    def match(self, group, trace, rgb):
        x, y = group["chars"][0][2]
        gx, gy = math.floor(x/ORIGIN_TOLERANCE_PT), math.floor(y/ORIGIN_TOLERANCE_PT)
        candidates = []
        for ix in range(gx-1, gx+2):
            for iy in range(gy-1, gy+2):
                for row_index, ci in self.index.get((trace["font"], ix, iy), ()):
                    row = self.rows[row_index]
                    span, line = row["span"], row["line"]
                    if (not _near(row["chars"][ci]["origin"], (x, y)) or
                            not _near(line.get("dir", (1, 0)), trace["dir"], .001) or
                            line.get("wmode", 0) != trace.get("wmode", 0) or
                            abs(span["size"]-trace["size"]) >
                            max(.02, SIZE_RELATIVE_TOLERANCE*trace["size"]) or
                            span.get("color") != rgb or
                            abs(span.get("alpha", 255)-round(trace["opacity"]*255)) > 1):
                        continue
                    matched = self._text_match(group, row, ci)
                    if matched:
                        count, kind = matched
                        candidates.append((row_index, ci, count, kind))
        return candidates


def _resolve_raw_matches(logical, raw, stats):
    uses = Counter()
    for item in logical:
        trace = item["trace"]
        for group in item["groups"]:
            candidates = raw.match(group, trace, item["rgb"])
            group["candidates"] = candidates
            if len(candidates) == 1:
                group["raw"] = candidates[0]
                ri, ci, count, _ = candidates[0]
                for char_index in range(ci, ci+count):
                    uses[ri, char_index] += 1
    for item in logical:
        for group in item["groups"]:
            match = group["raw"]
            if match:
                ri, ci, count, _ = match
                if any(uses[ri, i] != 1 for i in range(ci, ci+count)):
                    group["raw"] = None
            if group["raw"]:
                stats["raw_matched_char_count"] += len(group["chars"])
            elif group["candidates"]:
                stats["raw_ambiguous_char_count"] += len(group["chars"])


def _group_box(group, raw):
    if group["raw"]:
        ri, ci, count, _ = group["raw"]
        boxes = [c["bbox"] for c in raw.rows[ri]["chars"][ci:ci+count]]
    else:
        # Continuations have no ink; their primary glyph decides crop status.
        boxes = [group["chars"][0][3]]
    return fitz.Rect(min(b[0] for b in boxes), min(b[1] for b in boxes),
                     max(b[2] for b in boxes), max(b[3] for b in boxes))


def _crop_groups(logical, raw, region, strict, stats):
    visible = []
    for item in logical:
        groups = []
        for group in item["groups"]:
            box = _group_box(group, raw)
            if box.is_empty:
                point = fitz.Point(group["chars"][0][2])
                outside = not region.contains(point)
            else:
                outside = (box.x1 <= region.x0 or box.x0 >= region.x1 or
                           box.y1 <= region.y0 or box.y0 >= region.y1)
            if outside:
                stats["outside_glyph_count"] += len(group["chars"])
                continue
            if strict and (box.x0 < region.x0-.1 or box.y0 < region.y0-.1 or
                           box.x1 > region.x1+.1 or box.y1 > region.y1+.1):
                _fail(stats, "UNSUPPORTED_SOURCE_CROP_EDGE_TEXT",
                      f"paint {item['trace']['seqno']} glyph {group['chars'][0][0]}")
            groups.append(group)
        if groups:
            item["groups"] = groups
            visible.append(item)
        else:
            stats["outside_trace_count"] += len(item["trace_indices"])
    return visible


def _advance(group, trace):
    """Unrotate a trace glyph's metric box, whose normal height is trace.size."""
    box = group["chars"][0][3]
    dx, dy = map(abs, trace["dir"])
    if dx >= dy:
        width = ((box[2]-box[0])-dy*trace["size"])/max(dx, 1e-12)
    else:
        width = ((box[3]-box[1])-dx*trace["size"])/max(dy, 1e-12)
    return max(0.0, width)


def _split_reason(previous, current, trace, raw):
    a, b = previous["chars"][0][2], current["chars"][0][2]
    dx, dy = trace["dir"]
    delta = (b[0]-a[0], b[1]-a[1])
    along = delta[0]*dx + delta[1]*dy
    across = -delta[0]*dy + delta[1]*dx
    if abs(across) > max(.02, trace["size"]*.002):
        return "different_baseline"
    if along < -.02:
        return "backward_advance"
    if len(previous["chars"]) > 1 or len(current["chars"]) > 1:
        return "multichar_glyph_boundary"
    left, right = previous["raw"], current["raw"]
    if bool(left) != bool(right):
        return "raw_evidence_boundary"
    if left and right:
        if left[0] != right[0]:
            return "different_raw_span"
        between = raw.rows[left[0]]["chars"][left[1]+left[2]:right[1]]
        if any(c.get("synthetic") for c in between):
            return "synthetic_space_gap"
        if right[1] != left[1]+left[2]:
            return "noncontiguous_raw_chars"
    gap = along-_advance(previous, trace)
    if gap > max(.05, float(trace.get("spacewidth", 0))*0.45):
        return "source_advance_gap"
    return None


def _segments(item, raw):
    trace = item["trace"]
    result = []
    current = []
    reason = "trace_start"
    for group in item["groups"]:
        split = _split_reason(current[-1], group, trace, raw) if current else None
        if split:
            result.append((current, reason))
            current, reason = [], split
        current.append(group)
    if current:
        result.append((current, reason))
    return result


def _layout_span(groups, item, raw):
    trace = item["trace"]
    matches = [g["raw"] for g in groups]
    row_ids = {m[0] for m in matches if m is not None}
    unique_raw = all(m is not None for m in matches) and len(row_ids) == 1
    row = raw.rows[next(iter(row_ids))] if unique_raw else None
    metrics = row["span"] if row else trace
    size = float(metrics["size"])
    asc, desc = float(metrics["ascender"]), float(metrics["descender"])
    if row:
        boxes = [raw.rows[m[0]]["chars"][i]["bbox"]
                 for m in matches for i in range(m[1], m[1]+m[2])]
        bbox = (min(b[0] for b in boxes), min(b[1] for b in boxes),
                max(b[2] for b in boxes), max(b[3] for b in boxes))
    else:
        dx, dy = trace["dir"]
        nx, ny = -dy, dx
        points = []
        for group in groups:
            x, y = group["chars"][0][2]
            width = _advance(group, trace)
            for advance in (0, width):
                for height in (-asc*size, -desc*size):
                    points.append((x+advance*dx+height*nx, y+advance*dy+height*ny))
        bbox = (min(p[0] for p in points), min(p[1] for p in points),
                max(p[0] for p in points), max(p[1] for p in points))
    texts = []
    for group in groups:
        if group["raw"] and group["raw"][3] == "source_notdef_raw_nul":
            texts.append("□")
        else:
            texts.append("".join(chr(c[0]) for c in group["chars"]).replace("\x00", "□"))
    span = {
        "text": "".join(texts), "font": trace["font"], "size": size,
        "flags": int(metrics.get("flags", trace.get("flags", 0))),
        "ascender": asc, "descender": desc,
        "origin": tuple(groups[0]["chars"][0][2]), "bbox": tuple(bbox),
        "color": item["rgb"], "alpha": round(trace["opacity"]*255),
    }
    line = {"dir": tuple(trace["dir"]), "wmode": trace.get("wmode", 0)}
    return span, line, row


def _reject_visible_type3_fonts(page, logical, stats):
    """A Type3 Unicode mapping does not authorize a substitute font glyph.

    Older MuPDF versions expose the glyph paths and a separate ignore-text
    record. Newer versions can expose only a visible text record. The latter
    requires glyph-program reconstruction, which this collector does not do.
    Resource subtype and source /Name or XRef bind this check to the PDF;
    neither a display-font name alone nor unused Type3 resources hide text.
    """
    if not logical:
        return
    try:
        fonts = page.get_fonts(full=True)
        type3 = [font for font in fonts if font[2] == "Type3"]
        if not type3:
            return
        names, xrefs = set(), set()
        for font in type3:
            xref = font[0]
            xrefs.add(xref)
            if not isinstance(xref, int) or xref <= 0:
                # Another resource with the same name cannot prove which
                # direct font painted the glyph. Do not authorize a fallback.
                _fail(stats, "UNSUPPORTED_SOURCE_TYPE3_TEXT_PAINT",
                      "direct Type3 font resource has no verifiable XRef")
            if page.parent.xref_get_key(xref, "Subtype") != ("name", "/Type3"):
                _fail(stats, "UNSUPPORTED_SOURCE_TYPE3_TEXT_PAINT", "unverified source font subtype")
            name_kind, name = page.parent.xref_get_key(xref, "Name")
            if name_kind == "name":
                # get_fonts()[3] can prefer /BaseFont even when the actual
                # Type3 display name comes from a different source /Name.
                source_name = name.removeprefix("/")
                names.update((source_name, re.sub(r"^[A-Z]{6}\+", "", source_name)))
            else:
                # Type3 /BaseFont is not its display name in either supported
                # API. Treating it as one would reject an unrelated Helvetica.
                names.add("Unnamed-T3")
        for item in logical:
            trace = item["trace"]
            name = trace["font"]
            indirect = re.fullmatch(r"Type3 \((\d+) \d+ R\)", name)
            if name in names or indirect and int(indirect[1]) in xrefs:
                _fail(stats, "UNSUPPORTED_SOURCE_TYPE3_TEXT_PAINT",
                      f"paint {trace['seqno']}, source font {name!r}; visible glyph program is not native text")
    except TextEventError:
        raise
    except (AttributeError, IndexError, KeyError, RuntimeError, TypeError, ValueError) as exc:
        _fail(stats, "UNSUPPORTED_SOURCE_TYPE3_TEXT_PAINT", f"source font evidence: {exc}")


def collect_text_events(page, *, strict_crop_edges=False):
    """Return ``(events, stats)`` in source paint order, or fail closed.

    Explicit figure crops should set ``strict_crop_edges=True``.  In the legacy
    full-page mode, partially visible glyphs retain their inherited overflow;
    only provably fully outside glyphs are removed. Page rotation requires a
    separate whole-page transform and is deliberately unsupported here.
    """
    stats = _stats()
    if page.rotation:
        _fail(stats, "UNSUPPORTED_SOURCE_PAGE_ROTATION")
    # This also catches Tr=7, which can have raw glyphs but no trace at all.
    if not TextVisibility(page)._no_text_clipping():
        _fail(stats, "UNSUPPORTED_SOURCE_TEXT_CLIPPING")
    try:
        source_traces = page.get_texttrace()
        raw = _RawEvidence(page.get_text("rawdict"))
    except (AttributeError, RuntimeError, TypeError, ValueError, KeyError) as exc:
        _fail(stats, "UNSUPPORTED_SOURCE_TEXT_TRACE", str(exc))
    stats["trace_count"] = len(source_traces)
    traces = [_checked_trace(trace, index, stats) for index, trace in enumerate(source_traces)]
    if not traces and any(c["c"].strip() for r in raw.rows for c in r["chars"]):
        _fail(stats, "UNSUPPORTED_SOURCE_TEXT_TRACE_MISSING")

    logical = []
    index = 0
    while index < len(traces):
        trace = traces[index]
        kind = trace.get("type")
        pair = traces[index+1] if index+1 < len(traces) else None
        if pair is not None and _same_glyph_sequence(trace, pair):
            pair_indices = (index, index+1)
            stats["fill_stroke_pair_count"] += 1
            index += 2
        else:
            pair, pair_indices = None, (index,)
            index += 1
        paints = [trace, pair] if pair else [trace]
        if kind not in (0, 1, 3):
            _fail(stats, "UNSUPPORTED_SOURCE_TEXT_PAINT_TYPE", str(kind))
        if all(p.get("type") == 3 or p["opacity"] == 0 for p in paints):
            stats["hidden_trace_count"] += len(pair_indices)
            continue
        if kind == 1:
            _fail(stats, "UNSUPPORTED_SOURCE_TEXT_STROKE", f"paint {trace['seqno']}")
        if kind != 0:
            _fail(stats, "UNSUPPORTED_SOURCE_TEXT_PAINT_TYPE", str(kind))
        item = {"trace": trace, "stroke": pair, "trace_indices": pair_indices,
                "groups": _glyph_groups(trace, stats), "rgb": _color_int(trace, stats)}
        logical.append(item)

    _resolve_raw_matches(logical, raw, stats)
    logical = _crop_groups(logical, raw, fitz.Rect(page.rect), strict_crop_edges, stats)
    stats["visible_trace_count"] = sum(len(item["trace_indices"]) for item in logical)
    _reject_visible_type3_fonts(page, logical, stats)
    pending = []
    for item in logical:
        pieces = _segments(item, raw)
        if len(pieces) > 1:
            stats["segmented_trace_count"] += 1
        for local_index, (groups, reason) in enumerate(pieces):
            span, line, row = _layout_span(groups, item, raw)
            if not span["text"].strip():
                stats["whitespace_only_segment_count"] += 1
                continue
            raw_ids = sorted({raw.rows[g["raw"][0]]["source_id"]
                              for g in groups if g["raw"]})
            candidate_id = None
            if row is not None:
                covered = {i for g in groups for i in range(g["raw"][1],
                                                           g["raw"][1]+g["raw"][2])}
                if covered == set(range(len(row["chars"]))):
                    candidate_id = row["source_id"]
            pending.append(dict(item=item, groups=groups, span=span, line=line,
                                row=row, reason=reason, local_index=local_index,
                                raw_ids=raw_ids, candidate_id=candidate_id))

    id_uses = Counter(row["candidate_id"] for row in pending if row["candidate_id"])
    pending.sort(key=lambda row: (row["item"]["trace"]["seqno"],
                                  row["item"]["trace_indices"][0], row["local_index"]))
    events = []
    sequence_segments = Counter()
    for row in pending:
        item, groups, span = row["item"], row["groups"], row["span"]
        trace, stroke = item["trace"], item["stroke"]
        seqno = trace["seqno"]
        segment_index = sequence_segments[seqno]
        sequence_segments[seqno] += 1
        candidate_id = row["candidate_id"]
        source_id = (candidate_id if candidate_id and id_uses[candidate_id] == 1
                     else f"textpaint_{seqno}_{segment_index}")
        chars = tuple(c for group in groups for c in group["chars"])
        unmatched = sum(len(group["chars"]) for group in groups if not group["raw"])
        if unmatched:
            stats["trace_only_event_count"] += 1
            stats["trace_only_char_count"] += unmatched
        raw_size = row["row"] is not None
        if raw_size and abs(span["size"]-trace["size"]) > .001:
            stats["raw_size_correction_event_count"] += 1
        evidence = {
            "trace_index": item["trace_indices"][0],
            "trace_indices": item["trace_indices"],
            "segment_index": segment_index, "local_segment_index": row["local_index"],
            "segment_reason": row["reason"],
            "raw_source_ids": row["raw_ids"],
            "raw_char_matches": [dict(source_id=raw.rows[g["raw"][0]]["source_id"],
                                      char_index=g["raw"][1], char_count=g["raw"][2],
                                      kind=g["raw"][3]) for g in groups if g["raw"]],
            "size_basis": "unique_raw_span" if raw_size else "trace",
            "trace_size_pt": trace["size"], "source_font": trace["font"],
            "trace_only_char_count": unmatched,
            "visibility": "source_paint", "opacity": trace["opacity"],
            "color": trace["color"], "colorspace": trace["colorspace"],
            "fill_trace": trace,
        }
        if stroke:
            evidence["stroke_trace"] = stroke
        if any(g["raw"] and g["raw"][3] == "source_notdef_raw_nul" for g in groups):
            evidence["unicode_status"] = "UNRESOLVED_SOURCE_NOTDEF_RAW_NUL"
        events.append(TextPaintEvent(
            source_id=source_id, seqno=seqno,
            source_seqnos=(seqno, stroke["seqno"]) if stroke else (seqno,),
            span=span, line=row["line"], paint_type="fill_stroke" if stroke else "fill",
            chars=chars, evidence=evidence,
        ))
    stats["event_count"] = len(events)
    return events, stats
