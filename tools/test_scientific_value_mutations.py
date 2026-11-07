#!/usr/bin/env python3
"""Ensure altered scientific values and image processing claims fail validation."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from build_quantitative_examples import CONFIG, ROOT, load_data
from check_scientific_accessibility import check_text_contrast
from validate_image_quant_example import validate as validate_image
from validate_quantitative_examples import validate_outputs


def with_changed_spec(path, changed, action):
    original = Path.read_text

    def replacement(self, *args, **kwargs):
        if self.resolve() == path.resolve():
            return json.dumps(changed, ensure_ascii=False)
        return original(self, *args, **kwargs)

    with patch.object(Path, "read_text", replacement):
        action()


class ScientificValueMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.rows = load_data(cls.config)

    def chart_case(self, chart_id, mutate):
        chart = next(item for item in self.config["charts"] if item["id"] == chart_id)
        config = copy.deepcopy(self.config)
        config["charts"] = [chart]
        path = ROOT / f"figure_specs/quant/{chart_id}.json"
        changed = json.loads(path.read_text(encoding="utf-8"))
        mutate(changed)
        with self.assertRaises(AssertionError):
            with_changed_spec(path, changed, lambda: validate_outputs(config, self.rows))

    def test_wrong_confusion_count_fails(self):
        self.chart_case("Q04_iris_confusion", lambda spec: spec["computed_values"][0].update(count=49))

    def test_wrong_bootstrap_interval_fails(self):
        self.chart_case("Q03_iris_mean_ci", lambda spec: spec["computed_values"][0]["ci95"].__setitem__(0, 0.0))

    def test_moved_raw_point_fails(self):
        def move(spec):
            next(item for item in spec["elements"] if "data_row" in item)["x"] += .5
        self.chart_case("Q01_iris_scatter", move)

    def test_moved_interval_endpoint_fails(self):
        def move(spec):
            next(item for item in spec["elements"] if item["type"] == "line"
                 and item.get("color") == "#1C303A" and item.get("sw") == 1.8
                 and item["x1"] == item["x2"])["y2"] += .2
        self.chart_case("Q03_iris_mean_ci", move)

    def test_wrong_ablation_prediction_fails(self):
        self.chart_case("Q05_iris_ablation", lambda spec: spec["computed_values"][0].update(correct=1))

    def test_wrong_ablation_bar_height_fails(self):
        def shorten(spec):
            next(item for item in spec["elements"] if "row_predictions" in item)["h"] -= 1
        self.chart_case("Q05_iris_ablation", shorten)

    def test_undisclosed_image_adjustment_fails(self):
        path = ROOT / "figure_specs/image/I01_cell_image_quant.json"
        changed = json.loads(path.read_text(encoding="utf-8"))
        changed["image_contract"]["display"]["intensity_transform"] = "contrast stretch"
        with self.assertRaises(AssertionError):
            with_changed_spec(path, changed, validate_image)

    def test_low_contrast_confusion_cell_fails(self):
        path = ROOT / "figure_specs/quant/Q04_iris_confusion.json"
        changed = json.loads(path.read_text(encoding="utf-8"))
        next(item for item in changed["elements"] if "source_rows" in item)["fill"] = "#26343C"
        with self.assertRaises(AssertionError):
            check_text_contrast("Q04_iris_confusion", changed)


if __name__ == "__main__":
    unittest.main()
