"""Tests for the optional PaddleOCR/ONNX Runtime adapter."""
from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from source_layout_vision import run_paddleocr_backend, _load_paddleocr_models


class PaddleOCRBackendTests(unittest.TestCase):
    def tearDown(self):
        _load_paddleocr_models.cache_clear()
        sys.modules.pop("paddleocr", None)

    def test_missing_optional_dependency_has_actionable_error(self):
        _load_paddleocr_models.cache_clear()
        with patch.dict(sys.modules, {"paddleocr": None}):
            with self.assertRaisesRegex(RuntimeError, "PADDLEOCR_OPTIONAL_DEPENDENCY_MISSING"):
                run_paddleocr_backend(Path("figure.png"))

    def test_backend_uses_official_models_onnxruntime_and_preserves_nested_boxes(self):
        calls = {}

        class FakeLayout:
            def __init__(self, **kwargs):
                calls["layout_init"] = kwargs

            def predict(self, **kwargs):
                calls["layout_predict"] = kwargs
                return {"res": {"boxes": []}}

        class FakeOCR:
            def __init__(self, **kwargs):
                calls["ocr_init"] = kwargs

            def predict(self, **kwargs):
                calls["ocr_predict"] = kwargs
                return {"res": {"rec_texts": [], "rec_scores": [], "dt_polys": []}}

        fake = types.ModuleType("paddleocr")
        fake.__version__ = "3.7.0"
        fake.LayoutDetection = FakeLayout
        fake.PaddleOCR = FakeOCR
        with patch.dict(sys.modules, {"paddleocr": fake}):
            result = run_paddleocr_backend(
                Path("figure.png"),
                layout_model="PP-DocLayoutV3",
                ocr_det_model="PP-OCRv6_small_det",
                ocr_rec_model="PP-OCRv6_small_rec",
            )

        self.assertEqual(calls["layout_init"]["model_name"], "PP-DocLayoutV3")
        self.assertEqual(calls["layout_init"]["engine"], "onnxruntime")
        self.assertFalse(calls["layout_predict"]["layout_nms"])
        self.assertEqual(calls["layout_predict"]["layout_merge_bboxes_mode"], "union")
        self.assertEqual(calls["ocr_init"]["text_detection_model_name"], "PP-OCRv6_small_det")
        self.assertEqual(calls["ocr_init"]["text_recognition_model_name"], "PP-OCRv6_small_rec")
        self.assertEqual(calls["ocr_init"]["engine"], "onnxruntime")
        self.assertEqual(calls["layout_predict"]["input"], "figure.png")
        self.assertEqual(calls["ocr_predict"]["input"], "figure.png")
        self.assertEqual(result["backend"], "paddleocr")
        self.assertEqual(result["engine"], "onnxruntime")
        self.assertEqual(result["layout_model"], "PP-DocLayoutV3")
        self.assertEqual(result["paddleocr_version"], "3.7.0")
        self.assertIn("layout_result", result)
        self.assertIn("ocr_result", result)

    def test_model_initialization_error_is_not_silently_downgraded(self):
        class BrokenLayout:
            def __init__(self, **kwargs):
                raise OSError("model download failed")

        fake = types.ModuleType("paddleocr")
        fake.__version__ = "3.7.0"
        fake.LayoutDetection = BrokenLayout
        fake.PaddleOCR = object
        with patch.dict(sys.modules, {"paddleocr": fake}):
            with self.assertRaisesRegex(RuntimeError, "PADDLEOCR_MODEL_INITIALIZATION_FAILED"):
                run_paddleocr_backend(Path("figure.png"))

    def test_inference_error_is_reported_with_backend_context(self):
        class FakeLayout:
            def __init__(self, **kwargs):
                pass

            def predict(self, **kwargs):
                raise RuntimeError("invalid image")

        class FakeOCR:
            def __init__(self, **kwargs):
                pass

            def predict(self, **kwargs):
                return {}

        fake = types.ModuleType("paddleocr")
        fake.__version__ = "3.7.0"
        fake.LayoutDetection = FakeLayout
        fake.PaddleOCR = FakeOCR
        with patch.dict(sys.modules, {"paddleocr": fake}):
            with self.assertRaisesRegex(RuntimeError, "PADDLEOCR_INFERENCE_FAILED"):
                run_paddleocr_backend(Path("figure.png"))


if __name__ == "__main__":
    unittest.main()
