#!/usr/bin/env python3
"""Exercise the common ChartSpec gates on two independent source datasets."""
from __future__ import annotations

import copy
import json
import unittest

from chart_contract import validate_chart_contract
from chart_data import load_rows
from scientific_ir import ROOT


class ChartContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = []
        for name in ("iris", "wine"):
            config = json.loads((ROOT / f"specs/{name}_charts_v76.json").read_text(encoding="utf-8"))
            cls.cases.append((config, load_rows(config["data"])))

    def test_both_datasets_pass(self):
        for config, rows in self.cases:
            validate_chart_contract(config, rows)

    def test_wrong_sample_size_fails_both(self):
        for config, rows in self.cases:
            changed = copy.deepcopy(config)
            changed["charts"][0]["sample_size"] -= 1
            with self.assertRaises(AssertionError):
                validate_chart_contract(changed, rows)

    def test_wrong_axis_unit_fails_both(self):
        for config, rows in self.cases:
            changed = copy.deepcopy(config)
            changed["charts"][0]["axes"]["x"]["unit"] = "invented unit"
            with self.assertRaises(AssertionError):
                validate_chart_contract(changed, rows)

    def test_clipped_source_values_fail_both(self):
        for config, rows in self.cases:
            changed = copy.deepcopy(config)
            changed["charts"][0]["axes"]["x"]["domain"][1] = 12 if "wine" in changed["data"]["id"] else 1
            with self.assertRaises(AssertionError):
                validate_chart_contract(changed, rows)

    def test_missing_bootstrap_definition_fails(self):
        config, rows = self.cases[0]
        changed = copy.deepcopy(config)
        next(chart for chart in changed["charts"] if chart["kind"] == "point_ci")["statistics"].pop("resampling_unit")
        with self.assertRaises((AssertionError, KeyError)):
            validate_chart_contract(changed, rows)


if __name__ == "__main__":
    unittest.main()
