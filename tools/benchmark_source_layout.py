#!/usr/bin/env python3
"""Replay source-layout extraction over a frozen, hash-locked local PDF cohort."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import jsonschema

from extract_source_layout import extract_source_layout
from audit_source_crop_manifest import audit_source_crop_manifest


def run_benchmark(source_dir: Path, manifest_path: Path, output_dir: Path) -> dict:
    source_dir = Path(source_dir)
    manifest_path = Path(manifest_path)
    output_dir = Path(output_dir)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    schema_path = Path(__file__).resolve().parents[1] / "specs" / "source_figure_layout.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    crop_audit = audit_source_crop_manifest(source_dir, manifest_path)
    if crop_audit["status"] != "PASS":
        raise ValueError("SOURCE_CROP_MANIFEST_AUDIT_FAIL: " +
                         json.dumps(crop_audit["failures"], ensure_ascii=False))
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for source in manifest["sources"]:
        pdf = source_dir / source["filename"]
        if not pdf.is_file():
            raise FileNotFoundError(f"Frozen source missing: {pdf}")
        actual_sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
        if actual_sha != source["sha256"]:
            raise ValueError(
                f"SOURCE_HASH_MISMATCH for {source['figure_id']}: "
                f"expected {source['sha256']}, got {actual_sha}"
            )
        page_index = int(source["page_1based"]) - 1
        layout = extract_source_layout(
            pdf, page_index=page_index,
            figure_region=tuple(source["region_pt"]),
        )
        jsonschema.validate(layout, schema)
        layout["benchmark"] = {
            "benchmark_id": manifest["benchmark_id"],
            "figure_id": source["figure_id"],
            "cohort_role": manifest["cohort_role"],
            "region_status": "manual_crop_candidate_requires_review",
        }
        target = output_dir / f"{source['figure_id']}_source_layout.json"
        target.write_text(json.dumps(layout, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        rows.append({
            "figure_id": source["figure_id"],
            "source_sha256": actual_sha,
            "page_1based": source["page_1based"],
            "panel_detection_status": layout["panel_detection"]["status"],
            "confirmed_panels": len(layout["panel_detection"]["panels"]),
            "unresolved_markers": len(layout["panel_detection"]["unresolved_markers"]),
            "layout_elements": len(layout["layout_elements"]),
            "stroke_segment_candidates": len(layout["stroke_segment_candidates"]),
            "image_assets": len(layout["image_assets"]),
            "font_families": len(layout["style_profile"]["font_families"]),
            "palette_colors": len(layout["style_profile"]["palette"]),
            "layout_file": target.name,
            "layout_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        })

    summary = {
        "benchmark_id": manifest["benchmark_id"],
        "cohort_role": manifest["cohort_role"],
        "status": "COMPLETED",
        "source_count": len(rows),
        "source_hashes_verified": len(rows),
        "outputs_schema_validated": len(rows),
        "strict_blind_test_pass_rate": "not measured by source-layout extraction",
        "human_review_required": True,
        "crop_manifest_audit": {
            "status": crop_audit["status"],
            "passed": crop_audit["passed"],
            "failed": crop_audit["failed"],
        },
        "rows": rows,
    }
    summary_path = output_dir / "source_layout_benchmark_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    csv_path = output_dir / "source_layout_benchmark_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    summary["summary_json"] = str(summary_path)
    summary["summary_csv"] = str(csv_path)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path,
                        default=Path(__file__).resolve().parents[1] /
                        "tests/fixtures/blind10_source_regions_2026-11-14.json")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run_benchmark(args.source_dir, args.manifest, args.output_dir)
    print(json.dumps({
        "status": result["status"],
        "source_count": result["source_count"],
        "schema_validated": result["outputs_schema_validated"],
        "summary_json": result["summary_json"],
        "summary_csv": result["summary_csv"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
