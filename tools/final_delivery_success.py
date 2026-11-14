"""Calculate immutable first-pass and evidence-backed final delivery rates.

Supports both the compact metric ledger and the project's actual V7.6 review.json.
The actual review.json path requires a registered human independent reviewer.
Run validate_release_readiness.py separately to verify all source/artifact hashes
and the all-tasks release gate before treating a cohort as release-ready.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

# Compact metric-ledger compatibility.
DIMENSIONS = (
    "science",
    "data_image_integrity",
    "readability",
    "accessibility",
    "editability_reproducibility",
    "visual_quality",
)
HARD_FAILS = (
    "critical_scientific_error",
    "source_or_provenance_error",
    "undisclosed_image_processing",
    "unreadable_critical_content",
)

# Canonical V7.6 scientific review schema.
REVIEW_DIMENSIONS = (
    "scientific_accuracy",
    "data_image_integrity",
    "readability",
    "accessibility",
    "editability_reproducibility",
    "visual_quality",
)
REVIEW_HARD_FAILS = (
    "wrong_critical_relation_or_formula_or_value",
    "unclear_source_status",
    "undisclosed_image_processing",
    "unreadable_or_occluded_important_content",
)


def _baseline_metrics(baseline_path: Path) -> dict:
    baseline = json.loads(Path(baseline_path).read_text(encoding="utf-8"))
    rows = baseline.get("rows", [])
    population = int(baseline.get("first_pass_generated", len(rows)))
    passed = sum(bool(row.get("first_pass", {}).get("strict_pass")) for row in rows)
    return {
        "dataset_id": baseline.get("dataset_id"),
        "population": population,
        "passed": passed,
        "rate": round(passed / max(1, population), 6),
        "mean_score_24": baseline.get("mean_score_24"),
        "immutable": True,
        "score_source": "frozen historical first-pass baseline",
    }


def calculate_compact_ledger(baseline_path: Path, ledger_path: Path) -> dict:
    baseline = _baseline_metrics(baseline_path)
    ledger = json.loads(Path(ledger_path).read_text(encoding="utf-8"))
    reviewers = {
        item.get("reviewer_id"): item
        for item in ledger.get("reviewers", [])
        if item.get("reviewer_id")
    }
    tasks = ledger.get("tasks", [])
    completed = []
    accepted = []
    invalid = []
    repaired = []
    pending = []

    for task in tasks:
        task_id = task.get("task_id")
        if task.get("final_review_status") != "completed":
            pending.append(task_id)
            continue
        reasons = []
        reviewer = reviewers.get(task.get("reviewer_id"))
        if not reviewer:
            reasons.append("REVIEWER_NOT_REGISTERED")
        elif reviewer.get("human") is not True:
            reasons.append("REVIEWER_NOT_HUMAN")
        elif reviewer.get("independent") is not True:
            reasons.append("REVIEWER_NOT_INDEPENDENT")
        elif reviewer.get("discipline") not in task.get("required_disciplines", []):
            reasons.append("REVIEWER_DISCIPLINE_MISMATCH")
        if task.get("initial_review_before_expectations") is not True:
            reasons.append("INITIAL_REVIEW_ORDER_NOT_ATTESTED")

        scores = task.get("dimension_scores", {})
        evidence = task.get("dimension_evidence", {})
        for dimension in DIMENSIONS:
            score = scores.get(dimension)
            if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 4:
                reasons.append("INVALID_SCORE:" + dimension)
            elif score < 2:
                reasons.append("DIMENSION_BELOW_THRESHOLD:" + dimension)
            if not isinstance(evidence.get(dimension), str) or not evidence[dimension].strip():
                reasons.append("MISSING_EVIDENCE:" + dimension)

        hard = task.get("hard_failures", {})
        for flag in HARD_FAILS:
            if hard.get(flag) is not False:
                reasons.append("HARD_FAIL_NOT_EXPLICITLY_CLEARED:" + flag)

        if task.get("final_decision") not in ("PASS", "FAIL"):
            reasons.append("INVALID_FINAL_DECISION")
        if reasons:
            invalid.append({"task_id": task_id, "reasons": reasons})
            continue

        completed.append(task)
        if task["final_decision"] == "PASS":
            accepted.append(task)
            if int(task.get("repair_rounds", 0)) > 0:
                repaired.append(task)

    return _assemble_result(
        baseline, len(tasks), completed, accepted, repaired, invalid, pending,
        "compact_metric_ledger",
    )


def _review_task_reasons(task_id: str, task: dict, reviewers: dict) -> list[str]:
    reasons = []
    conclusion = task.get("conclusion")
    if conclusion not in ("pass", "fail"):
        return ["REVIEW_PENDING"]

    reviewer_id = task.get("reviewer_id")
    reviewer = reviewers.get(reviewer_id)
    if not reviewer:
        reasons.append("REVIEWER_NOT_REGISTERED")
    else:
        if reviewer.get("human") is not True:
            reasons.append("REVIEWER_NOT_HUMAN")
        if reviewer.get("independent_of_build") is not True:
            reasons.append("REVIEWER_NOT_INDEPENDENT")
        if task.get("required_discipline") not in reviewer.get("disciplines", []):
            reasons.append("REVIEWER_DISCIPLINE_MISMATCH")
        if reviewer.get("scored_before_reading_benchmark_expectations") is not True:
            reasons.append("REVIEW_NOT_BLIND")

    if type(task.get("repair_rounds")) is not int or task.get("repair_rounds", -1) < 0:
        reasons.append("INVALID_REPAIR_ROUND_COUNT")
    if task.get("source_checked") is not True:
        reasons.append("SOURCE_NOT_CHECKED")
    if task.get("scientific_relationships_checked") is not True:
        reasons.append("SCIENTIFIC_RELATIONSHIPS_NOT_CHECKED")

    initial = task.get("initial_review_before_expectations", {})
    if initial.get("completed") is not True:
        reasons.append("INITIAL_REVIEW_NOT_COMPLETED")
    if not isinstance(initial.get("score"), int) or isinstance(initial.get("score"), bool) or not 0 <= initial.get("score", -1) <= 4:
        reasons.append("INVALID_INITIAL_REVIEW_SCORE")
    if not isinstance(initial.get("evidence"), str) or not initial.get("evidence", "").strip():
        reasons.append("INITIAL_REVIEW_EVIDENCE_MISSING")

    final_size = task.get("final_size", {})
    if final_size.get("checked") is not True:
        reasons.append("FINAL_SIZE_NOT_CHECKED")
    if not isinstance(final_size.get("context"), str) or not final_size.get("context", "").strip():
        reasons.append("FINAL_SIZE_CONTEXT_MISSING")
    if not isinstance(final_size.get("evidence"), str) or not final_size.get("evidence", "").strip():
        reasons.append("FINAL_SIZE_EVIDENCE_MISSING")

    scores = task.get("scores", {})
    for dimension in REVIEW_DIMENSIONS:
        entry = scores.get(dimension, {})
        score = entry.get("score")
        if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 4:
            reasons.append("INVALID_SCORE:" + dimension)
        if not isinstance(entry.get("evidence"), str) or not entry.get("evidence", "").strip():
            reasons.append("MISSING_EVIDENCE:" + dimension)

    hard = task.get("hard_fail", {})
    for flag in REVIEW_HARD_FAILS:
        if not isinstance(hard.get(flag), bool):
            reasons.append("HARD_FAIL_NOT_RECORDED:" + flag)

    # The review validator owns SHA-256 verification. The calculator still
    # refuses a completed row that omits any hash evidence field.
    for field in ("source_sha256", "input_sha256", "related_inputs_sha256", "artifacts_sha256"):
        if field not in task:
            reasons.append("HASH_EVIDENCE_FIELD_MISSING:" + field)
    return reasons


def calculate_release_readiness_ledger(baseline_path: Path, ledger_path: Path) -> dict:
    baseline = _baseline_metrics(baseline_path)
    ledger = json.loads(Path(ledger_path).read_text(encoding="utf-8"))
    reviewers = ledger.get("reviewers", {})
    tasks = ledger.get("tasks", {})
    completed = []
    accepted = []
    invalid = []
    repaired = []
    pending = []

    for task_id, task in tasks.items():
        reasons = _review_task_reasons(task_id, task, reviewers)
        if reasons == ["REVIEW_PENDING"]:
            pending.append(task_id)
            continue
        if reasons:
            invalid.append({"task_id": task_id, "reasons": reasons})
            continue

        completed.append(task)
        scores = task.get("scores", {})
        hard = task.get("hard_fail", {})
        all_scores_pass = all(scores[d]["score"] >= 2 for d in REVIEW_DIMENSIONS)
        no_hard_fail = all(hard[flag] is False for flag in REVIEW_HARD_FAILS)
        if task.get("conclusion") == "pass" and all_scores_pass and no_hard_fail:
            accepted.append(task)
            if task.get("repair_rounds", 0) > 0:
                repaired.append(task)

    return _assemble_result(
        baseline, len(tasks), completed, accepted, repaired, invalid, pending,
        "v7.6_release_readiness_review",
    )


def _assemble_result(
    baseline: dict,
    registered: int,
    completed: list,
    accepted: list,
    repaired: list,
    invalid: list,
    pending: list,
    ledger_schema: str,
) -> dict:
    completed_count = len(completed)
    accepted_count = len(accepted)
    return {
        "schema_version": "1.2.0",
        "ledger_schema": ledger_schema,
        "first_pass": baseline,
        "final_delivery": {
            "registered_tasks": registered,
            "completed_valid_reviews": completed_count,
            "accepted": accepted_count,
            "accepted_after_repair": len(repaired),
            "rate_among_completed": round(accepted_count / completed_count, 6) if completed_count else None,
            "rate_over_registered_population": round(accepted_count / registered, 6) if registered else None,
            "status": "MEASURED" if completed_count else "NOT_YET_MEASURABLE",
            "pending_tasks": pending,
            "invalid_completed_reviews": invalid,
            "repair_rounds_mean_for_accepted": (
                round(sum(int(task.get("repair_rounds", 0)) for task in accepted) / accepted_count, 3)
                if accepted_count else None
            ),
            "rule": (
                "Final PASS requires a registered human independent reviewer, blind initial review, "
                "source and scientific-relation checks, final-size evidence, six evidenced dimensions "
                ">=2, and every hard-failure flag explicitly false. Run validate_release_readiness.py "
                "to verify source/artifact SHA-256 and the complete release gate."
            ),
        },
        "cohort_policy": {
            "first_pass_baseline_immutable": True,
            "development_cohort_is_not_blind_holdout": True,
            "scientific_and_office_host_gates_separate": True,
        },
    }


def calculate(baseline_path: Path, ledger_path: Path) -> dict:
    ledger = json.loads(Path(ledger_path).read_text(encoding="utf-8"))
    if isinstance(ledger.get("tasks"), dict):
        return calculate_release_readiness_ledger(baseline_path, ledger_path)
    return calculate_compact_ledger(baseline_path, ledger_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = calculate(args.baseline, args.ledger)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
