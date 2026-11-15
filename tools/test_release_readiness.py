import json
import tempfile
import unittest
from pathlib import Path

from validate_release_readiness import prepare_template, validate_review

DIMENSIONS = (
    "scientific_accuracy",
    "data_image_integrity",
    "readability",
    "accessibility",
    "editability_reproducibility",
    "visual_quality",
)
HARD_FAILS = (
    "wrong_critical_relation_or_formula_or_value",
    "unclear_source_status",
    "undisclosed_image_processing",
    "unreadable_or_occluded_important_content",
)
DISCIPLINES = (
    "aerospace_systems",
    "machinery_fault_diagnosis",
    "applied_statistics",
    "analytical_chemistry",
    "cell_imaging",
)


def complete_synthetic_review():
    review = prepare_template()
    review["reviewers"] = {
        "R1": {
            "human": True,
            "name": "Independent human domain reviewer",
            "date": "2026-11-14",
            "disciplines": list(DISCIPLINES),
            "independent_of_build": True,
            "scored_before_reading_benchmark_expectations": True,
        }
    }
    for task in review["tasks"].values():
        task.update({
            "reviewer_id": "R1",
            "repair_rounds": 2,
            "source_checked": True,
            "scientific_relationships_checked": True,
            "initial_review_before_expectations": {
                "completed": True,
                "score": 3,
                "evidence": "Initial blind review completed before reading benchmark expectations.",
            },
            "final_size": {
                "checked": True,
                "context": "projected at the intended presentation size",
                "evidence": "Critical labels, marks and connectors remain legible at full slide size.",
            },
            "scores": {
                dimension: {
                    "score": 3,
                    "evidence": f"{dimension} checked against source, editable PPTX and rendered output.",
                }
                for dimension in DIMENSIONS
            },
            "hard_fail": {flag: False for flag in HARD_FAILS},
            "conclusion": "pass",
        })
    return review


class ReleaseReadinessTests(unittest.TestCase):
    def validate_temp(self, review):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        path = Path(folder.name) / "review.json"
        path.write_text(json.dumps(review, ensure_ascii=False), encoding="utf-8")
        return validate_review(path)

    def test_blank_template_is_not_release_ready(self):
        with self.assertRaises(ValueError):
            self.validate_temp(prepare_template())

    def test_complete_independent_human_review_passes(self):
        self.validate_temp(complete_synthetic_review())

    def test_ai_reviewer_cannot_satisfy_human_final_review_gate(self):
        review = complete_synthetic_review()
        review["reviewers"]["R1"]["human"] = False
        with self.assertRaisesRegex(ValueError, "explicitly identified as human"):
            self.validate_temp(review)

    def test_non_independent_reviewer_is_rejected(self):
        review = complete_synthetic_review()
        review["reviewers"]["R1"]["independent_of_build"] = False
        with self.assertRaises(ValueError):
            self.validate_temp(review)

    def test_review_must_precede_benchmark_expectations(self):
        review = complete_synthetic_review()
        review["reviewers"]["R1"]["scored_before_reading_benchmark_expectations"] = False
        with self.assertRaises(ValueError):
            self.validate_temp(review)

    def test_missing_final_size_evidence_is_rejected(self):
        review = complete_synthetic_review()
        next(iter(review["tasks"].values()))["final_size"]["evidence"] = ""
        with self.assertRaises(ValueError):
            self.validate_temp(review)

    def test_negative_repair_round_count_is_rejected(self):
        review = complete_synthetic_review()
        next(iter(review["tasks"].values()))["repair_rounds"] = -1
        with self.assertRaises(ValueError):
            self.validate_temp(review)


if __name__ == "__main__":
    unittest.main()
