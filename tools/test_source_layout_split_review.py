"""Fail-closed manual panel-region splits with source-layout provenance.

A split is a *human reviewed geometric subdivision*, never an inferred
scientific panel or topology edge.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import tempfile
import unittest

from source_layout_review import create_source_layout_review_template, validate_source_layout_review
from test_source_layout_review import make_layout, write_layout


def _review(root, *, candidate="rect_candidate_01", axis="horizontal", location=95,
            reviewer_type="human", choice="split_region"):
    layout = write_layout(root)
    review_path = root / "review.json"
    review = create_source_layout_review_template(layout, review_path)
    review["reviewer"] = {"name": "domain expert", "type": reviewer_type}
    target = next(x for x in review["decisions"] if x["candidate_id"] == candidate)
    target["decision"] = choice
    target["rationale"] = "The source figure contains two distinguishable geometric regions."
    target["evidence_locator"] = "Figure 4, source PDF page 3"
    target["split_axis"] = axis
    target["split_position_pt"] = location
    review_path.write_text(json.dumps(review, ensure_ascii=False), encoding="utf-8")
    return layout, review_path


class SourceLayoutSplitReviewTests(unittest.TestCase):
    def test_human_horizontal_split_produces_two_source_regions_without_scientific_panels(self):
        with tempfile.TemporaryDirectory() as temp:
            layout, review = _review(Path(temp))
            result = validate_source_layout_review(layout, review)
            self.assertEqual(result["status"], "VALIDATED_WITH_ACCEPTED_FACTS")
            self.assertEqual(result["accepted_region_count"], 2)
            self.assertEqual(result["accepted_panel_count"], 0)
            self.assertEqual(result["split_region_count"], 1)
            children = result["accepted_source_layout_regions"]
            self.assertEqual([x["candidate_id"] for x in children],
                             ["rect_candidate_01__part1", "rect_candidate_01__part2"])
            self.assertEqual([x["bbox_pt"] for x in children],
                             [[30.0, 40.0, 390.0, 95.0], [30.0, 95.0, 390.0, 150.0]])
            self.assertTrue(all(x["derived_from_candidate"] == "rect_candidate_01" for x in children))
            self.assertTrue(all(x["reviewer"]["type"] == "human" for x in children))
            self.assertTrue(all(x["semantic_role"] == "geometric_region_only" for x in children))

    def test_vertical_split_preserves_entire_original_bbox_without_overlap_or_gap(self):
        with tempfile.TemporaryDirectory() as temp:
            layout, review = _review(Path(temp), axis="vertical", location=200)
            result = validate_source_layout_review(layout, review)
            self.assertEqual(result["status"], "VALIDATED_WITH_ACCEPTED_FACTS")
            self.assertEqual([x["bbox_pt"] for x in result["accepted_source_layout_regions"]],
                             [[30.0, 40.0, 200.0, 150.0], [200.0, 40.0, 390.0, 150.0]])

    def test_raster_gutter_and_alignment_group_cannot_be_split(self):
        for candidate in ("raster_gutter_01_horizontal_01", "alignment_vertical_stack_01"):
            with self.subTest(candidate=candidate), tempfile.TemporaryDirectory() as temp:
                layout, review = _review(Path(temp), candidate=candidate)
                result = validate_source_layout_review(layout, review)
                self.assertEqual(result["status"], "INVALID")
                self.assertTrue(any("CANDIDATE_CANNOT_BE_SPLIT" in e for e in result["errors"]))
                self.assertEqual(result["accepted_region_count"], 0)

    def test_split_near_boundary_and_non_finite_coordinates_are_rejected(self):
        for location in (-1, 40, 42, 149, 151, "invalid", float("nan"), float("inf"), True):
            with self.subTest(location=str(location)), tempfile.TemporaryDirectory() as temp:
                layout, review = _review(Path(temp), location=location)
                result = validate_source_layout_review(layout, review)
                self.assertEqual(result["status"], "INVALID")
                self.assertEqual(result["accepted_region_count"], 0)
                self.assertIn("INVALID_SPLIT_GEOMETRY:rect_candidate_01", result["errors"])

    def test_assistant_triage_cannot_approve_split(self):
        with tempfile.TemporaryDirectory() as temp:
            layout, review = _review(Path(temp), reviewer_type="assistant_visual_triage")
            result = validate_source_layout_review(layout, review)
            self.assertEqual(result["status"], "INVALID")
            self.assertEqual(result["accepted_region_count"], 0)
            self.assertTrue(any("ASSISTANT_CANNOT_APPROVE_OR_REJECT" in e for e in result["errors"]))

    def test_atomic_validation_does_not_release_other_acceptances_when_split_is_invalid(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            layout, review_path = _review(root, location=40)
            payload = json.loads(review_path.read_text(encoding="utf-8"))
            second = next(x for x in payload["decisions"] if x["candidate_id"] == "interstitial_01")
            second["decision"] = "accept_region"
            second["rationale"] = "Source visibly supports a local region."
            second["evidence_locator"] = "Figure 4, page 3"
            review_path.write_text(json.dumps(payload), encoding="utf-8")
            result = validate_source_layout_review(layout, review_path)
            self.assertEqual(result["status"], "INVALID")
            self.assertEqual(result["accepted_region_count"], 0)
            self.assertEqual(result["accepted_source_layout_regions"], [])
            self.assertEqual(result["accepted_source_panels"], [])

    def test_review_schema_accepts_split_fields_but_keeps_them_optional_for_old_templates(self):
        import jsonschema
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            layout, review_path = _review(root)
            schema_path = Path(__file__).resolve().parents[1] / "specs/source_layout_review.schema.json"
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            jsonschema.Draft202012Validator.check_schema(schema)
            jsonschema.validate(json.loads(review_path.read_text(encoding="utf-8")), schema)


if __name__ == "__main__":
    unittest.main()
