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


class StrictRouteEvidenceTests(unittest.TestCase):
    def _import_evidence(self, *, reconstruction_class="native_only", pictures=0, vectors=12):
        return dict(
            route="import",
            candidate={"shape_count": vectors + pictures + 4, "native_vectors": vectors,
                       "text_objects": 4, "picture_objects": pictures, "full_page_pictures": 0},
            import_report={"reconstruction_class": reconstruction_class,
                           "unresolved_visible_events": 0},
            structure={"status": "PASS"},
            text_geometry={"status": "PASS"},
            visual={"status": "PASS", "requires_visual_review": False,
                    "evidence_type": "source_comparison", "renderer": "LibreOffice"},
            office={"status": "PASS"},
        )

    def test_import_without_reconstruction_class_is_unsupported(self):
        args = self._import_evidence()
        args["import_report"] = {}
        result = classify_release(**args)
        self.assertEqual(result["status"], "UNSUPPORTED_SOURCE")
        self.assertIn("RECONSTRUCTION_CLASS_MISSING", result["blockers"])

    def test_picture_only_has_explicit_status_when_non_native_output_allowed(self):
        args = self._import_evidence(reconstruction_class="source_picture_only", pictures=1, vectors=0)
        result = classify_release(**args, require_native=False)
        self.assertEqual(result["status"], "SOURCE_PICTURE_ONLY")
        self.assertFalse(result["full_accepted"])

    def test_mixed_native_and_local_picture_is_explicitly_preserved(self):
        args = self._import_evidence(reconstruction_class="mixed_native_picture", pictures=2, vectors=10)
        result = classify_release(**args)
        self.assertEqual(result["status"], "TECHNICAL_PASS")
        self.assertEqual(result["reconstruction_class"], "mixed_native_picture")

    def test_mixed_class_without_native_vectors_fails(self):
        args = self._import_evidence(reconstruction_class="mixed_native_picture", pictures=2, vectors=0)
        result = classify_release(**args)
        self.assertEqual(result["status"], "STRUCTURE_FAIL")

    def test_missing_text_geometry_fails_closed(self):
        args = self._import_evidence()
        args["text_geometry"] = None
        result = classify_release(**args)
        self.assertEqual(result["status"], "STRUCTURE_FAIL")
        self.assertIn("TEXT_GEOMETRY_AUDIT_MISSING", result["blockers"])

    def test_visual_evidence_must_match_source_import_route(self):
        args = self._import_evidence()
        args["visual"] = {"status": "PASS", "requires_visual_review": False,
                          "evidence_type": "candidate_render", "renderer": "LibreOffice"}
        result = classify_release(**args)
        self.assertEqual(result["status"], "NEEDS_VISUAL_REVIEW")

    def test_source_math_risk_cannot_become_technical_pass(self):
        args = self._import_evidence()
        result = classify_release(**args, source_risks=[{"code": "SUSPICIOUS_UNICODE", "severity": "high"}])
        self.assertEqual(result["status"], "NEEDS_SCIENTIFIC_REVIEW")

    def test_figurespec_requires_static_semantic_audit_and_candidate_render(self):
        result = classify_release(
            route="figurespec",
            candidate={"shape_count": 30, "native_vectors": 20, "text_objects": 10,
                       "picture_objects": 0, "full_page_pictures": 0},
            structure={"status": "PASS"},
            text_geometry={"status": "PASS"},
            office={"status": "PASS"},
            visual={"status": "PASS", "requires_visual_review": False,
                    "evidence_type": "candidate_render", "renderer": "LibreOffice"},
            semantic_audit={"status": "NEEDS_REVIEW", "blockers": ["SEMANTIC_RELATION_AUDIT_MISSING"]},
        )
        self.assertEqual(result["status"], "NEEDS_SCIENTIFIC_REVIEW")

    def test_figurespec_cannot_use_source_comparison_as_its_render_evidence(self):
        result = classify_release(
            route="figurespec",
            candidate={"shape_count": 30, "native_vectors": 20, "text_objects": 10,
                       "picture_objects": 0, "full_page_pictures": 0},
            structure={"status": "PASS"},
            text_geometry={"status": "PASS"},
            office={"status": "PASS"},
            visual={"status": "PASS", "requires_visual_review": False,
                    "evidence_type": "source_comparison", "renderer": "LibreOffice"},
            semantic_audit={"status": "PASS"},
        )
        self.assertEqual(result["status"], "NEEDS_VISUAL_REVIEW")

    def test_empty_and_unknown_import_route_classifications_fail_closed(self):
        for value in ("", "mystery", None):
            args = self._import_evidence()
            args["import_report"] = {"reconstruction_class": value}
            with self.subTest(value=value):
                result = classify_release(**args)
                self.assertEqual(result["status"], "UNSUPPORTED_SOURCE")




if __name__ == "__main__":
    unittest.main()
