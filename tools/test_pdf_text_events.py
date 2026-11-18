"""Real-PDF regressions for occurrence-preserving native text paint events.

The fixtures assert independently authored positions, colors and paint order;
they do not use collector internals to derive expectations.
"""
from __future__ import annotations

from io import BytesIO
import math
from pathlib import Path
import tempfile
import unittest

import fitz
from pypdf import PdfWriter
from pypdf.generic import (
    ArrayObject, DecodedStreamObject, DictionaryObject, FloatObject,
    NameObject, NumberObject,
)

try:
    from pdf_text_events import collect_text_events
except ModuleNotFoundError:
    collect_text_events = None


def _stream(writer, data):
    obj = DecodedStreamObject()
    obj.set_data(data.encode("ascii"))
    return writer._add_object(obj)


def _custom_pdf(content, unicode_hex=None, *, type3=False, type3_direct=False):
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=220)
    font = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
        NameObject("/Encoding"): NameObject("/WinAnsiEncoding"),
    })
    if unicode_hex is not None:
        font[NameObject("/ToUnicode")] = _stream(writer, f"""
/CIDInit /ProcSet findresource begin 12 dict begin begincmap
/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def
/CMapName /EventTest def /CMapType 2 def
1 begincodespacerange <00> <FF> endcodespacerange
3 beginbfchar <46> <{unicode_hex}> <41> <0041> <20> <0020> endbfchar
endcmap CMapName currentdict /CMap defineresource pop end end
""")
    if type3:
        font = DictionaryObject({
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type3"),
            NameObject("/FontBBox"): ArrayObject([NumberObject(v) for v in (0, 0, 600, 700)]),
            NameObject("/FontMatrix"): ArrayObject([FloatObject(v) for v in (.001, 0, 0, .001, 0, 0)]),
            NameObject("/CharProcs"): DictionaryObject({
                NameObject("/A"): _stream(writer, "600 0 0 0 600 700 d1 50 0 500 700 re f")}),
            NameObject("/Encoding"): DictionaryObject({
                NameObject("/Type"): NameObject("/Encoding"),
                NameObject("/Differences"): ArrayObject([NumberObject(65), NameObject("/A")])}),
            NameObject("/FirstChar"): NumberObject(65),
            NameObject("/LastChar"): NumberObject(65),
            NameObject("/Widths"): ArrayObject([NumberObject(600)]),
            NameObject("/Resources"): DictionaryObject(),
        })
    page[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({
            NameObject("/F1"): font if type3_direct else writer._add_object(font)})})
    page[NameObject("/Contents")] = _stream(writer, content)
    data = BytesIO()
    writer.write(data)
    return fitz.open(stream=data.getvalue(), filetype="pdf")


