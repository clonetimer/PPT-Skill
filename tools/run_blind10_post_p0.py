#!/usr/bin/env python3
"""Run the frozen ten-paper post-P0 PDF-import regression locally.

Source PDFs remain private. This runner verifies the frozen source manifest,
then creates one isolated reproduction directory per selected figure crop.
It is a technical reproduction run, not an automatic scientific acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from audit_blind10_sources import audit_one
from reproduce_research_figure import run_pipeline


# These source crops have no PDF vector drawing records in the reviewed
# source-layout inventory. Their only honest import evidence class is a
# source-picture-preserving recovery, not native semantic reconstruction.
SOURCE_PICTURE_ONLY = {
    "01_wind_turbine_causal_framework",
    "06_harnessmm_overview",
    "07_iiot_mult_agent_digital_twin",
}


def run_cohort(source_dir: Path, manifest_path: Path, output_dir: Path,
               *, max_seconds: float = 60.0) -> dict:
    source_dir = Path(source_dir).resolve()
    manifest_path = Path(manifest_path).resolve()
    output_dir = Path(output_dir).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sources = manifest["sources"]

    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(
            f"Output directory is not empty; refusing to overwrite evidence: {output_dir}"
        )

    preflight = []
    for source in sources:
        result, _ = audit_one(source_dir, source)
        preflight.append(result)
    if len(preflight) != 10 or any(item["status"] != "PASS" for item in preflight):
        report = {
            "status": "BLOCKED_SOURCE_PREFLIGHT",
            "cohort_role": manifest.get("cohort_role"),
            "source_count": len(preflight),
            "preflight": preflight,
            "runs": [],
        }
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "blind10_post_p0_summary.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return report

    output_dir.mkdir(parents=True, exist_ok=True)
    runs = []
    for source in sources:
        figure_id = source["figure_id"]
        destination = output_dir / figure_id
        result = run_pipeline(
            source_dir / source["filename"],
            destination,
            mode="import",
            render_host="auto",
            require_native=figure_id not in SOURCE_PICTURE_ONLY,
            require_office_host=False,
            max_seconds=max_seconds,
            page_index=source["page_1based"] - 1,
            figure_region=tuple(source["region_pt"]),
        )
        manifest_file = destination / "delivery_manifest.json"
        runs.append({
            "figure_id": figure_id,
            "source_sha256": source["sha256"],
            "source_page_1based": source["page_1based"],
            "source_region_pt": source["region_pt"],
            "route": "SOURCE_PICTURE_ONLY_ALLOWED" if figure_id in SOURCE_PICTURE_ONLY
                     else "NATIVE_EDITABLE_IMPORT_REQUIRED",
            "pipeline_status": result.get("status"),
            "full_release_accepted": result.get("full_release_accepted"),
            "blockers": result.get("blockers", []),
            "pending_approvals": result.get("pending_approvals", []),
            "delivery_manifest": str(manifest_file),
            "delivery_manifest_sha256": (
                hashlib.sha256(manifest_file.read_bytes()).hexdigest()
                if manifest_file.is_file() else None
            ),
        })

    counts = {}
    for item in runs:
        status = item["pipeline_status"] or "UNKNOWN"
        counts[status] = counts.get(status, 0) + 1
    report = {
        "schema_version": "1.0.0",
        "benchmark_id": manifest.get("benchmark_id"),
        "cohort_role": manifest.get("cohort_role"),
        "run_type": "POST_P0_TECHNICAL_PDF_IMPORT_DIAGNOSTIC",
        "source_preflight": "PASS_10_OF_10",
        "source_count": len(sources),
        "pipeline_status_counts": counts,
        "scientific_human_acceptance": "NOT_PERFORMED",
        "powerpoint_2016_host_roundtrip": "NOT_PERFORMED",
        "strict_reproduction_pass_rate": None,
        "runs": runs,
    }
    (output_dir / "blind10_post_p0_summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-seconds", type=float, default=60.0)
    args = parser.parse_args()
    result = run_cohort(
        args.source_dir, args.manifest, args.output_dir, max_seconds=args.max_seconds
    )
    print(json.dumps({
        "status": result["status"] if "status" in result else "COMPLETED",
        "source_preflight": result.get("source_preflight"),
        "source_count": result.get("source_count"),
        "pipeline_status_counts": result.get("pipeline_status_counts", {}),
        "summary": str(args.output_dir / "blind10_post_p0_summary.json"),
    }, ensure_ascii=False))
    return 0 if result.get("source_preflight") == "PASS_10_OF_10" else 1


if __name__ == "__main__":
    raise SystemExit(main())
