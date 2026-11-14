"""Deterministic tests for evidence-based reconstruction route selection."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from source_layout_review import create_source_layout_review_template
from source_reconstruction_router import build_reconstruction_routes, write_reconstruction_routes


def make_layout():
    return {
        "schema_version": "1.1.0",
        "source": {"filename": "figure.pdf", "sha256": "a" * 64, "page_index": 0},
        "figure_region_pt": [0.0, 0.0, 400.0, 300.0],
        "layout_elements": [
            {"id": "img_1", "kind": "image", "source_order": 1, "bbox_pt": [10, 10, 190, 140]},
            {"id": "img_2", "kind": "image", "source_order": 2, "bbox_pt": [210, 10, 390, 140]},
            {"id": "vec_2", "kind": "filled_path", "source_order": 3, "bbox_pt": [220, 20, 380, 140]},
            {"id": "txt_2", "kind": "text_span", "source_order": None, "bbox_pt": [240, 40, 300, 60]},
            {"id": "crossing", "kind": "stroke_path", "source_order": 4, "bbox_pt": [180, 30, 230, 50]},
        ],
        "image_assets": [
            {"id": "img_1", "source_order": 1, "bbox_pt": [10, 10, 190, 140]},
            {"id": "img_2", "source_order": 2, "bbox_pt": [210, 10, 390, 140]},
        ],
        "panel_detection": {
            "unlabeled_panel_candidates": [
                {"id": "p_raster", "candidate_type": "source_enclosure", "bbox_pt": [0, 0, 170, 160], "confidence": "high"},
                {"id": "p_mixed", "candidate_type": "source_enclosure", "bbox_pt": [200, 0, 400, 160], "confidence": "high"},
                {"id": "p_cross", "candidate_type": "source_enclosure", "bbox_pt": [170, 0, 240, 160], "confidence": "medium"},
                {"id": "p_empty", "candidate_type": "source_enclosure", "bbox_pt": [0, 170, 170, 290], "confidence": "medium"},
            ],
            "alignment_groups": [],
            "raster_gutter_candidates": [],
        },
    }


class ReconstructionRouterTests(unittest.TestCase):
    def _files(self, root):
        layout_path = root / "layout.json"
        review_path = root / "review.json"
        layout_path.write_text(json.dumps(make_layout(), indent=2), encoding="utf-8")
        review = create_source_layout_review_template(layout_path, review_path)
        review["reviewer"] = {"name": "reviewer", "type": "human"}
        for item in review["decisions"]:
            item["decision"] = "accept_panel"
            item["rationale"] = "Reviewed source bounds against the paper figure."
            item["evidence_locator"] = "Figure 1, PDF page 1"
        review_path.write_text(json.dumps(review, indent=2), encoding="utf-8")
        return layout_path, review_path

    def test_selects_picture_only_mixed_native_and_manual_boundary_routes(self):
        with tempfile.TemporaryDirectory() as folder:
            layout_path, review_path = self._files(Path(folder))
            result = build_reconstruction_routes(layout_path, review_path)
        routes = {item["reviewed_region_id"]: item["recommended_route"] for item in result["panel_routes"]}
        self.assertEqual(routes["p_raster"], "source_picture_only")
        self.assertEqual(routes["p_mixed"], "mixed_native_picture")
        self.assertEqual(routes["p_cross"], "manual_review_required")
        self.assertEqual(routes["p_empty"], "unsupported_source")
        self.assertFalse(result["policy"]["execution_authorized"])
        self.assertTrue(all(not item["execution_authorized"] for item in result["panel_routes"]))

    def test_native_vector_and_text_only_routes(self):
        layout = make_layout()
        layout["layout_elements"] = [
            {"id": "v", "kind": "stroke_path", "source_order": 1, "bbox_pt": [10, 10, 80, 80]},
            {"id": "t", "kind": "text_span", "source_order": None, "bbox_pt": [100, 10, 180, 30]},
        ]
        layout["image_assets"] = []
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            path=root/"layout.json"
            review_path=root/"review.json"
            path.write_text(json.dumps(layout),encoding="utf-8")
            review=create_source_layout_review_template(path,review_path)
            review["reviewer"]={"name":"reviewer","type":"human"}
            for item in review["decisions"]:
                item["decision"]="accept_panel"
                item["rationale"]="Verified against source."
                item["evidence_locator"]="Figure 1"
            review_path.write_text(json.dumps(review),encoding="utf-8")
            result=build_reconstruction_routes(path,review_path)
        routes={item["reviewed_region_id"]:item["recommended_route"] for item in result["panel_routes"]}
        self.assertEqual(routes["p_raster"],"native_vector")
        self.assertEqual(routes["p_mixed"],"native_text")

    def test_rejects_stale_review_hash_and_removes_stale_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            layout_path,review_path=self._files(root)
            output=root/"routes.json"
            output.write_text("stale")
            layout_path.write_text(json.dumps(make_layout()),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"INVALID_SOURCE_LAYOUT_REVIEW"):
                write_reconstruction_routes(layout_path,review_path,output)
            self.assertFalse(output.exists())

    def test_unreviewed_or_invalid_review_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            layout_path=root/"layout.json"
            review_path=root/"review.json"
            layout_path.write_text(json.dumps(make_layout()),encoding="utf-8")
            create_source_layout_review_template(layout_path,review_path)
            with self.assertRaisesRegex(ValueError,"HUMAN_REVIEWED_SOURCE_FACTS_REQUIRED"):
                build_reconstruction_routes(layout_path,review_path)

    def test_image_assets_are_not_double_counted(self):
        with tempfile.TemporaryDirectory() as folder:
            layout_path,review_path=self._files(Path(folder))
            result=build_reconstruction_routes(layout_path,review_path)
        raster=next(item for item in result["panel_routes"] if item["reviewed_region_id"]=="p_raster")
        self.assertEqual(raster["counts"]["image_assets"],1)
        self.assertEqual(raster["source_object_ids"]["images"],["img_1"])


if __name__ == "__main__":
    unittest.main()