class TextPaintEventTests(unittest.TestCase):
    def collect(self, page, **kwargs):
        self.assertIsNotNone(collect_text_events, "trace-first collector is not implemented")
        return collect_text_events(page, **kwargs)

    def new_page(self):
        doc = fitz.open()
        self.addCleanup(doc.close)
        return doc.new_page(width=300, height=220)

    def test_ordinary_unique_raw_span_keeps_source_id_and_font_size(self):
        page = self.new_page()
        page.insert_text((40, 70), "Label", fontsize=16, color=(.2, .4, .6))
        events, stats = self.collect(page)
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event.source_id, "text_0_0_0")
        self.assertEqual(event.source_seqnos, (0,))
        self.assertEqual(event.span["text"], "Label")
        self.assertEqual(event.span["size"], 16)
        self.assertEqual(event.span["color"], 0x336699)
        self.assertEqual(event.span["origin"], (40, 70))
        self.assertEqual(event.line["dir"], (1, 0))
        self.assertEqual(event.paint_type, "fill")
        self.assertEqual(stats["unsupported_count"], 0)

    def test_duplicate_glyphs_survive_as_three_distinct_paint_occurrences(self):
        page = self.new_page()
        for color in ((1, 0, 0), (0, 0, 1), (0, 0, 1)):
            if page.get_contents():
                page.draw_rect((35, 50, 90, 75), color=None, fill=(1, 1, 1))
            page.insert_text((40, 70), "DUP", fontsize=16, color=color)
        events, _ = self.collect(page)
        self.assertEqual([e.seqno for e in events], [0, 2, 4])
        self.assertEqual([e.span["text"] for e in events], ["DUP"]*3)
        self.assertEqual([e.span["color"] for e in events], [0xFF0000, 0x0000FF, 0x0000FF])
        self.assertEqual(len({e.source_id for e in events}), 3)

    def test_trace_only_visible_layer_survives_rawdict_deduplication(self):
        page = self.new_page()
        page.insert_text((40, 70), "A", fontsize=16, fill_opacity=0)
        page.insert_text((40, 70), "A", fontsize=16, color=(1, 0, 0))
        events, stats = self.collect(page)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].seqno, 1)
        self.assertEqual(events[0].span["text"], "A")
        self.assertEqual(events[0].span["color"], 0xFF0000)
        self.assertEqual(events[0].span["alpha"], 255)
        self.assertEqual(stats["hidden_trace_count"], 1)
        self.assertEqual(stats["trace_only_event_count"], 1)

    def test_white_letter_after_circle_is_not_lost_to_earlier_black_letter(self):
        page = self.new_page()
        page.insert_text((40, 70), "A", fontsize=16)
        page.draw_circle((45, 64), 10, color=None, fill=(0, 0, 1))
        page.insert_text((40, 70), "A", fontsize=16, color=(1, 1, 1))
        events, _ = self.collect(page)
        self.assertEqual([e.seqno for e in events], [0, 2])
        self.assertEqual([e.span["color"] for e in events], [0, 0xFFFFFF])

    def test_dict_merged_vertical_letters_remain_on_their_source_baselines(self):
        page = self.new_page()
        for char, y in zip("CSV", (70, 75.3, 80.6)):
            page.insert_text((40, y), char, fontsize=6.8383889)
        events, _ = self.collect(page)
        self.assertEqual([e.span["text"] for e in events], ["C", "S", "V"])
        self.assertEqual([e.seqno for e in events], [0, 1, 2])
        for event, y in zip(events, (70, 75.3, 80.6)):
            self.assertAlmostEqual(event.span["origin"][0], 40, delta=.001)
            self.assertAlmostEqual(event.span["origin"][1], y, delta=.001)

    def test_one_trace_with_multiple_baselines_is_split_without_reordering(self):
        doc = _custom_pdf("BT /F1 12 Tf 1 0 0 1 40 150 Tm (C) Tj 0 -8 Td (S) Tj 0 -8 Td (V) Tj ET")
        self.addCleanup(doc.close)
        events, stats = self.collect(doc[0])
        self.assertEqual([e.span["text"] for e in events], ["C", "S", "V"])
        self.assertEqual([round(e.span["origin"][1], 3) for e in events], [70, 78, 86])
        self.assertEqual(len({e.source_id for e in events}), 3)
        self.assertGreater(stats["segmented_trace_count"], 0)

    def test_multiple_font_runs_in_one_paint_keep_unique_event_ids(self):
        doc = _custom_pdf("BT /F1 12 Tf 1 0 0 1 40 150 Tm (A) Tj /F1 16 Tf (B) Tj ET")
        self.addCleanup(doc.close)
        events, _ = self.collect(doc[0])
        self.assertEqual([e.span["text"] for e in events], ["A", "B"])
        self.assertEqual([e.seqno for e in events], [0, 0])
        self.assertEqual(len({e.source_id for e in events}), 2)

    def test_synthetic_space_preserves_the_real_gap_instead_of_joining_ab(self):
        doc = _custom_pdf("BT /F1 16 Tf 1 0 0 1 40 150 Tm [(A) -500 (B)] TJ ET")
        self.addCleanup(doc.close)
        events, stats = self.collect(doc[0])
        self.assertEqual([e.span["text"] for e in events], ["A", "B"])
        self.assertAlmostEqual(events[0].span["origin"][0], 40, delta=.001)
        self.assertAlmostEqual(events[1].span["origin"][0], 58.672, delta=.001)
        self.assertEqual(events[0].seqno, events[1].seqno)
        self.assertEqual(stats["segmented_trace_count"], 1)

    def test_adjacent_fill_stroke_pair_retains_both_source_paints_and_stroke(self):
        page = self.new_page()
        page.insert_text((40, 70), "DUAL", fontsize=16,
                         color=(1, 0, 0), fill=(0, 0, 1), render_mode=2)
        events, stats = self.collect(page)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].source_seqnos, (0, 1))
        self.assertEqual(events[0].paint_type, "fill_stroke")
        self.assertEqual(events[0].span["color"], 0x0000FF)
        self.assertEqual(tuple(events[0].evidence["stroke_trace"]["color"]), (1, 0, 0))
        self.assertGreater(events[0].evidence["stroke_trace"]["linewidth"], 0)
        self.assertEqual(stats["fill_stroke_pair_count"], 1)

    def test_unpaired_stroke_text_is_rejected_instead_of_silently_filled(self):
        page = self.new_page()
        page.insert_text((40, 70), "STROKE", fontsize=16, render_mode=1)
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED.*STROKE"):
            self.collect(page)

    def test_text_clipping_is_rejected_even_when_trace_omits_the_clip_event(self):
        page = self.new_page()
        page.insert_text((40, 70), "A", fontsize=16, render_mode=7)
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED.*CLIP"):
            self.collect(page)

    def test_type3_semantic_overlay_is_ignored_only_with_safe_no_clip_evidence(self):
        doc = _custom_pdf("BT /F1 16 Tf 1 0 0 1 40 150 Tm (A) Tj ET", type3=True)
        self.addCleanup(doc.close)
        self.assert_type3_source_preserved_or_rejected(doc[0])

    def assert_type3_source_preserved_or_rejected(self, page):
        # This is a source-authored rectangle mapped to Unicode A. MuPDF 1.26
        # exposes a native path plus ignore-text; 1.28 exposes visible Type3
        # text without a path. Neither API permits substituting an ordinary A.
        fonts = page.get_fonts(full=True)
        self.assertEqual(len(fonts), 1)
        self.assertEqual(page.parent.xref_get_key(fonts[0][0], "Subtype"),
                         ("name", "/Type3"))
        self.assertEqual(page.get_pixmap().pixel(44, 65), (0, 0, 0))
        traces = page.get_texttrace()
        self.assertEqual(len(traces), 1)
        ledger = page.get_bboxlog()
        if traces[0]["type"] == 3:
            events, stats = self.collect(page)
            self.assertEqual(events, [])
            self.assertEqual(stats["hidden_trace_count"], 1)
            self.assertEqual(ledger[traces[0]["seqno"]][0], "ignore-text")
            self.assertTrue(any(d["type"] == "f" for d in page.get_drawings()))
        else:
            self.assertEqual(traces[0]["type"], 0)
            self.assertGreater(traces[0]["opacity"], 0)
            self.assertEqual(ledger[traces[0]["seqno"]][0], "fill-text")
            with self.assertRaisesRegex(ValueError, "UNSUPPORTED_SOURCE_TYPE3_TEXT_PAINT"):
                self.collect(page)

    def test_named_type3_source_cannot_be_replaced_by_standard_font_text(self):
        for attributes in ({"Name": "NamedBox"}, {"BaseFont": "Helvetica"},
                           {"Name": "NamedBox", "BaseFont": "Helvetica"},
                           {"Name": "ABCDEF+NamedBox"},
                           {"Name": "Type3#20#28999#200#20R#29"}):
            with self.subTest(source_attributes=attributes):
                doc = _custom_pdf("BT /F1 16 Tf 1 0 0 1 40 150 Tm (A) Tj ET", type3=True)
                xref = doc[0].get_fonts(full=True)[0][0]
                for key, name in attributes.items():
                    doc.xref_set_key(xref, key, "/"+name)
                # Reopen to avoid reusing a pre-mutation font cache.
                reopened = fitz.open(stream=doc.tobytes(), filetype="pdf")
                doc.close()
                self.addCleanup(reopened.close)
                self.assert_type3_source_preserved_or_rejected(reopened[0])

    def test_direct_type3_is_not_authorized_by_an_ordinary_font_with_same_name(self):
        doc = _custom_pdf("BT /F1 16 Tf 1 0 0 1 40 150 Tm (A) Tj ET",
                          type3=True, type3_direct=True)
        page = doc[0]
        doc.xref_set_key(page.xref, "Resources/Font/F1/Name", "/Helvetica")
        doc.xref_set_key(page.xref, "Resources/Font/F1/BaseFont", "/DifferentBaseFont")
        page.insert_font(fontname="helv")  # An unused, unrelated ordinary font.
        reopened = fitz.open(stream=doc.tobytes(), filetype="pdf")
        doc.close()
        self.addCleanup(reopened.close)
        page = reopened[0]
        self.assertEqual(page.get_pixmap().pixel(44, 65), (0, 0, 0))
        self.assertTrue(any(f[0] == 0 and f[2] == "Type3" for f in page.get_fonts(full=True)))
        if page.get_texttrace()[0]["type"] == 3:
            events, _ = self.collect(page)
            self.assertEqual(events, [])
            self.assertTrue(page.get_drawings())
        else:
            with self.assertRaisesRegex(ValueError, "UNSUPPORTED_SOURCE_TYPE3_TEXT_PAINT"):
                self.collect(page)

    def test_unused_type3_basefont_alias_does_not_reject_real_type1_text(self):
        doc = _custom_pdf("", type3=True)
        self.addCleanup(doc.close)
        xref = doc[0].get_fonts(full=True)[0][0]
        doc.xref_set_key(xref, "BaseFont", "/Helvetica")
        page = doc[0]
        page.insert_text((40, 70), "REAL", fontsize=16)
        events, stats = self.collect(page)
        self.assertEqual([e.span["text"] for e in events], ["REAL"])
        self.assertEqual(stats["unsupported_count"], 0)

    def test_completely_off_crop_type3_paint_does_not_reject_visible_text(self):
        doc = _custom_pdf("BT /F1 16 Tf 1 0 0 1 40 150 Tm (A) Tj ET", type3=True)
        self.addCleanup(doc.close)
        page = doc[0]
        page.insert_text((90, 100), "IN", fontsize=12)
        page.set_cropbox(fitz.Rect(60, 60, 240, 180))
        events, stats = self.collect(page, strict_crop_edges=True)
        self.assertEqual([e.span["text"] for e in events], ["IN"])
        self.assertEqual(stats["unsupported_count"], 0)

    def test_both_audits_reject_ordinary_a_impersonating_a_type3_rectangle(self):
        from pptx import Presentation
        from pptx.util import Pt
        from audit_imported_pdf_figure import audit_figure
        from audit_text_geometry import audit_text_geometry
        from pdf_figure_import import _add_text, _annotate_source_shape

        doc = _custom_pdf("BT /F1 16 Tf 1 0 0 1 40 150 Tm (A) Tj ET", type3=True)
        self.addCleanup(doc.close)
        page = doc[0]
        line = page.get_text("dict")["blocks"][0]["lines"][0]
        deck = Presentation()
        deck.slide_width, deck.slide_height = Pt(300), Pt(220)
        slide = deck.slides.add_slide(deck.slide_layouts[6])
        # Deliberately forge a visible ordinary A, even when the older raw API
        # marks its semantic overlay alpha=0. Both auditors must reject it.
        _add_text(slide, {**line["spans"][0], "alpha": 255}, line, page.rect)
        _annotate_source_shape(slide.shapes[-1], "text_0_0_0",
                               page.get_texttrace()[0]["seqno"], "text")
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)/"type3_rectangle.pdf"
            candidate = Path(directory)/"wrong_ordinary_a.pptx"
            doc.save(source)
            deck.save(candidate)
            structure = audit_figure(source, candidate)
            geometry = audit_text_geometry(source, candidate)
        self.assertEqual(structure["status"], "FAIL")
        self.assertEqual(geometry["status"], "FAIL")
        if page.get_texttrace()[0]["type"] == 0:
            self.assertFalse(structure["checks"]["source_text_paint_supported"])
            self.assertFalse(geometry["source_text_collection_complete"])
            self.assertGreater(geometry["unsupported_source_text_paint_count"], 0)
            self.assertGreater(structure["source_text_spans"], 0)
            self.assertGreater(geometry["source_text_span_count"], 0)

    def test_completely_outside_crop_glyphs_do_not_require_rawdict_matches(self):
        page = self.new_page()
        page.insert_text((20, 35), "OUTSIDE", fontsize=12)
        page.insert_text((90, 100), "IN A B", fontsize=12)
        page.insert_text((230, 195), "EDGE", fontsize=12)
        page.set_cropbox(fitz.Rect(60, 60, 240, 180))
        events, stats = self.collect(page, strict_crop_edges=True)
        self.assertEqual("".join(e.span["text"] for e in events), "IN A B")
        self.assertEqual(stats["outside_glyph_count"], 11)
        self.assertEqual(stats["outside_trace_count"], 2)

    def test_partial_glyph_is_rejected_for_explicit_crop(self):
        page = self.new_page()
        page.insert_text((55, 100), "EDGE", fontsize=12)
        page.set_cropbox(fitz.Rect(60, 60, 240, 180))
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED.*CROP_EDGE_TEXT"):
            self.collect(page, strict_crop_edges=True)

    def test_partial_glyph_is_retained_for_legacy_full_page_audit(self):
        page = self.new_page()
        page.insert_text((55, 100), "EDGE", fontsize=12)
        page.set_cropbox(fitz.Rect(60, 60, 240, 180))
        events, _ = self.collect(page)
        self.assertEqual("".join(e.span["text"] for e in events), "EDGE")
        self.assertLess(events[0].span["bbox"][0], 0)

    def test_local_text_rotations_preserve_direction_without_axis_aligned_regrouping(self):
        for angle in (45, -45, 90, 180):
            with self.subTest(angle=angle):
                page = self.new_page()
                origin = fitz.Point(150, 110)
                page.insert_text(origin, "ROT", fontsize=14,
                                 morph=(origin, fitz.Matrix(angle)))
                events, _ = self.collect(page)
                self.assertEqual(len(events), 1)
                self.assertEqual(events[0].span["text"], "ROT")
                self.assertAlmostEqual(events[0].line["dir"][0], math.cos(math.radians(angle)), delta=1e-4)
                self.assertAlmostEqual(events[0].line["dir"][1], -math.sin(math.radians(angle)), delta=1e-4)

    def test_page_rotation_fails_closed_until_an_explicit_page_transform_exists(self):
        page = self.new_page()
        page.insert_text((40, 70), "PAGE", fontsize=14)
        page.set_rotation(90)
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED.*PAGE_ROTATION"):
            self.collect(page)

    def test_multichar_tounicode_continuation_is_not_dropped_or_bound_to_next_glyph(self):
        doc = _custom_pdf("BT /F1 16 Tf 1 0 0 1 40 150 Tm (FA) Tj ET", "00660069")
        self.addCleanup(doc.close)
        events, _ = self.collect(doc[0])
        self.assertEqual([e.span["text"] for e in events], ["fi", "A"])
        self.assertEqual([c[0] for e in events for c in e.chars], [102, 105, 65])
        self.assertEqual(events[0].chars[1][1], -1)
        self.assertAlmostEqual(events[1].span["origin"][0], 49.776, delta=.001)

    def test_source_ligature_unicode_is_preserved_without_global_nfkc(self):
        doc = _custom_pdf("BT /F1 16 Tf 1 0 0 1 40 150 Tm (FA) Tj ET", "FB01")
        self.addCleanup(doc.close)
        events, _ = self.collect(doc[0])
        self.assertEqual("".join(e.span["text"] for e in events), "\ufb01A")

    def test_unique_raw_match_corrects_small_trace_size_discrepancy(self):
        page = self.new_page()
        page.insert_text((40, 70), "Label", fontsize=12,
                         morph=(fitz.Point(40, 70), fitz.Matrix(1.02, 1)))
        events, stats = self.collect(page)
        self.assertEqual(len(events), 1)
        self.assertAlmostEqual(events[0].span["size"], 12.119405746459961, delta=.001)
        self.assertEqual(events[0].evidence["size_basis"], "unique_raw_span")
        self.assertEqual(stats["raw_size_correction_event_count"], 1)

    def test_ambiguous_same_position_occurrences_do_not_borrow_raw_font_size(self):
        page = self.new_page()
        for _ in range(2):
            page.insert_text((40, 70), "Label", fontsize=12,
                             morph=(fitz.Point(40, 70), fitz.Matrix(1.02, 1)))
        events, stats = self.collect(page)
        self.assertEqual(len(events), 2)
        self.assertTrue(all(e.evidence["size_basis"] == "trace" for e in events))
        self.assertTrue(all(abs(e.span["size"]-12.24) < .001 for e in events))
        self.assertEqual(stats["raw_size_correction_event_count"], 0)


if __name__ == "__main__":
    unittest.main()
