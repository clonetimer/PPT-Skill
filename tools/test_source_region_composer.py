"""Tests for P1-01D source-region composition manifests."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from source_layout_review import create_source_layout_review_template
from source_reconstruction_router import build_reconstruction_routes
from source_region_composer import build_source_composition_manifest, write_source_composition_manifest


def make_layout():
    return {
        "schema_version": "1.1.0",
        "source": {"filename": "figure.pdf", "sha256": "a" * 64, "page_index": 0},
        "figure_region_pt": [0.0, 0.0, 400.0, 300.0],
        "layout_elements": [
            {"id": "image_a", "kind": "image", "source_order": 1, "bbox_pt": [10, 10, 160, 140]},
            {"id": "image_b", "kind": "image", "source_order": 2, "bbox_pt": [210, 10, 390, 140]},
            {"id": "vector_b", "kind": "filled_path", "source_order": 3, "bbox_pt": [220, 20, 380, 130]},
            {"id": "text_b", "kind": "text_span", "source_order": None, "bbox_pt": [240, 40, 300, 60], "text": "Panel B"},
            {"id": "shared", "kind": "stroke_path", "source_order": 4, "bbox_pt": [150, 40, 220, 50]},
        ],
        "image_assets": [
            {"id": "image_a", "source_order": 1, "bbox_pt": [10, 10, 160, 140]},
            {"id": "image_b", "source_order": 2, "bbox_pt": [210, 10, 390, 140]},
        ],
        "panel_detection": {
            "unlabeled_panel_candidates": [
                {"id": "panel_a", "candidate_type": "source_enclosure", "bbox_pt": [0, 0, 170, 160], "confidence": "high"},
                {"id": "panel_b", "candidate_type": "source_enclosure", "bbox_pt": [200, 0, 400, 160], "confidence": "high"},
            ],
            "alignment_groups": [],
            "raster_gutter_candidates": [],
        },
    }


class SourceRegionComposerTests(unittest.TestCase):
    def _files(self, root: Path):
        layout_path = root / "layout.json"
        review_path = root / "review.json"
        routes_path = root / "routes.json"
        layout_path.write_text(json.dumps(make_layout(), indent=2), encoding="utf-8")
        review = create_source_layout_review_template(layout_path, review_path)
        review["reviewer"] = {"name": "reviewer", "type": "human"}
        for item in review["decisions"]:
            item.update({
                "decision": "accept_panel",
                "rationale": "Panel boundary checked against the source PDF.",
                "evidence_locator": "Figure 1, page 1",
            })
        review_path.write_text(json.dumps(review, indent=2), encoding="utf-8")
        routes = build_reconstruction_routes(layout_path, review_path)
        routes_path.write_text(json.dumps(routes, indent=2), encoding="utf-8")
        return layout_path, review_path, routes_path

    def test_mixed_route_keeps_picture_vector_and_text_separate(self):
        with tempfile.TemporaryDirectory() as folder:
            paths = self._files(Path(folder))
            result = build_source_composition_manifest(*paths)
        panel_b = next(x for x in result["composition_units"] if x["unit_id"] == "panel_b")
        treatments = {x["source_object_id"]: x["treatment"] for x in panel_b["objects"]}
        self.assertEqual(treatments["image_b"], "picture_asset")
        self.assertEqual(treatments["vector_b"], "editable_vector")
        self.assertEqual(treatments["text_b"], "editable_text")
        self.assertFalse(result["policy"]["mixed_content_flattening_allowed"])

    def test_shared_boundary_object_is_listed_once_and_blocks_execution(self):
        with tempfile.TemporaryDirectory() as folder:
            paths = self._files(Path(folder))
            result = build_source_composition_manifest(*paths)
        shared = next(x for x in result["shared_boundary_objects"] if x["source_object_id"] == "shared")
        self.assertFalse(shared["duplicated"])
        self.assertIn("OBJECT_REFERENCED_BY_MULTIPLE_REVIEWED_UNITS:shared", result["blockers"])
        self.assertEqual(result["status"], "BLOCKED")

    def test_source_order_is_deterministic_and_text_without_paint_order_is_secondary(self):
        with tempfile.TemporaryDirectory() as folder:
            paths = self._files(Path(folder))
            result = build_source_composition_manifest(*paths)
        sequence = result["source_order_sequence"]
        orders = [x["source_order"] for x in sequence if x["source_order"] is not None]
        self.assertEqual(orders, sorted(orders))
        text_item = next(x for x in sequence if x["source_object_id"] == "text_b")
        self.assertIsNone(text_item["source_order"])
        self.assertFalse(text_item["paint_order_available"])

    def test_stale_route_hash_fails_and_removes_existing_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            layout_path, review_path, routes_path = self._files(root)
            routes = json.loads(routes_path.read_text(encoding="utf-8"))
            routes["source_layout_sha256"] = "0" * 64
            routes_path.write_text(json.dumps(routes), encoding="utf-8")
            output = root / "composition.json"
            output.write_text("stale", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "ROUTE_SOURCE_LAYOUT_HASH_MISMATCH"):
                write_source_composition_manifest(layout_path, review_path, routes_path, output)
            self.assertFalse(output.exists())

    def test_duplicate_source_object_conflict_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            layout = make_layout()
            layout["layout_elements"].append({
                "id": "image_a", "kind": "stroke_path", "source_order": 9,
                "bbox_pt": [1, 1, 2, 2],
            })
            layout_path = root / "layout.json"
            layout_path.write_text(json.dumps(layout), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "DUPLICATE_SOURCE_OBJECT_ID_CONFLICT"):
                from source_region_composer import _source_inventory
                _source_inventory(layout)


if __name__ == "__main__":
    unittest.main()
