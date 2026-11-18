"""Real PDF regressions for canonical vector paint order across extraction APIs."""
from __future__ import annotations

from copy import deepcopy
import unittest

import fitz


def source_with_stream(content):
    doc = fitz.open()
    page = doc.new_page(width=240, height=140)
    page.draw_line((10, 10), (20, 20))
    doc.update_stream(page.get_contents()[0], content)
    return doc, page


class DrawingPaintOrderTests(unittest.TestCase):
    def collect(self, page, **kwargs):
        try:
            from pdf_drawing_events import collect_drawing_paint_orders
        except ModuleNotFoundError as exc:
            if exc.name == "pdf_drawing_events":
                self.fail("Missing canonical drawing paint order reconciliation")
            raise
        return collect_drawing_paint_orders(page, **kwargs)

    def test_empty_stroke_does_not_move_later_white_mask_before_text(self):
        with fitz.open() as doc:
            page = doc.new_page(width=240, height=140)
            page.insert_text((40, 70), "HIDDEN", fontsize=16, color=(1, 0, 0))
            xref = page.get_contents()[0]
            doc.update_stream(xref, b"q S Q\n" + doc.xref_stream(xref))
            page.draw_rect((35, 50, 120, 80), color=None, fill=(1, 1, 1))
            legacy = page.get_drawings(extended=True)[0]["seqno"]
            # Newer MuPDF versions omit the empty operation from bboxlog too.
            # Require the source's actual text-before-cover order in either
            # representation, rather than a version-specific numeric index.
            ledger = page.get_bboxlog()
            cover_order = next(i for i, (kind, bounds) in enumerate(ledger)
                               if kind == "fill-path" and fitz.Rect(bounds) == fitz.Rect(35, 50, 120, 80))
            empty = [i for i, (kind, b) in enumerate(ledger)
                     if kind == "stroke-path" and (b[2] < b[0] or b[3] < b[1])]
            orders, stats = self.collect(page)
            self.assertLess(page.get_texttrace()[0]["seqno"], cover_order)
            self.assertEqual(orders[f"draw_{legacy}"]["source_order"], cover_order)
            self.assertEqual(orders[f"draw_{legacy}"]["source_seqnos"], [cover_order])
            self.assertEqual(stats["empty_path_paint_seqnos"], empty)

    def test_horizontal_zero_width_hairline_is_kept(self):
        doc, page = source_with_stream(b"q S 0 w 30 90 m 180 90 l S Q")
        try:
            ledger = page.get_bboxlog()
            line_paints = [i for i, (kind, b) in enumerate(ledger)
                           if kind == "stroke-path" and b[2] >= b[0] and b[3] >= b[1]]
            self.assertEqual(len(line_paints), 1)
            drawing = page.get_drawings()[0]
            self.assertEqual(drawing["width"], 0)
            self.assertEqual(drawing["rect"].height, 0)
            orders, stats = self.collect(page)
            self.assertEqual([o["source_order"] for o in orders.values()], line_paints)
            self.assertEqual(stats["nonempty_path_paints"], 1)
        finally:
            doc.close()

    def test_adjacent_fill_and_stroke_keep_both_paint_numbers(self):
        doc, page = source_with_stream(b"q 1 0 0 rg 20 30 80 60 re B Q")
        try:
            orders, _ = self.collect(page)
            self.assertEqual([o["source_seqnos"] for o in orders.values()], [[0, 1]])
        finally:
            doc.close()

    def test_merged_fill_and_stroke_across_text_are_rejected(self):
        with fitz.open() as doc:
            page = doc.new_page(width=240, height=140)
            page.draw_rect((20, 30, 100, 90), color=None, fill=(1, 0, 0))
            page.insert_text((40, 70), "Between", fontsize=12)
            page.draw_rect((20, 30, 100, 90), color=(0, 0, 0), fill=None)
            with self.assertRaisesRegex(ValueError, "MERGED_PAINT_ORDER"):
                self.collect(page)

    def test_only_proven_empty_path_may_separate_merged_fill_and_stroke(self):
        doc, page = source_with_stream(b"q 1 0 0 rg 20 30 80 60 re f S 20 30 80 60 re S Q")
        try:
            ledger = page.get_bboxlog()
            visible_paths = [(i, kind) for i, (kind, b) in enumerate(ledger)
                             if b[2] >= b[0] and b[3] >= b[1]]
            self.assertEqual([kind for _, kind in visible_paths], ["fill-path", "stroke-path"])
            empty = [i for i, (kind, b) in enumerate(ledger)
                     if kind == "stroke-path" and (b[2] < b[0] or b[3] < b[1])]
            orders, stats = self.collect(page)
            self.assertEqual([o["source_seqnos"] for o in orders.values()],
                             [[i for i, _ in visible_paths]])
            self.assertEqual(stats["empty_path_paint_seqnos"], empty)
        finally:
            doc.close()

    def test_path_geometry_reordering_is_rejected_instead_of_nearest_matching(self):
        doc, page = source_with_stream(b"q 20 30 40 20 re f 100 60 30 15 re f Q")
        try:
            drawings = page.get_drawings(extended=True)
            with self.assertRaisesRegex(ValueError, "GEOMETRY"):
                self.collect(page, drawings=list(reversed(drawings)))
        finally:
            doc.close()

    def test_legacy_seqnos_are_ids_and_do_not_determine_actual_order(self):
        doc, page = source_with_stream(b"q 20 30 40 20 re f 100 60 30 15 re f Q")
        try:
            drawings = deepcopy(page.get_drawings(extended=True))
            drawings[0]["seqno"], drawings[1]["seqno"] = 999, 4
            orders, _ = self.collect(page, drawings=drawings)
            self.assertEqual(orders["draw_999"]["source_order"], 0)
            self.assertEqual(orders["draw_4"]["source_order"], 1)
        finally:
            doc.close()


if __name__ == "__main__":
    unittest.main()
