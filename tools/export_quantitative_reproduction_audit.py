#!/usr/bin/env python3
"""Export reproducible Q03/Q06 bootstrap audit and row-to-mark traceability."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from validate_quantitative_examples import validate_config, validate_outputs
from build_quantitative_examples import CONFIG, load_data
from chart_contract import validate_chart_contract
from scientific_ir import ROOT

CHART_IDS = (
    "Q01_iris_scatter", "Q02_iris_strip", "Q03_iris_mean_ci",
    "Q03_iris_mean_ci_nature", "Q06_iris_trend_interval",
    "Q07_wine_scatter", "Q08_wine_strip",
)


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build() -> dict:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    validate_config(config)
    rows = load_data(config)
    validate_chart_contract(config, rows)
    # This independently recomputes the bootstrap summaries from source rows and
    # checks every stored interval, source row, mark coordinate and rendered artifact.
    validate_outputs(config, rows)

    point_rows = []
    specs = {}
    for chart_id in CHART_IDS:
        path = ROOT / f"figure_specs/quant/{chart_id}.json"
        spec = json.loads(path.read_text(encoding="utf-8"))
        specs[chart_id] = spec
        for element in spec["elements"]:
            if "data_row" not in element:
                continue
            point_rows.append({
                "chart_id": chart_id,
                "object_id": element["id"],
                "source_row": element["data_row"],
                "raw_values_json": json.dumps(element.get("data_values", {}), ensure_ascii=False, sort_keys=True),
                "display_geometry": json.dumps({key: element[key] for key in ("x","y","w","h")},
                                               ensure_ascii=False, sort_keys=True),
                "display_offset_policy": spec["chart_contract"]["statistics"].get("jitter", {}).get("purpose", "none"),
            })

    iris = ROOT / config["data"]["file"]
    q03 = specs["Q03_iris_mean_ci"]
    q06 = specs["Q06_iris_trend_interval"]
    q03_stats = q03["chart_contract"]["statistics"]
    q06_stats = q06["chart_contract"]["statistics"]
    report = {
        "schema_version": "1.0.0",
        "validation_status": "PASS",
        "validation_method": "validate_quantitative_examples.validate_outputs independently recomputes bootstrap intervals from source rows and checks saved values and point geometry",
        "source": {
            "file": config["data"]["file"],
            "sha256": config["data"]["sha256"],
            "row_count": config["data"]["row_count"],
            "row_unit": config["data"]["row_unit"],
        },
        "Q03": {
            "chart_claim": q03["chart_contract"]["claim"],
            "resampling": {
                "method": q03_stats["interval"],
                "resamples": q03_stats["resamples"],
                "seed": q03_stats["seed"],
                "resampling_unit": q03_stats["resampling_unit"],
                "percentile_order_statistics": [49, 1949],
                "interpretation": "95% percentile bootstrap interval for each species mean",
            },
            "groups": q03["computed_values"],
            "publication_variant_matches_source_values": specs["Q03_iris_mean_ci_nature"]["computed_values"] == q03["computed_values"],
        },
        "Q06": {
            "chart_claim": q06["chart_contract"]["claim"],
            "binning": q06_stats["bins"],
            "resampling": {
                "method": q06_stats["interval"],
                "resamples": q06_stats["resamples"],
                "base_seed": q06_stats["seed"],
                "bin_seed_rule": "base seed + zero-based bin index",
                "resampling_unit": q06_stats["resampling_unit"],
                "percentile_order_statistics": [49, 1949],
            },
            "bins": q06["computed_values"],
            "source_rows_partitioned_once": sorted(row for item in q06["computed_values"] for row in item["source_rows"]) == sorted(
                row["source_row"] for row in rows if row["species"] == "Iris-setosa"
            ),
        },
        "traceability": {
            "charts": list(CHART_IDS),
            "point_to_source_row_records": len(point_rows),
            "mapping_file": "dist/quantitative_point_traceability_v76.csv",
        },
    }
    if not report["Q03"]["publication_variant_matches_source_values"]:
        raise AssertionError("Q03_PUBLICATION_VARIANT_STATISTICS_DIVERGED")
    if not report["Q06"]["source_rows_partitioned_once"]:
        raise AssertionError("Q06_BIN_SOURCE_ROWS_NOT_A_PARTITION")

    csv_path = ROOT / "dist/quantitative_point_traceability_v76.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(point_rows[0]))
        writer.writeheader()
        writer.writerows(point_rows)
    report["traceability"]["sha256"] = sha(csv_path)
    json_path = ROOT / "dist/quantitative_reproduction_audit_v76.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    report = build()
    print(json.dumps({
        "status": report["validation_status"],
        "Q03_groups": len(report["Q03"]["groups"]),
        "Q06_bins": len(report["Q06"]["bins"]),
        "traceability_rows": report["traceability"]["point_to_source_row_records"],
        "report": "dist/quantitative_reproduction_audit_v76.json",
        "traceability": "dist/quantitative_point_traceability_v76.csv",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
