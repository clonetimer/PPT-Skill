#!/usr/bin/env python3
"""Regression test for glyph-level PDF matching and per-glyph font fallback."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt

from calibrate_text_fit_against_pdf import calibrate
from render_with_libreoffice import render_pptx

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "profiles/renderer/lo_headless_v1.json"


class PdfTextCalibrationTests(unittest.TestCase):
    def test_adjacent_text_boxes_and_split_subscript_glyphs_are_matched(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            pptx_path = root / "text-calibration.pptx"
            deck = Presentation()
            deck.slide_width = Inches(8)
            deck.slide_height = Inches(4)
            slide = deck.slides.add_slide(deck.slide_layouts[6])

            examples = [
                (1.0, 1.0, 2.8, 0.55, "Layer l · Regular windows"),
                (4.0, 1.0, 3.0, 0.55, "Layer l+1 · Shifted windows"),
                (1.0, 2.0, 6.0, 0.55, "Schematic: Δₜ, Bₜ and Cₜ"),
                (1.0, 2.8, 3.0, 0.70, "Shift by\\n(2, 2)"),
                (4.2, 2.8, 3.2, 0.70, "Illustration: shift=(⌊M/2⌋, ⌊M/2⌋)."),
            ]
            for x, y, width, height, value in examples:
                shape = slide.shapes.add_textbox(
                    Inches(x), Inches(y), Inches(width), Inches(height)
                )
                shape.text_frame.word_wrap = True
                shape.text_frame.margin_left = Inches(0.02)
                shape.text_frame.margin_right = Inches(0.02)
                shape.text_frame.margin_top = Inches(0.01)
                shape.text_frame.margin_bottom = Inches(0.01)
                shape.text = value
                for paragraph in shape.text_frame.paragraphs:
                    for run in paragraph.runs:
                        run.font.name = "Arial"
                        run.font.size = Pt(14)
            deck.save(pptx_path)

            render = render_pptx(
                pptx_path, root / "render", profile_path=PROFILE
            )
            report = calibrate(
                pptx_path, Path(render["outputs"]["pdf"]["path"])
            )

            self.assertEqual(report["text_shapes"], 5)
            self.assertEqual(report["missing_text_count"], 0, report["elements"])
            self.assertEqual(report["rendered_text_outside_frame_count"], 0, report["elements"])
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(
                {item["text"] for item in report["elements"]},
                {value for _, _, _, _, value in examples},
            )
            note = next(item for item in report["elements"] if "Schematic:" in item["text"])
            self.assertIn("U+209C", note["font_fallbacks"])


if __name__ == "__main__":
    unittest.main()
