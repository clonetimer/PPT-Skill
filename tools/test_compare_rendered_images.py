#!/usr/bin/env python3
"""Unit tests for raster parity comparison."""
from __future__ import annotations
import tempfile, unittest
from pathlib import Path
from PIL import Image
from compare_rendered_images import compare


class CompareRenderedImagesTests(unittest.TestCase):
    def test_identical_images_have_zero_difference(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); first=root/"a.png"; second=root/"b.png"
            Image.new("RGB",(16,16),(10,20,30)).save(first)
            Image.new("RGB",(16,16),(10,20,30)).save(second)
            report=compare(first,second,root/"diff.png")
            self.assertEqual(report["mean_absolute_error"],0)
            self.assertEqual(report["changed_pixel_ratio"],0)

    def test_changed_pixels_are_reported(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); first=root/"a.png"; second=root/"b.png"
            Image.new("RGB",(16,16),(10,20,30)).save(first)
            Image.new("RGB",(16,16),(40,50,60)).save(second)
            report=compare(first,second,root/"diff.png")
            self.assertGreater(report["mean_absolute_error"],0)
            self.assertEqual(report["changed_pixel_ratio"],1)


if __name__=="__main__":
    unittest.main()
