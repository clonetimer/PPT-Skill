"""Real-PDF checks for the deliberately limited native text-outline recovery."""
from __future__ import annotations

from types import SimpleNamespace
import unittest

import fitz
import numpy as np


def fixture(text="I", *, fill=(0, 0, 1), stroke=(1, 0, 0), clip=False,
            text_matrix=None, **kwargs):
    doc = fitz.open()
    page = doc.new_page(width=120, height=100)
    page.insert_text((40, 70), text, fontsize=16, color=stroke,
                     fill=fill, render_mode=2, **kwargs)
    if text_matrix is not None:
        xref = page.get_contents()[0]
        data = doc.xref_stream(xref)
        original = b"1 0 0 1 40 30 Tm"
        assert data.count(original) == 1
        doc.update_stream(xref, data.replace(original, text_matrix))
    if clip:
        xref = page.get_contents()[0]
        data = doc.xref_stream(xref)
        doc.update_stream(xref, b"q 41 0 1 100 re W n\n" + data + b"\nQ")
    traces = page.get_texttrace()
    fill_trace = next(t for t in traces if t["type"] == 0)
    stroke_trace = next(t for t in traces if t["type"] == 1)
    event = SimpleNamespace(
        seqno=fill_trace["seqno"],
        source_seqnos=(fill_trace["seqno"], stroke_trace["seqno"]),
        chars=fill_trace["chars"],
        span={"font": fill_trace["font"], "size": fill_trace["size"],
              "text": text},
        line={"dir": fill_trace["dir"]}, paint_type="fill_stroke",
        evidence={"stroke_trace": stroke_trace},
    )
    return doc, page, event


def painted_pixels(page, clip):
    pix = page.get_pixmap(matrix=fitz.Matrix(12, 12), clip=clip, alpha=False)
    return np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3)


def render_records(records, page_rect):
    doc = fitz.open()
    page = doc.new_page(width=page_rect.width, height=page_rect.height)
    for record in records:
        shape = page.new_shape()
        for path in record["paths"]:
            shape.draw_polyline(path + [path[0]])
        shape.finish(color=None, fill=record["fill"], even_odd=False,
                     fill_opacity=record["opacity"], closePath=True)
        shape.commit()
    return doc, page


class TextOutlineTests(unittest.TestCase):
    def recover(self, page, event):
        try:
            from pdf_text_outlines import recover_text_outlines
        except ModuleNotFoundError as error:
            if error.name == "pdf_text_outlines":
                self.fail("Missing source-bound native outline recovery")
            raise
        return recover_text_outlines(page, event)

    def test_real_pdf_retains_blue_fill_and_red_stroke_geometry(self):
        source, page, event = fixture()
        records = self.recover(page, event)
        self.assertEqual([tuple(r["fill"]) for r in records], [(0, 0, 1), (1, 0, 0)])
        self.assertEqual([tuple(r["source_seqnos"]) for r in records],
                         [(event.source_seqnos[0],), (event.source_seqnos[1],)])
        self.assertTrue(all(tuple(r["provenance"]["source_seqnos"]) == event.source_seqnos
                            for r in records))
        candidate, made = render_records(records, page.rect)
        clip = fitz.Rect(38, 55, 47, 73)
        wanted, observed = painted_pixels(page, clip), painted_pixels(made, clip)
        active = np.any(wanted < 250, axis=2) | np.any(observed < 250, axis=2)
        error = np.abs(wanted.astype(float) - observed.astype(float))[active].mean() / 255
        self.assertLess(error, .025, "Native fill/stroke regions must match the painted source, including the blue interior")
        source.close()
        candidate.close()

    def test_opaque_same_color_symbol_retains_source_affine_geometry(self):
        source, page, event = fixture(
            "+", fill=(0, 0, 0), stroke=(0, 0, 0),
            text_matrix=b"1.2 0 0 .8 40 30 Tm")
        records = self.recover(page, event)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["provenance"]["paint_role"], "opaque_fill_stroke_union")
        candidate, made = render_records(records, page.rect)
        clip = fitz.Rect(38, 55, 57, 74)
        wanted, observed = painted_pixels(page, clip), painted_pixels(made, clip)
        active = np.any(wanted < 250, axis=2) | np.any(observed < 250, axis=2)
        error = np.abs(wanted.astype(float) - observed.astype(float))[active].mean() / 255
        self.assertLess(error, .025)
        source.close()
        candidate.close()

    def test_non_similarity_stroke_ctm_is_explicitly_unsupported(self):
        # MuPDF's text rasterizer and path/SVG stroker disagree for this CTM.
        # Keep the proven support boundary explicit rather than accepting a
        # 7.6% painted-region mismatch or adjusting the source glyph by eye.
        source, page, event = fixture(
            "+", fill=(0, 0, 0), stroke=(0, 0, 0),
            morph=(fitz.Point(40, 70), fitz.Matrix(1.2, .8)))
        with self.assertRaisesRegex(ValueError, "NON_SIMILARITY_STROKE_CTM"):
            self.recover(page, event)
        source.close()

    def test_curve_event_is_rejected_as_a_whole(self):
        source, page, event = fixture("DUAL")
        with self.assertRaisesRegex(ValueError, "CURVED_GLYPH"):
            self.recover(page, event)
        source.close()

    def test_source_clip_cutting_glyph_is_rejected(self):
        source, page, event = fixture(clip=True)
        with self.assertRaisesRegex(ValueError, "OUTLINE_CLIP"):
            self.recover(page, event)
        source.close()

    def test_coincident_identical_paints_require_unambiguous_occurrence(self):
        source, page, event = fixture()
        page.insert_text((40, 70), "I", fontsize=16, color=(1, 0, 0),
                         fill=(0, 0, 1), render_mode=2)
        with self.assertRaisesRegex(ValueError, "AMBIGUOUS_OCCURRENCE"):
            self.recover(page, event)
        source.close()

    def test_wrong_character_origin_cannot_borrow_another_source_outline(self):
        source, page, event = fixture()
        cp, gid, origin, box = event.chars[0]
        event.chars = ((cp, gid, (origin[0] + 1, origin[1]), box),)
        with self.assertRaisesRegex(ValueError, "EVENT_IDENTITY"):
            self.recover(page, event)
        source.close()

    def test_transparent_fill_stroke_knockout_compositing_is_rejected(self):
        source, page, event = fixture(fill_opacity=.7, stroke_opacity=.4)
        with self.assertRaisesRegex(ValueError, "TRANSPARENT_COMPOSITING"):
            self.recover(page, event)
        source.close()

    def test_stroke_collapsing_a_different_color_interior_is_rejected(self):
        source, page, event = fixture(border_width=3)
        with self.assertRaisesRegex(ValueError, "COLLAPSED_STROKE|SELF_INTERSECTION"):
            self.recover(page, event)
        source.close()


if __name__ == "__main__":
    unittest.main()
