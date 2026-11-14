"""Integration tests for optional visual evidence in the SourceLayout extractor."""
from __future__ import annotations

import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import fitz
from PIL import Image, ImageDraw

import extract_source_layout as extractor


def make_raster_figure_pdf(path: Path):
    image = Image.new("RGB", (400, 300), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 20, 180, 140), outline="#1F4E79", width=3, fill="#EAF2F8")
    draw.rectangle((220, 20, 380, 140), outline="#9C5700", width=3, fill="#FCE4D6")
    payload = io.BytesIO()
    image.save(payload, format="PNG")
    document = fitz.open()
    page = document.new_page(width=400, height=300)
    page.insert_image(fitz.Rect(0, 0, 400, 300), stream=payload.getvalue())
    document.save(path)
    document.close()


def fake_backend(image_path):
    assert Path(image_path).exists()
    return {
        "backend": "paddleocr",
        "engine": "onnxruntime",
        "paddleocr_version": "3.7.0",
        "layout_model": "PP-DocLayoutV2",
        "ocr_detection_model": "PP-OCRv6_small_det",
        "ocr_recognition_model": "PP-OCRv6_small_rec",
        "layout_result": {
            "res": {
                "boxes": [
                    {"label": "image", "score": 0.94, "coordinate": [10, 10, 190, 150]},
                    {"label": "image", "score": 0.93, "coordinate": [210, 10, 390, 150]},
                ]
            }
        },
        "ocr_result": {
            "res": {
                "rec_texts": ["(a)", "(b)"],
                "rec_scores": [0.98, 0.97],
                "dt_polys": [
                    [[16, 16], [30, 16], [30, 30], [16, 30]],
                    [[216, 16], [230, 16], [230, 30], [216, 30]],
                ],
            }
        },
    }


class SourceLayoutVisionIntegrationTests(unittest.TestCase):
    def test_default_mode_is_model_free_and_records_not_requested(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "figure.pdf"
            make_raster_figure_pdf(source)
            with patch.object(extractor, "run_paddleocr_backend",
                              side_effect=AssertionError("backend must not load")):
                layout = extractor.extract_source_layout(source, figure_region=(0, 0, 400, 300))
        self.assertEqual(layout["schema_version"], "1.1.0")
        self.assertEqual(layout["visual_evidence"]["backend"], "none")
        self.assertEqual(layout["visual_evidence"]["status"], "NOT_REQUESTED")
        self.assertEqual(layout["panel_detection"]["visual_region_candidates"], [])
        self.assertEqual(layout["panel_detection"]["panel_hypotheses"], [])

    def test_paddleocr_backend_produces_crop_relative_nested_and_marker_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "figure.pdf"
            make_raster_figure_pdf(source)
            with patch.object(extractor, "run_paddleocr_backend", side_effect=fake_backend) as backend:
                layout = extractor.extract_source_layout(
                    source,
                    figure_region=(0, 0, 400, 300),
                    vision_backend="paddleocr",
                    vision_dpi=72,
                    vision_max_side=1000,
                )
                backend.assert_called_once()
        detection = layout["panel_detection"]
        self.assertEqual(layout["schema_version"], "1.1.0")
        self.assertEqual(layout["visual_evidence"]["status"], "COMPLETED")
        self.assertEqual(layout["visual_evidence"]["raster_size_px"], [400, 300])
        self.assertEqual(layout["visual_evidence"]["layout_model"], "PP-DocLayoutV2")
        self.assertEqual(len(detection["visual_region_candidates"]), 2)
        self.assertEqual([item["label"] for item in detection["panel_hypotheses"]], ["a", "b"])
        self.assertEqual(
            [item["axis"] for item in detection["visual_alignment_groups"]],
            ["horizontal_row"],
        )
        self.assertTrue(all(item["needs_human_review"]
                            for item in detection["visual_region_candidates"]))
        self.assertTrue(all(item["needs_human_review"]
                            for item in detection["panel_hypotheses"]))

    def test_unknown_backend_and_invalid_raster_limits_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "figure.pdf"
            make_raster_figure_pdf(source)
            with self.assertRaisesRegex(ValueError, "UNSUPPORTED_VISION_BACKEND"):
                extractor.extract_source_layout(source, vision_backend="unknown")
            with self.assertRaisesRegex(ValueError, "INVALID_VISION_RASTER_LIMITS"):
                extractor.extract_source_layout(source, vision_backend="paddleocr", vision_dpi=0)

    def test_visual_output_conforms_to_versioned_source_layout_schema(self):
        import jsonschema
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "figure.pdf"
            make_raster_figure_pdf(source)
            with patch.object(extractor, "run_paddleocr_backend", side_effect=fake_backend):
                layout = extractor.extract_source_layout(
                    source, figure_region=(0, 0, 400, 300),
                    vision_backend="paddleocr", vision_dpi=72,
                )
            schema_path = Path(__file__).resolve().parents[1] / "specs" / "source_figure_layout.schema.json"
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            jsonschema.Draft202012Validator.check_schema(schema)
            jsonschema.validate(layout, schema)


if __name__ == "__main__":
    unittest.main()
