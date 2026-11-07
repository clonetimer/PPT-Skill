#!/usr/bin/env python3
"""Fail scientific chart configurations with omitted metadata."""
from __future__ import annotations

import copy
import json
import unittest

from build_quantitative_examples import CONFIG
from validate_quantitative_examples import validate_config


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


if __name__ == "__main__":
    unittest.main()
