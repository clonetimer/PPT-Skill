#!/usr/bin/env python3
"""Integration test for deterministic headless LibreOffice rendering."""
from __future__ import annotations
import shutil, tempfile, unittest
from pathlib import Path
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt
from render_with_libreoffice import render_pptx


class LibreOfficeRendererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        missing=[name for name in ("soffice","pdftoppm","pdfinfo","pdffonts","fc-match") if not shutil.which(name)]
        if missing:
            raise unittest.SkipTest("missing headless render tools: "+", ".join(missing))

    def test_repeat_render_png_hashes_are_stable_and_environment_is_recorded(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); source=root/"minimal.pptx"
            deck=Presentation(); deck.slide_width=Inches(13.333); deck.slide_height=Inches(7.5)
            slide=deck.slides.add_slide(deck.slide_layouts[6])
            box=slide.shapes.add_textbox(Inches(1),Inches(1),Inches(5),Inches(1))
            run=box.text_frame.paragraphs[0].add_run()
            run.text="PPT-Skill canonical renderer"; run.font.name="DejaVu Sans"
            run.font.size=Pt(24); run.font.color.rgb=RGBColor(30,60,90)
            deck.save(source)
            first=render_pptx(source,root/"first")
            second=render_pptx(source,root/"second")
            first_hashes=[p["sha256"] for p in first["outputs"]["pages"]]
            second_hashes=[p["sha256"] for p in second["outputs"]["pages"]]
            self.assertEqual(first_hashes,second_hashes)
            self.assertEqual(len(first_hashes),1)
            self.assertEqual(first["renderer"]["renderer"],"LibreOffice headless")
            self.assertTrue(first["renderer"]["libreoffice_version"])
            self.assertTrue(first["renderer"]["poppler_version"])
            self.assertIn("DejaVu Sans",first["renderer"]["requested_fonts"])
            self.assertEqual(first["powerpoint_host_round_trip"]["status"],"not_tested")
            self.assertTrue((root/"first"/"render_record.json").is_file())


if __name__ == "__main__":
    unittest.main()
