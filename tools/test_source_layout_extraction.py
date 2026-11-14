"""Source-first layout extraction tests; unknown topology must stay unknown."""
from __future__ import annotations

import io
import json
from pathlib import Path
import tempfile
import unittest

import fitz
from PIL import Image

from extract_source_layout import extract_source_layout


def make_two_panel_pdf(path: Path, *, labels=True, include_image=False):
    doc = fitz.open()
    page = doc.new_page(width=600, height=400)
    page.draw_rect(fitz.Rect(20, 40, 280, 350), color=(.1, .2, .4), width=1.2)
    page.draw_rect(fitz.Rect(320, 40, 580, 350), color=(.5, .2, .2), width=1.6)
    if labels:
        page.insert_text((32, 58), "(a)", fontsize=12, fontname="helv")
        page.insert_text((332, 58), "(b)", fontsize=14, fontname="tiro")
    page.draw_rect(fitz.Rect(65, 105, 180, 165), color=(.1, .3, .7),
                   fill=(.85, .9, .96), width=1.1)
    page.draw_line((180, 135), (230, 135), color=(.1, .3, .7), width=1.3)
    page.draw_circle(fitz.Point(230, 135), 7, color=(.1, .3, .7), fill=(.2, .6, .3))
    page.draw_rect(fitz.Rect(370, 115, 520, 205), color=(.5, .2, .2),
                   fill=(.98, .9, .88), width=1.6)
    if include_image:
        image = io.BytesIO()
        Image.new("RGB", (24, 16), (220, 120, 50)).save(image, "PNG")
        page.insert_image(fitz.Rect(400, 230, 520, 310), stream=image.getvalue())
    doc.save(path)
    doc.close()


class SourceLayoutExtractionTests(unittest.TestCase):
    def test_explicit_panel_markers_and_boundaries_are_detected_in_source_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "two_panel.pdf"
            make_two_panel_pdf(source)
            layout = extract_source_layout(source)
            self.assertEqual(layout["panel_detection"]["status"], "EXPLICIT_MARKERS_FOUND")
            self.assertEqual(len(layout["panel_detection"]["panels"]), 2)
            self.assertEqual([p["label"] for p in layout["panel_detection"]["panels"]], ["a", "b"])
            self.assertEqual([p["order"] for p in layout["panel_detection"]["panels"]], [1, 2])
            self.assertEqual(layout["page"]["aspect_ratio"], 1.5)

    def test_punctuated_label_without_enclosing_boundary_stays_unresolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "label_only.pdf"
            doc = fitz.open()
            page = doc.new_page(width=300, height=180)
            page.insert_text((30, 50), "(b)", fontsize=12)
            page.draw_line((40, 80), (250, 80), color=(.2, .2, .2), width=1)
            doc.save(source)
            doc.close()
            layout = extract_source_layout(source)
            self.assertEqual(layout["panel_detection"]["status"], "NO_CONFIRMED_PANEL_BOUNDARIES")
            self.assertEqual(layout["panel_detection"]["panels"], [])
            self.assertEqual(layout["panel_detection"]["unresolved_markers"][0]["label"], "b")

    def test_plain_single_letter_text_is_not_a_panel_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "single_letters.pdf"
            doc = fitz.open()
            page = doc.new_page(width=300, height=180)
            page.insert_text((30, 50), "a", fontsize=12)
            page.insert_text((50, 50), "b", fontsize=12)
            page.draw_rect(fitz.Rect(20, 20, 280, 160), color=(.2, .2, .2))
            doc.save(source)
            doc.close()
            layout = extract_source_layout(source)
            self.assertEqual(layout["panel_detection"]["panels"], [])
            self.assertEqual(layout["panel_detection"]["status"], "NO_EXPLICIT_PANEL_MARKERS")
            self.assertEqual(layout["figure_region_source"], "full_page_default")

    def test_no_panel_marker_does_not_invent_subpanels(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "unlabelled.pdf"
            make_two_panel_pdf(source, labels=False)
            layout = extract_source_layout(source)
            self.assertEqual(layout["panel_detection"]["status"], "NO_EXPLICIT_PANEL_MARKERS")
            self.assertEqual(layout["panel_detection"]["panels"], [])
            self.assertTrue(layout["requires_human_review"])

    def test_layout_elements_use_source_relative_coordinates(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "layout.pdf"
            make_two_panel_pdf(source)
            layout = extract_source_layout(source)
            self.assertGreater(len(layout["layout_elements"]), 0)
            for item in layout["layout_elements"]:
                x, y, w, h = item["bbox_normalized"]
                self.assertGreaterEqual(x, 0)
                self.assertGreaterEqual(y, 0)
                self.assertGreater(w, 0)
                self.assertGreater(h, 0)
                self.assertLessEqual(x + w, 1.0001)
                self.assertLessEqual(y + h, 1.0001)

    def test_connection_candidates_are_not_assumed_directed_without_arrowhead_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "edges.pdf"
            make_two_panel_pdf(source)
            layout = extract_source_layout(source)
            self.assertGreater(len(layout["stroke_segment_candidates"]), 0)
            self.assertTrue(all(edge["directedness"] == "undetermined"
                                for edge in layout["stroke_segment_candidates"]))
            self.assertTrue(all(edge["confidence"] in ("low", "medium")
                                for edge in layout["stroke_segment_candidates"]))

    def test_crop_region_excludes_other_panel_without_changing_source_page_ratio(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "two_panel.pdf"
            make_two_panel_pdf(source)
            layout = extract_source_layout(source, figure_region=(300, 0, 600, 400))
            self.assertEqual(len(layout["panel_detection"]["panels"]), 1)
            panel = layout["panel_detection"]["panels"][0]
            self.assertEqual(panel["label"], "b")
            self.assertAlmostEqual(layout["figure_region_pt"][2] - layout["figure_region_pt"][0], 300)
            self.assertEqual(layout["page"]["aspect_ratio"], 1.5)

    def test_style_profile_preserves_multiple_font_and_stroke_tiers(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "styles.pdf"
            make_two_panel_pdf(source)
            layout = extract_source_layout(source)
            self.assertIn("Helvetica", layout["style_profile"]["font_families"])
            self.assertIn("Times-Roman", layout["style_profile"]["font_families"])
            self.assertGreaterEqual(len(layout["style_profile"]["stroke_widths_pt"]), 2)
            self.assertGreaterEqual(len(layout["style_profile"]["palette"]), 2)

    def test_extracted_layout_conforms_to_versioned_schema(self):
        import jsonschema
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "schema.pdf"
            make_two_panel_pdf(source, include_image=True)
            layout = extract_source_layout(source)
            schema_path = Path(__file__).resolve().parents[1] / "specs" / "source_figure_layout.schema.json"
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            jsonschema.Draft202012Validator.check_schema(schema)
            jsonschema.validate(layout, schema)

    def test_image_occurrences_have_source_hash_and_local_crop_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "image_panel.pdf"
            make_two_panel_pdf(source, include_image=True)
            layout = extract_source_layout(source)
            self.assertEqual(len(layout["image_assets"]), 1)
            image = layout["image_assets"][0]
            self.assertEqual(len(image["sha256"]), 64)
            self.assertIn(image["source_kind"], ("xref", "image_block"))
            self.assertGreater(image["xref"], 0)
            self.assertEqual(image["panel_candidate"], "panel_b")


if __name__ == "__main__":
    unittest.main()
