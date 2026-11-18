"""Conservative paint-aware handling of zero-alpha PDF text overlays.

The text dictionary reports fill alpha even when a glyph has a visible stroke.
Only matched, wholly non-painting text traces prove that an overlay is hidden.
Ambiguous or unsupported paint stays required by audits and blocks import.
This does not infer visibility from text color or from a white raster region.
"""
from __future__ import annotations

from collections import Counter
import math

import fitz
from pypdf.generic import ContentStream, DecodedStreamObject


class TextVisibility:
    def __init__(self, page):
        self.page = page
        self._loaded = False
        self._traces = None
        self._clip_safe = None

    def _no_text_clipping(self):
        """Conservatively reject Tr 4..7 in page or reachable Form streams.

        MuPDF paint traces and drawings omit the clipping action of transparent
        text in modes 4..6. Parse operators, including nested Forms, rather than
        searching bytes (comments, strings and split streams are not operators).
        An unrelated clipping run may cause a safe false positive here.
        """
        if self._clip_safe is None:
            self._clip_safe = False
            try:
                streams = [self.page.read_contents()]
                streams.extend(self.page.parent.xref_stream(xref)
                               for xref in {x[0] for x in self.page.get_xobjects()})
                for raw in streams:
                    stream = DecodedStreamObject()
                    stream.set_data(raw)
                    for operands, operator in ContentStream(stream, None).operations:
                        if operator == b"Tr":
                            if len(operands) != 1 or float(operands[0]) not in (0, 1, 2, 3):
                                return False
                self._clip_safe = True
            except Exception:
                # Parsing is evidence gathering. An unreadable stream must not
                # authorize deleting a source run or make the audit pass.
                return False
        return self._clip_safe

    def classify(self, span):
        """Return visible, hidden, or unsupported; only hidden may be omitted."""
        if span.get("alpha", 255) != 0:
            return "visible"
        # Clip-only text may affect subsequent artwork even without a fill.
        if span.get("char_flags", 0) & 64:
            return "unsupported"
        if not self._no_text_clipping():
            return "unsupported"
        if not self._loaded:
            self._loaded = True
            try:
                self._traces = self.page.get_texttrace()
            except (AttributeError, RuntimeError, ValueError):
                self._traces = None
        if not self._traces:
            return "unsupported"
        try:
            box = fitz.Rect(span["bbox"])
            box += (-.01, -.01, .01, .01)
            glyphs = set()
            origin_matched = False
            for trace in self._traces:
                if not box.intersects(fitz.Rect(trace["bbox"])):
                    continue
                if (trace.get("font") != span.get("font") or
                        abs(trace.get("size", 0) - span.get("size", 0)) > .01):
                    continue
                kind = trace.get("type")
                opacity = trace.get("opacity")
                for codepoint, _, origin, bounds in trace.get("chars", ()):
                    glyph_box = fitz.Rect(bounds)
                    # Baselines can lie outside Type3 glyph bounding boxes.
                    # Ignore incidental overlap with an adjacent character.
                    if (glyph_box.is_empty or
                            (box & glyph_box).get_area() < .5 * glyph_box.get_area()):
                        continue
                    if kind != 3 and (kind not in (0, 1) or
                            not isinstance(opacity, (int, float)) or
                            not math.isfinite(opacity) or opacity != 0):
                        return "unsupported"
                    if math.dist(origin, span["origin"]) <= .02:
                        origin_matched = True
                    glyphs.add((codepoint, round(origin[0], 4), round(origin[1], 4)))
            observed = Counter(chr(codepoint) for codepoint, _, _ in glyphs
                               if not chr(codepoint).isspace())
            expected = Counter(c for c in span.get("text", "") if not c.isspace())
            if origin_matched and expected and observed == expected:
                return "hidden"
        except (KeyError, TypeError, ValueError, OverflowError):
            pass
        return "unsupported"
