#!/usr/bin/env python3
"""Tests for font metrics, fit solvers and WCAG contrast calculations."""
from __future__ import annotations
import shutil, unittest
from text_layout_metrics import FontMetrics, binary_search_min_height, contrast_ratio, fit_font_size, fit_textbox_height, resolve_font_face, resolve_font_file


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

    def test_ttc_font_resolution_selects_the_requested_cjk_face(self):
        path, face_index, resolved = resolve_font_face("Noto Sans CJK SC")
        self.assertEqual(resolved, "Noto Sans CJK SC")
        self.assertEqual(path.suffix.lower(), ".ttc")
        self.assertEqual(face_index, 2)
        metrics = FontMetrics(path, face_index=face_index)
        try:
            self.assertEqual(metrics.family_name, "Noto Sans CJK SC")
            self.assertGreater(metrics.text_width_pt("中文测试", 14), 0)
        finally:
            metrics.close()

    def test_missing_math_subscript_uses_a_fontconfig_fallback_face(self):
        path, face_index, resolved = resolve_font_face("Cambria Math")
        metrics = FontMetrics(path, face_index=face_index)
        try:
            self.assertGreater(metrics.text_width_pt("ₜ", 14), 0)
            self.assertIn("U+209C", metrics.fallback_fonts)
            fallback = metrics.fallback_fonts["U+209C"]
            self.assertTrue(fallback["resolved_family"])
            self.assertNotEqual(
                (fallback["font_file"], fallback["font_face_index"]),
                (str(path), face_index),
            )
        finally:
            metrics.close()

    def test_glyph_vertical_offsets_use_the_selected_fallback_face(self):
        path, face_index, _ = resolve_font_face("Cambria Math")
        metrics = FontMetrics(path, face_index=face_index)
        try:
            base_top, base_bottom = metrics.glyph_vertical_offsets_pt("h", 14)
            sub_top, sub_bottom = metrics.glyph_vertical_offsets_pt("ₜ", 14)
            self.assertLess(base_top, 0)
            self.assertGreater(base_bottom, 0)
            self.assertLess(sub_top, 0)
            self.assertGreater(sub_bottom, 0)
            self.assertIn("U+209C", metrics.fallback_fonts)
            self.assertNotEqual((base_top, base_bottom), (sub_top, sub_bottom))
        finally:
            metrics.close()

    def test_glyph_outline_bounds_are_available_for_math_and_fallback_glyphs(self):
        path, face_index, _ = resolve_font_face("Cambria Math")
        metrics = FontMetrics(path, face_index=face_index)
        try:
            delta = metrics.glyph_ink_offsets_pt("Δ", 14)
            subscript = metrics.glyph_ink_offsets_pt("ₜ", 14)
            self.assertIsNotNone(delta)
            self.assertIsNotNone(subscript)
            for bounds in (delta, subscript):
                left, bottom, right, top = bounds
                self.assertLess(left, right)
                self.assertLess(bottom, top)
                self.assertLess(right - left, 20)
                self.assertLess(top - bottom, 20)
            self.assertIn("U+209C", metrics.fallback_fonts)
        finally:
            metrics.close()

    def test_wcag_contrast_ratio(self):
        self.assertAlmostEqual(contrast_ratio("#000000","#FFFFFF"),21.0,places=4)
        self.assertLess(contrast_ratio("#777777","#FFFFFF"),4.5)
        self.assertGreater(contrast_ratio("#1A1A1A","#FFFFFF"),4.5)


if __name__ == "__main__":
    unittest.main()
