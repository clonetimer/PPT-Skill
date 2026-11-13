"""Release-state classification must fail closed across both figure routes."""
from __future__ import annotations

import unittest

from reproduction_release_gate import classify_release


class ReproductionReleaseGateTests(unittest.TestCase):
    def test_empty_candidate_is_structure_fail(self):
        result = classify_release(
            route="import",
            candidate={"shape_count": 0, "picture_objects": 0, "native_vectors": 0, "text_objects": 0},
            structure={"status": "FAIL"},
            text_geometry={"status": "FAIL"},
            visual=None,
            office={"status": "PASS"},
        )
        self.assertEqual(result["status"], "STRUCTURE_FAIL")

    def test_full_page_raster_is_unsupported_for_native_editable_route(self):
        result = classify_release(
            route="import",
            candidate={"shape_count": 1, "full_page_pictures": 1, "native_vectors": 0, "text_objects": 0},
            structure={"status": "FAIL"},
            text_geometry={"status": "PASS"},
            visual={"requires_visual_review": False},
            office={"status": "PASS"},
            require_native=True,
        )
        self.assertEqual(result["status"], "UNSUPPORTED_SOURCE")

    def test_source_picture_only_recovery_is_not_misreported_as_native_pass(self):
        result = classify_release(
            route="import",
            candidate={"shape_count": 1, "full_page_pictures": 0, "picture_objects": 1,
                        "native_vectors": 0, "text_objects": 0},
            import_report={"reconstruction_class": "source_picture_only"},
            structure={"status": "PASS"},
            text_geometry={"status": "PASS"},
            visual={"requires_visual_review": False},
            office={"status": "PASS"},
            require_native=True,
        )
        self.assertEqual(result["status"], "UNSUPPORTED_SOURCE")

    def test_dense_source_budget_has_its_own_status(self):
        result = classify_release(
            route="import",
            error="RESOURCE_LIMIT: source_segments 127713 > 100000",
        )
        self.assertEqual(result["status"], "RESOURCE_LIMIT")

    def test_missing_render_export_requires_visual_review(self):
        result = classify_release(
            route="import",
            candidate={"shape_count": 80, "native_vectors": 60, "text_objects": 20, "full_page_pictures": 0},
            structure={"status": "PASS"},
            text_geometry={"status": "PASS"},
            visual=None,
            office={"status": "PASS"},
        )
        self.assertEqual(result["status"], "NEEDS_VISUAL_REVIEW")

    def test_high_visual_similarity_does_not_approve_wrong_or_unverified_figurespec_edges(self):
        result = classify_release(
            route="figurespec",
            candidate={"shape_count": 50, "native_vectors": 40, "text_objects": 10, "full_page_pictures": 0},
            structure={"status": "PASS"},
            text_geometry=None,
            visual={"requires_visual_review": False, "global_similarity": 0.99},
            office={"status": "PASS"},
            semantic_audit={"status": "FAIL", "missing_edges": ["encoder_to_fusion"]},
        )
        self.assertEqual(result["status"], "NEEDS_SCIENTIFIC_REVIEW")
        self.assertIn("SEMANTIC_RELATION_FAILURE", result["blockers"])

    def test_technical_pass_is_not_full_acceptance_without_human_and_host_evidence(self):
        result = classify_release(
            route="import",
            candidate={"shape_count": 50, "native_vectors": 40, "text_objects": 10, "full_page_pictures": 0},
            structure={"status": "PASS"},
            text_geometry={"status": "PASS"},
            visual={"requires_visual_review": False},
            office={"status": "PASS"},
            semantic_audit={"status": "PASS"},
        )
        self.assertEqual(result["status"], "TECHNICAL_PASS")
        self.assertFalse(result["full_accepted"])

    def test_full_acceptance_requires_all_explicit_approvals(self):
        result = classify_release(
            route="figurespec",
            candidate={"shape_count": 50, "native_vectors": 40, "text_objects": 10, "full_page_pictures": 0},
            structure={"status": "PASS"},
            visual={"requires_visual_review": False},
            office={"status": "PASS"},
            semantic_audit={"status": "PASS"},
            approvals={
                "scientific_review": "approved",
                "visual_review": "approved",
                "rights_review": "cleared",
                "office_host": {"target": "PowerPoint 2016", "status": "verified"},
            },
        )
        self.assertEqual(result["status"], "FULL_ACCEPTED")
        self.assertTrue(result["full_accepted"])

    def test_office_host_requirement_can_be_explicitly_disabled(self):
        result = classify_release(
            route="figurespec",
            candidate={"shape_count": 50, "native_vectors": 40, "text_objects": 10, "full_page_pictures": 0},
            structure={"status": "PASS"},
            visual={"requires_visual_review": False},
            office={"status": "PASS"},
            semantic_audit={"status": "PASS"},
            approvals={
                "scientific_review": "approved",
                "visual_review": "approved",
                "rights_review": "cleared",
            },
            require_office_host=False,
        )
        self.assertEqual(result["status"], "FULL_ACCEPTED")

    def test_route_must_be_explicit(self):
        with self.assertRaises(ValueError):
            classify_release(route="guess", candidate={"shape_count": 1})


if __name__ == "__main__":
    unittest.main()
