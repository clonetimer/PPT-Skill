#!/usr/bin/env python3
"""Load provenance-locked numeric/category columns without dataset-specific assumptions."""
from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path

from scientific_ir import ROOT


def load_rows(meta: dict, root: Path = ROOT) -> list[dict]:
    path = (root / meta["file"]).resolve()
    assert path.is_relative_to(root.resolve()) and path.is_file()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == meta["sha256"]
    assert meta["row_count"] > 0 and meta["row_unit"]
    assert meta["missing_value_policy"] == "fail", "Other missing-value policies need an explicit transform"
    columns = meta["columns"]
    positions = [field["source_position"] for field in columns.values()]
    assert positions and len(positions) == len(set(positions)) and min(positions) >= 0
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        raw_rows = list(csv.reader(stream))
        while raw_rows and not raw_rows[-1]:
            raw_rows.pop()  # UCI Iris has an empty record after the last observation.
        for source_row, raw in enumerate(raw_rows, 1):
            assert raw, (source_row, "blank row")
            assert len(raw) > max(positions), (source_row, "missing column")
            parsed = {"source_row": source_row}
            for name, field in columns.items():
                value = raw[field["source_position"]].strip()
                assert value, (source_row, name, "missing value")
                if field["type"] == "number":
                    number = float(value)
                    assert math.isfinite(number), (source_row, name, "nonfinite value")
                    parsed[name] = number
                else:
                    assert field["type"] == "category"
                    parsed[name] = value
            rows.append(parsed)
    assert len(rows) == meta["row_count"], (len(rows), meta["row_count"])
    return rows
