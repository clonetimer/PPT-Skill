#!/usr/bin/env python3
"""Fail scientific chart configurations with omitted metadata."""
from __future__ import annotations

import copy
import json
import unittest

from build_quantitative_examples import CONFIG, load_data
from validate_quantitative_examples import validate_axis_coverage, validate_config


class QuantitativeContractTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(CONFIG.read_text(encoding="utf-8"))

    def test_baseline(self):
        validate_config(self.config)

    def test_missing_source_fails(self):
        changed = copy.deepcopy(self.config)
        changed["data"]["source_url"] = ""
        with self.assertRaises((AssertionError, ValueError)):
            validate_config(changed)

    def test_missing_transform_log_fails(self):
        changed = copy.deepcopy(self.config)
        changed["data"]["transforms"] = []
        with self.assertRaises((AssertionError, ValueError)):
            validate_config(changed)

    def test_undisclosed_scatter_jitter_fails(self):
        changed = copy.deepcopy(self.config)
        changed["charts"][0]["caption"] = "Each point is one flower."
        with self.assertRaises((AssertionError, ValueError)):
            validate_config(changed)

    def test_undisclosed_strip_jitter_fails(self):
        changed = copy.deepcopy(self.config)
        changed["charts"][1]["caption"] = "All 50 flowers per species are shown."
        with self.assertRaises((AssertionError, ValueError)):
            validate_config(changed)

    def test_missing_unit_fails(self):
        changed = copy.deepcopy(self.config)
        changed["data"]["columns"]["petal_length_cm"]["unit"] = ""
        with self.assertRaises((AssertionError, ValueError)):
            validate_config(changed)

    def test_missing_n_fails(self):
        changed = copy.deepcopy(self.config)
        changed["charts"][0]["sample_size"] = 0
        with self.assertRaises((AssertionError, ValueError)):
            validate_config(changed)

    def test_missing_error_definition_fails(self):
        changed = copy.deepcopy(self.config)
        changed["charts"][2]["statistics"]["interval"] = ""
        with self.assertRaises((AssertionError, ValueError)):
            validate_config(changed)

    def test_missing_axis_contract_fails(self):
        changed = copy.deepcopy(self.config)
        del changed["charts"][0]["axes"]
        with self.assertRaises((AssertionError, ValueError, KeyError)):
            validate_config(changed)

    def test_truncated_axis_needs_reason(self):
        changed = copy.deepcopy(self.config)
        del changed["charts"][1]["axes"]["y"]["domain_reason"]
        with self.assertRaises((AssertionError, ValueError)):
            validate_config(changed)

    def test_zero_flag_must_match_domain(self):
        changed = copy.deepcopy(self.config)
        changed["charts"][0]["axes"]["x"]["zero_included"] = False
        with self.assertRaises((AssertionError, ValueError)):
            validate_config(changed)

    def test_axis_cannot_hide_source_values(self):
        changed = copy.deepcopy(self.config)
        changed["charts"][0]["axes"]["x"]["domain"] = [0, 5]
        with self.assertRaises(AssertionError):
            validate_axis_coverage(changed["charts"][0], load_data(self.config),
                                   self.config["data"]["columns"])


if __name__ == "__main__":
    unittest.main()
