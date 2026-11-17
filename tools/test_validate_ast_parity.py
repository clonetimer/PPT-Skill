#!/usr/bin/env python3
"""Unit tests for native object and raster parity gates."""
from __future__ import annotations
import tempfile, unittest
from pathlib import Path
from PIL import Image
from pptx import Presentation
from pptx.util import Inches
from validate_ast_parity import validate


class AstParityTests(unittest.TestCase):
    def _deck(self,path:Path,text:str):
        deck=Presentation()
        slide=deck.slides.add_slide(deck.slide_layouts[6])
        box=slide.shapes.add_textbox(Inches(1),Inches(1),Inches(2),Inches(.5))
        box.text=text
        deck.save(path)

    def test_equal_objects_and_pixels_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); a,b=root/"a.pptx",root/"b.pptx"
            self._deck(a,"same"); self._deck(b,"same")
            Image.new("RGB",(16,16),(10,20,30)).save(root/"a.png")
            Image.new("RGB",(16,16),(10,20,30)).save(root/"b.png")
            report=validate(a,b,root/"a.png",root/"b.png",root/"diff.png")
            self.assertEqual(report["status"],"PASS")
            self.assertEqual(report["legacy"]["slides"][0]["shape_count"],1)

    def test_slide_size_change_fails_even_if_objects_and_pixels_match(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); a,b=root/"a.pptx",root/"b.pptx"
            self._deck(a,"same")
            deck=Presentation()
            deck.slide_width=Inches(12)
            slide=deck.slides.add_slide(deck.slide_layouts[6])
            box=slide.shapes.add_textbox(Inches(1),Inches(1),Inches(2),Inches(.5))
            box.text="same"
            deck.save(b)
            Image.new("RGB",(16,16),(10,20,30)).save(root/"a.png")
            Image.new("RGB",(16,16),(10,20,30)).save(root/"b.png")
            report=validate(a,b,root/"a.png",root/"b.png",root/"diff.png")
            self.assertEqual(report["status"],"FAIL")
            self.assertIn("SLIDE_SIZE_MISMATCH",report["issues"])

    def test_picture_inventory_change_is_reported_explicitly(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); a,b=root/"a.pptx",root/"b.pptx"
            image_path=root/"pixel.png"
            Image.new("RGB",(1,1),(10,20,30)).save(image_path)
            deck=Presentation()
            slide=deck.slides.add_slide(deck.slide_layouts[6])
            slide.shapes.add_picture(str(image_path),Inches(1),Inches(1),Inches(.5),Inches(.5))
            deck.save(a)
            deck=Presentation()
            slide=deck.slides.add_slide(deck.slide_layouts[6])
            slide.shapes.add_shape(1,Inches(1),Inches(1),Inches(.5),Inches(.5))
            deck.save(b)
            Image.new("RGB",(16,16),(10,20,30)).save(root/"a.png")
            Image.new("RGB",(16,16),(10,20,30)).save(root/"b.png")
            report=validate(a,b,root/"a.png",root/"b.png",root/"diff.png")
            self.assertEqual(report["status"],"FAIL")
            self.assertIn("PICTURE_COUNT_MISMATCH:1",report["issues"])

    def test_text_change_fails_even_if_raster_matches(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); a,b=root/"a.pptx",root/"b.pptx"
            self._deck(a,"source"); self._deck(b,"changed")
            Image.new("RGB",(16,16),(10,20,30)).save(root/"a.png")
            Image.new("RGB",(16,16),(10,20,30)).save(root/"b.png")
            report=validate(a,b,root/"a.png",root/"b.png",root/"diff.png")
            self.assertEqual(report["status"],"FAIL")
            self.assertIn("TEXT_SEQUENCE_MISMATCH:1",report["issues"])


if __name__=="__main__":
    unittest.main()
