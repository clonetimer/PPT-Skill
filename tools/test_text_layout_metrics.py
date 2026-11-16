#!/usr/bin/env python3
"""Tests for font metrics, fit solvers and WCAG contrast calculations."""
from __future__ import annotations
import shutil, unittest
from text_layout_metrics import FontMetrics, binary_search_min_height, contrast_ratio, fit_font_size, fit_textbox_height, resolve_font_file


class TextLayoutMetricsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which("fc-match"):
            raise unittest.SkipTest("fontconfig not installed")
        cls.font_path = resolve_font_file("DejaVu Sans")
        cls.metrics = FontMetrics(cls.font_path)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "metrics"):
            cls.metrics.close()

    def test_measurement_wraps_and_reports_geometry(self):
        result = self.metrics.measure("A long scientific label with multiple words",14,1.2,.6,margins_pt=(1,1,.5,.5))
        self.assertGreaterEqual(result["line_count"],2)
        self.assertGreater(result["required_height_pt"],0)
        self.assertIsInstance(result["fits"],bool)

    def test_fit_font_size_uses_binary_search_and_never_exceeds_preferred(self):
        result = fit_font_size(self.metrics,"A long scientific label with multiple words",1.2,.4,preferred_size_pt=24,min_size_pt=7)
        self.assertTrue(result.fits)
        self.assertLessEqual(result.selected_font_size_pt,24)
        self.assertGreaterEqual(result.selected_font_size_pt,7)
        self.assertEqual(result.reason,"binary_search_max_fitting_size")

    def test_unfit_minimum_is_reported_not_silently_shrunk(self):
        result = fit_font_size(self.metrics,"A very long scientific label that cannot fit",.25,.12,preferred_size_pt=18,min_size_pt=12)
        self.assertFalse(result.fits)
        self.assertIsNone(result.selected_font_size_pt)
        self.assertEqual(result.reason,"minimum_size_does_not_fit")

    def test_minimum_height_binary_search_accepts_render_probe(self):
        result = binary_search_min_height(lambda height: height >= 24.0,4,80)
        self.assertTrue(result["fits"])
        self.assertGreaterEqual(result["height_pt"],24.0)
        self.assertLessEqual(result["height_pt"],24.5)

    def test_textbox_height_is_solved_by_binary_search(self):
        result = fit_textbox_height(
            self.metrics, "A compact scientific label", 14, 1.2,
            min_height_pt=2, max_height_pt=80,
        )
        self.assertTrue(result["fits"])
        self.assertGreater(result["height_pt"], 2)
        self.assertLessEqual(result["height_pt"], 80)
        self.assertEqual(result["reason"], "binary_search_minimum_height")

    def test_wcag_contrast_ratio(self):
        self.assertAlmostEqual(contrast_ratio("#000000","#FFFFFF"),21.0,places=4)
        self.assertLess(contrast_ratio("#777777","#FFFFFF"),4.5)
        self.assertGreater(contrast_ratio("#1A1A1A","#FFFFFF"),4.5)


if __name__ == "__main__":
    unittest.main()
