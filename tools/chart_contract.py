#!/usr/bin/env python3
"""Dataset-independent scientific checks for tabular ChartSpecs."""
from __future__ import annotations

import math


def validate_chart_contract(config: dict, rows: list[dict]) -> None:
    meta = config["data"]
    assert meta["row_unit"] and meta["source_url"] and meta["doi"] and meta["license"]
    assert meta["transforms"] and all(meta["transforms"])
    assert meta["missing_value_policy"] in {"fail", "documented_exclusion", "documented_imputation"}
    assert len(rows) == meta["row_count"]
    columns = meta["columns"]
    assert len({field["source_position"] for field in columns.values()}) == len(columns)
    assert all(field["unit"] for field in columns.values())

    for chart in config["charts"]:
        assert chart["claim"] and chart["caption"] and chart["encoding"]
        derived = chart.get("derived_fields", {})
        used = {chart[key] for key in ("x", "y", "group")}
        assert set(derived) == used - set(columns), (chart["id"], "derived fields")
        for name, field in derived.items():
            assert field["type"] in {"number", "category"} and field["unit"] and field["derivation"]
            assert field["source_fields"] and set(field["source_fields"]) <= set(columns), name

        selected = [row for row in rows if all(row.get(key) == value
                    for key, value in chart.get("filter", {}).items())]
        assert selected and len(selected) == chart["sample_size"], (chart["id"], "sample size")
        assert set(chart["axes"]) == {"x", "y"}
        for direction in ("x", "y"):
            field_name = chart[direction]
            axis = chart["axes"][direction]
            assert axis["field"] == field_name, (chart["id"], direction, "axis field")
            field = columns.get(field_name, derived.get(field_name))
            assert field is not None and axis["unit"] == field["unit"], (chart["id"], direction, "unit")
            expected_type = "linear" if field["type"] == "number" else "category"
            assert axis["type"] == expected_type, (chart["id"], direction, "axis type")
            if axis["type"] == "linear":
                low, high = axis["domain"]
                assert math.isfinite(low) and math.isfinite(high) and low < high
                assert axis["zero_included"] is (low <= 0 <= high)
                assert axis["zero_included"] or axis.get("domain_reason")
                if field_name in columns:
                    assert all(low <= row[field_name] <= high for row in selected), (
                        chart["id"], field_name, "clipped source value")
            else:
                categories = axis["categories"]
                assert categories and len(categories) == len(set(categories))
                if field_name in columns:
                    assert set(categories) == {row[field_name] for row in selected}, (
                        chart["id"], field_name, "category coverage")
        statistics = chart["statistics"]
        assert statistics["display"] and statistics["interval"]
        if statistics["interval"] == "bootstrap_percentile_95":
            assert statistics["resamples"] > 0 and isinstance(statistics["seed"], int)
            assert statistics["resampling_unit"]
