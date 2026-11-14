"""Human approval and source-route recommendation tests for SourceLayout."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from source_layout_review import (
    create_source_layout_review_template,
    recommend_source_route,
    validate_source_layout_review,
)


def make_layout():
    return {
        "schema_version": "1.0.0",
        "source": {
            "filename": "source.pdf",
            "sha256": "a" * 64,
            "page_index": 2,
        },
        "figure_region_pt": [10.0, 20.0, 410.0, 320.0],
        "layout_elements": [
            {"id": "draw_1", "kind": "stroke_path"},
            {"id": "image_1", "kind": "image"},
        ],
        "image_assets": [{"id": "image_1", "sha256": "b" * 64}],
        "panel_detection": {
            "unlabeled_panel_candidates": [
                {
                    "id": "rect_candidate_01",
                    "candidate_type": "source_enclosure",
                    "bbox_pt": [30.0, 40.0, 390.0, 150.0],
                    "confidence": "medium",
                },
                {
                    "id": "interstitial_01",
                    "candidate_type": "interstitial_band",
                    "bbox_pt": [30.0, 150.0, 390.0, 180.0],
                    "confidence": "low",
                },
            ],
            "alignment_groups": [
                {
                    "id": "alignment_vertical_stack_01",
                    "axis": "vertical_stack",
                    "member_candidate_ids": ["rect_candidate_01", "interstitial_01"],
                    "confidence": "medium",
                }
            ],
            "raster_gutter_candidates": [
                {
                    "id": "raster_gutter_01_horizontal_01",
                    "source_image_id": "image_1",
                    "axis": "horizontal",
                    "start_pt": 200.0,
                    "end_pt": 205.0,
                    "width_pt": 5.0,
                    "confidence": "low",
                }
            ],
        },
    }


def write_layout(root: Path):
    path = root / "source_layout.json"
    path.write_text(json.dumps(make_layout(), indent=2), encoding="utf-8")
    return path


class SourceLayoutReviewTests(unittest.TestCase):
    def test_template_contains_every_candidate_and_accepts_none_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            layout_path = write_layout(root)
            review_path = root / "review.json"
            review = create_source_layout_review_template(layout_path, review_path)
            self.assertEqual(len(review["decisions"]), 4)
            self.assertTrue(all(item["decision"] == "pending" for item in review["decisions"]))
            audit = validate_source_layout_review(layout_path, review_path)
            self.assertEqual(audit["status"], "REVIEW_PENDING")
            self.assertEqual(audit["accepted_panel_count"], 0)
            self.assertEqual(audit["pending_count"], 4)

    def test_human_can_accept_a_source_enclosure_as_a_panel_with_locator(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            layout_path = write_layout(root)
            review_path = root / "review.json"
            review = create_source_layout_review_template(layout_path, review_path)
            review["reviewer"] = {"name": "domain reviewer", "type": "human"}
            item = next(x for x in review["decisions"] if x["candidate_id"] == "rect_candidate_01")
            item["decision"] = "accept_panel"
            item["rationale"] = "The enclosure matches the source paper's labeled panel."
            item["evidence_locator"] = "Figure 4(a), source PDF page 3"
            review_path.write_text(json.dumps(review), encoding="utf-8")
            audit = validate_source_layout_review(layout_path, review_path)
            self.assertEqual(audit["status"], "VALIDATED_WITH_ACCEPTED_FACTS")
            self.assertEqual(audit["accepted_panel_count"], 1)
            self.assertEqual(audit["accepted_source_panels"][0]["candidate_id"], "rect_candidate_01")

    def test_assistant_visual_triage_cannot_accept_a_panel(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            layout_path = write_layout(root)
            review_path = root / "review.json"
            review = create_source_layout_review_template(layout_path, review_path)
            review["reviewer"] = {"name": "assistant triage", "type": "assistant_visual_triage"}
            item = next(x for x in review["decisions"] if x["candidate_id"] == "rect_candidate_01")
            item["decision"] = "accept_panel"
            item["rationale"] = "Looks like a panel."
            item["evidence_locator"] = "visual inspection"
            review_path.write_text(json.dumps(review), encoding="utf-8")
            audit = validate_source_layout_review(layout_path, review_path)
            self.assertEqual(audit["status"], "INVALID")
            self.assertTrue(any("ASSISTANT_CANNOT_APPROVE_OR_REJECT" in e for e in audit["errors"]))

    def test_raster_gutter_cannot_be_promoted_to_scientific_panel(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            layout_path = write_layout(root)
            review_path = root / "review.json"
            review = create_source_layout_review_template(layout_path, review_path)
            review["reviewer"] = {"name": "domain reviewer", "type": "human"}
            item = next(x for x in review["decisions"] if x["candidate_id"].startswith("raster_gutter"))
            item["decision"] = "accept_panel"
            item["rationale"] = "The whitespace seems to separate two streams."
            item["evidence_locator"] = "Figure 2, source PDF page 3"
            review_path.write_text(json.dumps(review), encoding="utf-8")
            audit = validate_source_layout_review(layout_path, review_path)
            self.assertEqual(audit["status"], "INVALID")
            self.assertTrue(any("CANDIDATE_CANNOT_BE_PROMOTED_TO_PANEL" in e for e in audit["errors"]))

    def test_source_layout_hash_mismatch_invalidates_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            layout_path = write_layout(root)
            review_path = root / "review.json"
            create_source_layout_review_template(layout_path, review_path)
            layout_path.write_text(json.dumps(make_layout() | {"figure_region_pt": [11, 20, 410, 320]}), encoding="utf-8")
            audit = validate_source_layout_review(layout_path, review_path)
            self.assertEqual(audit["status"], "INVALID")
            self.assertIn("SOURCE_LAYOUT_HASH_MISMATCH", audit["errors"])

    def test_missing_candidate_decision_is_incomplete_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            layout_path = write_layout(root)
            review_path = root / "review.json"
            review = create_source_layout_review_template(layout_path, review_path)
            review["decisions"].pop()
            review_path.write_text(json.dumps(review), encoding="utf-8")
            audit = validate_source_layout_review(layout_path, review_path)
            self.assertEqual(audit["status"], "INVALID")
            self.assertIn("REVIEW_COVERAGE_INCOMPLETE", audit["errors"])

    def test_source_route_recommendation_distinguishes_mixed_image_and_vector_inputs(self):
        mixed = recommend_source_route(make_layout())
        self.assertEqual(mixed["recommended_reconstruction_class"], "mixed_native_picture")
        image_only = make_layout() | {
            "image_assets": [{"id": "image_1"}],
            "layout_elements": [{"id": "image_1", "kind": "image"}],
        }
        self.assertEqual(recommend_source_route(image_only)["recommended_reconstruction_class"], "source_picture_only")
        vector_only = make_layout() | {
            "image_assets": [],
            "layout_elements": [{"id": "draw_1", "kind": "stroke_path"}],
        }
        self.assertEqual(recommend_source_route(vector_only)["recommended_reconstruction_class"], "native_only")


if __name__ == "__main__":
    unittest.main()
