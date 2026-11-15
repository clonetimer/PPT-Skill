"""Bound high-density PDFs without emitting partial editable presentation files."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import fitz
from pdf_figure_import import convert_pdf_page


def dense_source(filename: Path, segments: int = 24):
    doc = fitz.open()
    p = doc.new_page(width=300, height=200)
    for i in range(segments):
        x = 10 + i % 12 * 17
        y = 10 + i // 12 * 17
        p.draw_line((x, y), (x + 9, y + 4), color=(.1, .2, .4), width=.6)
    doc.save(filename)
    doc.close()


class ResourceBudgetTests(unittest.TestCase):
    def test_aborts_on_drawings_before_writing_pptx(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "dense.pdf"
            out = Path(tmp) / "no.pptx"
            dense_source(src)
            with self.assertRaisesRegex(ValueError, "RESOURCE_LIMIT: drawings"):
                convert_pdf_page(src, out, max_drawings=10)
            self.assertFalse(out.exists())

    def test_aborts_on_source_segments_before_freeform_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "dense.pdf"
            out = Path(tmp) / "no.pptx"
            dense_source(src)
            with self.assertRaisesRegex(ValueError, "RESOURCE_LIMIT: source_segments"):
                convert_pdf_page(src, out, max_source_segments=10)
            self.assertFalse(out.exists())

    def test_aborts_on_expanded_vertex_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "curve.pdf"
            out = Path(tmp) / "no.pptx"
            doc = fitz.open()
            p = doc.new_page(width=300, height=150)
            p.draw_bezier((30, 80), (60, 10), (100, 120), (140, 75), color=(0, 0, 0), width=1)
            doc.save(src)
            doc.close()
            with self.assertRaisesRegex(ValueError, "RESOURCE_LIMIT: estimated_vertices"):
                convert_pdf_page(src, out, max_vertices=6)
            self.assertFalse(out.exists())

    def test_wall_time_budget_yields_controlled_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "simple.pdf"
            out = Path(tmp) / "no.pptx"
            dense_source(src, 3)
            with self.assertRaisesRegex(ValueError, "RESOURCE_LIMIT: time"):
                convert_pdf_page(src, out, max_seconds=1e-9)
            self.assertFalse(out.exists())

    def test_normal_source_still_generates_and_reports_usage(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "source.pdf"
            out = Path(tmp) / "result.pptx"
            dense_source(src, 4)
            report = convert_pdf_page(src, out)
            self.assertTrue(out.exists())
            self.assertEqual(report["resource_profile"]["drawings"], 4)
            self.assertLessEqual(report["resource_profile"]["estimated_vertices"], 250000)
            self.assertGreater(report["resource_profile"]["elapsed_seconds"], 0)


if __name__ == "__main__":
    unittest.main()
