#!/usr/bin/env python3
"""Require a complete independent review of the exact benchmark artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from scientific_ir import ROOT
from validate_research_benchmark import artifact_paths


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def prepare_template() -> dict:
    benchmark_path = ROOT / "specs/research_figure_benchmark_v76.json"
    benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))
    return {
        "benchmark_sha256": sha256(benchmark_path),
        "reviewers": {},
        "tasks": {task["id"]: {
            "required_discipline": task["discipline"], "reviewer_id": "",
            "source_sha256": sha256(ROOT / task["source"]),
            "input_sha256": sha256(ROOT / task["input"]),
            "artifacts_sha256": {path: sha256(ROOT / path) for path in artifact_paths(task["id"])},
            "source_checked": False, "scientific_relationships_checked": False,
            "final_size": {"checked": False, "context": "", "evidence": ""},
            "scores": {dimension: {"score": None, "evidence": ""}
                       for dimension in benchmark["scoring"]["dimensions"]},
            "hard_fail": {reason: None for reason in benchmark["scoring"]["hard_fail"]},
            "conclusion": "pending",
        } for task in benchmark["tasks"]},
    }


def validate_review(review: dict) -> None:
    benchmark_path = ROOT / "specs/research_figure_benchmark_v76.json"
    benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))
    require(review.get("benchmark_sha256") == sha256(benchmark_path), "Benchmark changed since review")
    reviewers = review.get("reviewers", {})
    require(isinstance(reviewers, dict) and bool(reviewers), "Reviewer roster required")
    for reviewer_id, reviewer in reviewers.items():
        require(bool(reviewer_id and reviewer.get("name") and reviewer.get("date")),
                f"{reviewer_id}: reviewer identity and date required")
        require(isinstance(reviewer.get("disciplines"), list) and bool(reviewer["disciplines"]),
                f"{reviewer_id}: reviewer disciplines required")
        require(reviewer.get("independent_of_build") is True, f"{reviewer_id}: independence required")
        require(reviewer.get("blind_to_implementation_version") is True, f"{reviewer_id}: blind review required")
    results = review.get("tasks", {})
    expected_ids = {task["id"] for task in benchmark["tasks"]}
    require(set(results) == expected_ids, "Every benchmark task needs one review")
    dimensions = benchmark["scoring"]["dimensions"]
    hard_fails = benchmark["scoring"]["hard_fail"]
    for task in benchmark["tasks"]:
        task_id = task["id"]
        result = results[task_id]
        require(result.get("required_discipline") == task["discipline"], f"{task_id}: discipline changed")
        reviewer_id = result.get("reviewer_id")
        require(reviewer_id in reviewers, f"{task_id}: assigned reviewer required")
        require(task["discipline"] in reviewers[reviewer_id]["disciplines"],
                f"{task_id}: reviewer field does not cover {task['discipline']}")
        require(result.get("source_checked") is True, f"{task_id}: source check required")
        require(result.get("scientific_relationships_checked") is True, f"{task_id}: science check required")
        source = ROOT / task["source"]
        spec = ROOT / task["input"]
        require(result.get("source_sha256") == sha256(source), f"{task_id}: source changed")
        require(result.get("input_sha256") == sha256(spec), f"{task_id}: input changed")
        artifacts = result.get("artifacts_sha256", {})
        expected_artifacts = artifact_paths(task_id)
        require(set(artifacts) == set(expected_artifacts), f"{task_id}: reviewed artifact list changed")
        for path in expected_artifacts:
            require(artifacts[path] == sha256(ROOT / path), f"{task_id}: {path} changed")
        final_size = result.get("final_size", {})
        require(final_size.get("checked") is True and bool(final_size.get("context")), f"{task_id}: final-size check required")
        require(bool(final_size.get("evidence")), f"{task_id}: final-size evidence required")
        scores = result.get("scores", {})
        require(set(scores) == set(dimensions), f"{task_id}: all six scores required")
        for dimension in dimensions:
            item = scores[dimension]
            require(type(item.get("score")) is int and 0 <= item["score"] <= 4,
                    f"{task_id}: {dimension} score must be 0–4")
            require(bool(item.get("evidence")), f"{task_id}: {dimension} evidence required")
        failures = result.get("hard_fail", {})
        require(set(failures) == set(hard_fails), f"{task_id}: hard-failure checklist incomplete")
        require(all(type(failures[key]) is bool for key in hard_fails), f"{task_id}: hard failure unresolved")
        require(not any(failures.values()), f"{task_id}: hard failure blocks release")
        require(result.get("conclusion") == "pass", f"{task_id}: task conclusion must be pass")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", type=Path, metavar="PATH", help="write an unfilled review template")
    mode.add_argument("--review", type=Path, metavar="PATH", help="check a completed independent review")
    args = parser.parse_args()
    if args.prepare:
        require(not args.prepare.exists(), "Refusing to overwrite an existing review")
        args.prepare.write_text(json.dumps(prepare_template(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Prepared unfilled review template: {args.prepare}")
    else:
        validate_review(json.loads(args.review.read_text(encoding="utf-8")))
        print("PASS release readiness: all benchmark tasks independently reviewed; no hard failures")


if __name__ == "__main__":
    main()
