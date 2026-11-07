#!/usr/bin/env python3
"""Exercise the release gate using in-memory synthetic review data only."""
from __future__ import annotations

import unittest

from validate_release_readiness import prepare_template, validate_review


class ReleaseGateTests(unittest.TestCase):
    def complete_synthetic_review(self):
        review = prepare_template()
        disciplines = {result["required_discipline"] for result in review["tasks"].values()}
        review["reviewers"] = {discipline: {
            "name": "SYNTHETIC TEST", "date": "2000-01-01", "disciplines": [discipline],
            "independent_of_build": True, "blind_to_implementation_version": True,
        } for discipline in disciplines}
        for result in review["tasks"].values():
            result["reviewer_id"] = result["required_discipline"]
            result["source_checked"] = result["scientific_relationships_checked"] = True
            result["final_size"] = {"checked": True, "context": "synthetic", "evidence": "test only"}
            for item in result["scores"].values():
                item.update(score=4, evidence="synthetic test only")
            result["hard_fail"] = {key: False for key in result["hard_fail"]}
            result["conclusion"] = "pass"
        return review

    def test_unfilled_template_fails(self):
        with self.assertRaises(ValueError):
            validate_review(prepare_template())

    def test_complete_synthetic_data_exercises_gate(self):
        validate_review(self.complete_synthetic_review())

    def test_hard_failure_blocks_release(self):
        review = self.complete_synthetic_review()
        review["tasks"]["Q03"]["hard_fail"]["wrong_critical_relation_or_formula_or_value"] = True
        with self.assertRaises(ValueError):
            validate_review(review)

    def test_changed_output_blocks_stale_review(self):
        review = self.complete_synthetic_review()
        review["tasks"]["Q03P"]["output_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            validate_review(review)

    def test_missing_final_size_blocks_release(self):
        review = self.complete_synthetic_review()
        review["tasks"]["I01"]["final_size"]["checked"] = False
        with self.assertRaises(ValueError):
            validate_review(review)

    def test_wrong_domain_reviewer_blocks_release(self):
        review = self.complete_synthetic_review()
        review["tasks"]["I01"]["reviewer_id"] = "applied_statistics"
        with self.assertRaises(ValueError):
            validate_review(review)


if __name__ == "__main__":
    unittest.main()
