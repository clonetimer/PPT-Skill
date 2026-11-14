import json
import tempfile
import unittest
from pathlib import Path

from final_delivery_success import (
    calculate,
    DIMENSIONS,
    HARD_FAILS,
    REVIEW_DIMENSIONS,
    REVIEW_HARD_FAILS,
)


def baseline(path):
    path.write_text(json.dumps({
        "dataset_id": "frozen",
        "first_pass_generated": 2,
        "mean_score_24": 18.2,
        "rows": [
            {"figure_id": "a", "first_pass": {"strict_pass": False}},
            {"figure_id": "b", "first_pass": {"strict_pass": False}},
        ],
    }), encoding="utf-8")


def compact_good_task():
    return {
        "task_id": "X",
        "final_review_status": "completed",
        "final_decision": "PASS",
        "reviewer_id": "R1",
        "required_disciplines": ["control"],
        "initial_review_before_expectations": True,
        "repair_rounds": 2,
        "dimension_scores": {d: 3 for d in DIMENSIONS},
        "dimension_evidence": {d: "checked against source and rendered output" for d in DIMENSIONS},
        "hard_failures": {h: False for h in HARD_FAILS},
    }


def release_good_task():
    return {
        "required_discipline": "control",
        "reviewer_id": "R1",
        "repair_rounds": 2,
        "source_checked": True,
        "scientific_relationships_checked": True,
        "initial_review_before_expectations": {
            "completed": True,
            "score": 3,
            "evidence": "Initial blind review completed before benchmark expectations were read.",
        },
        "final_size": {
            "checked": True,
            "context": "projected at the intended presentation size",
            "evidence": "Critical labels and connectors remain legible.",
        },
        "scores": {
            d: {"score": 3, "evidence": f"{d} checked against source and rendered output."}
            for d in REVIEW_DIMENSIONS
        },
        "hard_fail": {h: False for h in REVIEW_HARD_FAILS},
        "conclusion": "pass",
        "source_sha256": "source-hash",
        "input_sha256": "input-hash",
        "related_inputs_sha256": {},
        "artifacts_sha256": {},
    }


def release_ledger(task=None, human=True):
    return {
        "reviewers": {
            "R1": {
                "human": human,
                "name": "Independent human domain reviewer",
                "date": "2026-11-14",
                "disciplines": ["control"],
                "independent_of_build": True,
                "scored_before_reading_benchmark_expectations": True,
            }
        },
        "tasks": {"X": task or release_good_task()},
    }


class FinalDeliverySuccessTests(unittest.TestCase):
    def calc(self, tasks, independent=True, human=True):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        baseline_path = root / "baseline.json"
        ledger_path = root / "ledger.json"
        baseline(baseline_path)
        ledger_path.write_text(json.dumps({
            "reviewers": [{"reviewer_id": "R1", "human": human, "independent": independent, "discipline": "control"}],
            "tasks": tasks,
        }), encoding="utf-8")
        return calculate(baseline_path, ledger_path)

    def calc_release(self, ledger):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        baseline_path = root / "baseline.json"
        ledger_path = root / "review.json"
        baseline(baseline_path)
        ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
        return calculate(baseline_path, ledger_path)

    def test_valid_compact_final_pass_after_repair_preserves_first_pass(self):
        result = self.calc([compact_good_task()])
        self.assertEqual(result["first_pass"]["rate"], 0)
        self.assertEqual(result["final_delivery"]["accepted_after_repair"], 1)
        self.assertEqual(result["final_delivery"]["rate_among_completed"], 1)

    def test_compact_ai_reviewer_does_not_count_as_human_acceptance(self):
        result = self.calc([compact_good_task()], human=False)
        self.assertEqual(result["final_delivery"]["accepted"], 0)
        reasons = result["final_delivery"]["invalid_completed_reviews"][0]["reasons"]
        self.assertIn("REVIEWER_NOT_HUMAN", reasons)

    def test_compact_not_independent_reviewer_does_not_count(self):
        result = self.calc([compact_good_task()], independent=False)
        self.assertEqual(result["final_delivery"]["accepted"], 0)

    def test_compact_pending_reviews_are_not_zero_rate(self):
        task = compact_good_task()
        task["final_review_status"] = "pending"
        result = self.calc([task])
        self.assertIsNone(result["final_delivery"]["rate_among_completed"])
        self.assertEqual(result["final_delivery"]["status"], "NOT_YET_MEASURABLE")

    def test_actual_v76_human_pass_after_repair_is_counted(self):
        result = self.calc_release(release_ledger())
        self.assertEqual(result["first_pass"]["rate"], 0)
        self.assertEqual(result["final_delivery"]["accepted"], 1)
        self.assertEqual(result["final_delivery"]["accepted_after_repair"], 1)
        self.assertEqual(result["final_delivery"]["rate_among_completed"], 1)
        self.assertEqual(result["ledger_schema"], "v7.6_release_readiness_review")

    def test_actual_v76_ai_reviewer_is_invalid(self):
        result = self.calc_release(release_ledger(human=False))
        self.assertEqual(result["final_delivery"]["accepted"], 0)
        self.assertEqual(result["final_delivery"]["completed_valid_reviews"], 0)
        reasons = result["final_delivery"]["invalid_completed_reviews"][0]["reasons"]
        self.assertIn("REVIEWER_NOT_HUMAN", reasons)

    def test_actual_v76_completed_fail_is_in_denominator_only(self):
        task = release_good_task()
        task["conclusion"] = "fail"
        result = self.calc_release(release_ledger(task))
        self.assertEqual(result["final_delivery"]["completed_valid_reviews"], 1)
        self.assertEqual(result["final_delivery"]["accepted"], 0)
        self.assertEqual(result["final_delivery"]["rate_among_completed"], 0)

    def test_actual_v76_pending_is_not_a_zero_success_rate(self):
        task = release_good_task()
        task["conclusion"] = "pending"
        result = self.calc_release(release_ledger(task))
        self.assertEqual(result["final_delivery"]["status"], "NOT_YET_MEASURABLE")
        self.assertIsNone(result["final_delivery"]["rate_among_completed"])
        self.assertEqual(result["final_delivery"]["pending_tasks"], ["X"])

    def test_actual_v76_low_score_or_hard_failure_is_not_accepted(self):
        task = release_good_task()
        task["scores"]["visual_quality"]["score"] = 1
        task["hard_fail"]["undisclosed_image_processing"] = True
        result = self.calc_release(release_ledger(task))
        self.assertEqual(result["final_delivery"]["completed_valid_reviews"], 1)
        self.assertEqual(result["final_delivery"]["accepted"], 0)

    def test_actual_v76_missing_hash_evidence_is_invalid(self):
        task = release_good_task()
        del task["source_sha256"]
        result = self.calc_release(release_ledger(task))
        self.assertEqual(result["final_delivery"]["accepted"], 0)
        reasons = result["final_delivery"]["invalid_completed_reviews"][0]["reasons"]
        self.assertIn("HASH_EVIDENCE_FIELD_MISSING:source_sha256", reasons)


if __name__ == "__main__":
    unittest.main()
