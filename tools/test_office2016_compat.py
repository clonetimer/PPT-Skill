"""Conservative Office 2016 OOXML portability preflight tests."""
from __future__ import annotations

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
import zipfile

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_office2016_compat import audit_pptx


class Office2016PreflightTests(unittest.TestCase):
    def _deck(self, path: Path) -> None:
        deck = Presentation()
        slide = deck.slides.add_slide(deck.slide_layouts[6])
        shape = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(1), Inches(1), Inches(2), Inches(1)
        )
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(230, 238, 245)
        shape.line.color.rgb = RGBColor(30, 60, 90)
        box = slide.shapes.add_textbox(Inches(1), Inches(2.2), Inches(4), Inches(.5))
        run = box.text_frame.paragraphs[0].add_run()
        run.text = "Editable scientific label"
        run.font.name = "Arial"
        run.font.size = Pt(16)
        deck.save(path)

    def _rewrite(self, source: Path, target: Path, extra: dict[str, bytes]) -> None:
        with zipfile.ZipFile(source) as src, zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as dst:
            for item in src.infolist():
                dst.writestr(item, src.read(item.filename))
            for name, content in extra.items():
                dst.writestr(name, content)

    def test_native_shapes_and_windows_fonts_pass(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "native.pptx"
            self._deck(path)
            report = audit_pptx(path)
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["zip_integrity"], "PASS")
            self.assertIn("Arial", report["fonts"])
            self.assertEqual(report["unsupported_media"], [])

    def test_svg_media_fails_conservative_office_profile(self):
        with TemporaryDirectory() as temp:
            source = Path(temp) / "native.pptx"
            target = Path(temp) / "svg.pptx"
            self._deck(source)
            self._rewrite(source, target, {"ppt/media/image1.svg": b"<svg/>"})
            report = audit_pptx(target)
            self.assertEqual(report["status"], "FAIL")
            self.assertTrue(any("image1.svg" in failure for failure in report["failures"]))

    def test_embedded_ole_fails_conservative_office_profile(self):
        with TemporaryDirectory() as temp:
            source = Path(temp) / "native.pptx"
            target = Path(temp) / "ole.pptx"
            self._deck(source)
            self._rewrite(source, target, {"ppt/embeddings/oleObject1.bin": b"test"})
            report = audit_pptx(target)
            self.assertEqual(report["status"], "FAIL")
            self.assertTrue(any("OLE/ActiveX" in failure for failure in report["failures"]))

    def test_unknown_font_is_warning_not_false_certification(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "unknown-font.pptx"
            self._deck(path)
            deck = Presentation(path)
            for shape in deck.slides[0].shapes:
                if shape.has_text_frame and shape.text:
                    for paragraph in shape.text_frame.paragraphs:
                        for run in paragraph.runs:
                            run.font.name = "PrivateSubsetFont123"
            deck.save(path)
            report = audit_pptx(path)
            self.assertEqual(report["status"], "PASS")
            self.assertIn("PrivateSubsetFont123", report["unknown_fonts"])
            self.assertTrue(report["warnings"])


if __name__ == "__main__":
    unittest.main()
