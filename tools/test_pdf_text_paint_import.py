"""Real-PDF regressions for visible paint order and text occurrence recovery."""
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import fitz
from PIL import Image
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from pdf_figure_import import convert_pdf_page


class TextPaintImportTests(unittest.TestCase):
    def test_late_white_page_fill_is_an_occluder_not_initial_background(self):
        with TemporaryDirectory() as tmp:
            source, output = Path(tmp)/'source.pdf', Path(tmp)/'candidate.pptx'
            doc = fitz.open()
            page = doc.new_page(width=180, height=120)
            page.insert_text((30, 60), 'COVERED', fontsize=18)
            page.draw_rect(page.rect, fill=(1, 1, 1), color=None)
            doc.save(source)
            doc.close()
            convert_pdf_page(source, output)
            shapes = list(Presentation(output).slides[0].shapes)
            self.assertEqual(len(shapes), 2, 'a late full-page white paint must remain a native occluder')
            self.assertEqual(shapes[0].text, 'COVERED')
            self.assertEqual(str(shapes[1].fill.fore_color.rgb), 'FFFFFF')

    def test_native_text_before_later_opaque_image_stays_behind_it(self):
        with TemporaryDirectory() as tmp:
            source, output = Path(tmp)/'source.pdf', Path(tmp)/'candidate.pptx'
            icon = BytesIO()
            Image.new('RGB', (120, 70), (20, 160, 170)).save(icon, 'PNG')
            doc = fitz.open()
            page = doc.new_page(width=180, height=120)
            page.insert_text((30, 72), 'CSV', fontname='hebo', fontsize=42,
                             color=(1, 1, 1))
            page.insert_image(fitz.Rect(24, 24, 160, 100), stream=icon.getvalue())
            doc.save(source)
            doc.close()
            convert_pdf_page(source, output)
            shapes = list(Presentation(output).slides[0].shapes)
            text = next(i for i, s in enumerate(shapes) if s.has_text_frame and s.text == 'CSV')
            picture = next(i for i, s in enumerate(shapes) if s.shape_type == MSO_SHAPE_TYPE.PICTURE)
            self.assertLess(text, picture, 'later source picture must cover earlier text')

    def test_three_vertical_text_operations_are_not_a_horizontal_word(self):
        with TemporaryDirectory() as tmp:
            source, output = Path(tmp)/'source.pdf', Path(tmp)/'candidate.pptx'
            doc = fitz.open()
            page = doc.new_page(width=180, height=120)
            for char, y in zip('CSV', (42, 51.3, 60.6)):
                page.insert_text((40, y), char, fontname='hebo', fontsize=12)
            doc.save(source)
            doc.close()
            convert_pdf_page(source, output)
            texts = [s for s in Presentation(output).slides[0].shapes
                     if s.has_text_frame and s.text.strip()]
            self.assertEqual([s.text for s in texts], list('CSV'))
            self.assertAlmostEqual(texts[0].left.pt, texts[1].left.pt, delta=.15)
            self.assertAlmostEqual(texts[1].left.pt, texts[2].left.pt, delta=.15)
            self.assertLess(texts[0].top, texts[1].top)
            self.assertLess(texts[1].top, texts[2].top)

    def test_visible_text_missing_from_raw_dictionary_is_recovered(self):
        with TemporaryDirectory() as tmp:
            source, output = Path(tmp)/'source.pdf', Path(tmp)/'candidate.pptx'
            doc = fitz.open()
            page = doc.new_page(width=180, height=120)
            page.insert_text((45, 70), 'A', fontsize=24, fill_opacity=0)
            page.insert_text((45, 70), 'A', fontsize=24, color=(1, 0, 0))
            doc.save(source)
            doc.close()
            try:
                convert_pdf_page(source, output)
            except ValueError as exc:
                self.fail(f'visible red A must survive the hidden raw span: {exc}')
            texts = [s for s in Presentation(output).slides[0].shapes
                     if s.has_text_frame and s.text.strip()]
            self.assertEqual([s.text for s in texts], ['A'])
            self.assertEqual(str(texts[0].text_frame.paragraphs[0].runs[0].font.color.rgb), 'FF0000')

    def test_badge_circle_keeps_black_underprint_behind_white_letter(self):
        with TemporaryDirectory() as tmp:
            source, output = Path(tmp)/'source.pdf', Path(tmp)/'candidate.pptx'
            doc = fitz.open()
            page = doc.new_page(width=180, height=120)
            page.insert_text((40, 64), 'A', fontsize=16, color=(0, 0, 0))
            page.draw_circle((45, 58), 13, fill=(0.02, .1, .4), color=None)
            page.insert_text((40, 64), 'A', fontsize=16, color=(1, 1, 1))
            doc.save(source)
            doc.close()
            convert_pdf_page(source, output)
            shapes = list(Presentation(output).slides[0].shapes)
            letters = [(i, s) for i, s in enumerate(shapes) if s.has_text_frame and s.text == 'A']
            self.assertEqual(len(letters), 2)
            circle = next(i for i, s in enumerate(shapes) if not (s.has_text_frame and s.text.strip()))
            self.assertLess(letters[0][0], circle)
            self.assertLess(circle, letters[1][0])
            self.assertEqual(str(letters[1][1].text_frame.paragraphs[0].runs[0].font.color.rgb), 'FFFFFF')


if __name__ == '__main__':
    unittest.main()
