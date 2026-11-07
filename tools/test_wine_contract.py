#!/usr/bin/env python3
"""Reject source, value, location and unit mutations in the second dataset."""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from build_wine_scatter import CONFIG
from chart_data import load_rows
from validate_wine_scatter import SPEC, check


class WineContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.spec = json.loads(SPEC.read_text(encoding="utf-8"))

    def test_source_hash(self):
        changed = copy.deepcopy(self.config)
        changed["data"]["sha256"] = "0" * 64
        with self.assertRaises(AssertionError):
            check(changed, self.spec)

    def test_value(self):
        changed = copy.deepcopy(self.spec)
        next(e for e in changed["elements"] if "data_row" in e)["data_values"]["alcohol"] += 1
        with self.assertRaises(AssertionError):
            check(self.config, changed)

    def test_position(self):
        changed = copy.deepcopy(self.spec)
        next(e for e in changed["elements"] if "data_row" in e)["x"] += 1
        with self.assertRaises(AssertionError):
            check(self.config, changed)

    def test_axis_unit(self):
        changed = copy.deepcopy(self.config)
        spec = copy.deepcopy(self.spec)
        changed["charts"][0]["axes"]["x"]["unit"] = "%"
        spec["chart_contract"]["axes"]["x"]["unit"] = "%"
        with self.assertRaises(AssertionError):
            check(changed, spec)

    def test_csv_column_and_row_count(self):
        for mutation in (lambda meta: meta["columns"]["alcohol"].update(source_position=14),
                         lambda meta: meta.update(row_count=177)):
            changed = copy.deepcopy(self.config["data"])
            mutation(changed)
            with self.assertRaises(AssertionError):
                load_rows(changed)

    def test_only_terminal_blank_records_are_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.csv"
            meta = {"file": "sample.csv", "row_count": 2, "row_unit": "sample",
                    "missing_value_policy": "fail",
                    "columns": {"group": {"type": "category", "source_position": 0},
                                "value": {"type": "number", "source_position": 1}}}
            path.write_bytes(b"A,1\nB,2\n\n")
            meta["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(len(load_rows(meta, Path(directory))), 2)
            path.write_bytes(b"A,1\n\nB,2\n")
            meta["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaises(AssertionError):
                load_rows(meta, Path(directory))


if __name__ == "__main__":
    unittest.main()
