#!/usr/bin/env python3
"""Ensure altered scientific values and image processing claims fail validation."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from build_quantitative_examples import CONFIG, ROOT, load_data
from check_scientific_accessibility import check_arrow_contrast, check_mark_contrast, check_text_contrast
from validate_image_quant_example import validate as validate_image
from validate_quantitative_examples import validate_outputs
from validate_publication_example import main as validate_publication


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

    def test_swapped_confusion_axis_label_fails(self):
        def relabel(spec):
            next(item for item in spec["elements"] if item["type"] == "text"
                 and item["text"] == "versicolor" and item.get("x") == 5.47)["text"] = "virginica"
        self.chart_case("Q04_iris_confusion", relabel)

    def test_wrong_bootstrap_interval_fails(self):
        self.chart_case("Q03_iris_mean_ci", lambda spec: spec["computed_values"][0]["ci95"].__setitem__(0, 0.0))

    def test_moved_raw_point_fails(self):
        def move(spec):
            next(item for item in spec["elements"] if "data_row" in item)["x"] += .5
        self.chart_case("Q01_iris_scatter", move)

    def test_collapsed_coincident_points_fail(self):
        def collapse(spec):
            seen = {}
            for point in (item for item in spec["elements"] if "data_row" in item):
                key = tuple(point["data_values"][name] for name in ("petal_length_cm", "petal_width_cm"))
                if key in seen:
                    point["x"], point["y"] = seen[key]["x"], seen[key]["y"]
                    return
                seen[key] = point
            raise AssertionError("No coincident observations in fixture")
        self.chart_case("Q01_iris_scatter", collapse)

    def test_swapped_scatter_legend_label_fails(self):
        def swap(spec):
            label = next(item for item in spec["elements"] if item["type"] == "text"
                         and item["text"] == "versicolor" and item.get("x") == 10.76)
            label["text"] = "virginica"
        self.chart_case("Q01_iris_scatter", swap)

    def test_collapsed_strip_points_fail(self):
        def collapse(spec):
            seen = {}
            for point in (item for item in spec["elements"] if "data_row" in item):
                key = (point["type"], point["data_values"]["sepal_length_cm"])
                if key in seen:
                    point["x"], point["y"] = seen[key]["x"], seen[key]["y"]
                    return
                seen[key] = point
            raise AssertionError("No equal-value observations in fixture")
        self.chart_case("Q02_iris_strip", collapse)

    def test_wrong_distribution_axis_tick_fails(self):
        def relabel(spec):
            tick = next(item for item in spec["elements"] if item["type"] == "text"
                        and item["text"] == "6" and item.get("x") == .55)
            tick["text"] = "8"
        self.chart_case("Q02_iris_strip", relabel)

    def test_wrong_publication_category_tick_fails(self):
        path = ROOT / "figure_specs/quant/Q03_iris_mean_ci_nature.json"
        changed = json.loads(path.read_text(encoding="utf-8"))
        next(item for item in changed["elements"] if item["type"] == "text"
             and item["text"] == "versicolor" and item.get("y") == 3.35)["text"] = "virginica"
        with self.assertRaises(AssertionError):
            with_changed_spec(path, changed, validate_publication)

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

    def test_wrong_drawn_scale_bar_fails(self):
        path = ROOT / "figure_specs/image/I01_cell_image_quant.json"
        changed = json.loads(path.read_text(encoding="utf-8"))
        next(item for item in changed["elements"] if item["type"] == "line"
             and item.get("color") == "#FFFFFF" and item.get("sw") == 3)["x1"] += .2
        with self.assertRaises(AssertionError):
            with_changed_spec(path, changed, validate_image)

    def test_wrong_histogram_bar_height_fails(self):
        path = ROOT / "figure_specs/image/I01_cell_image_quant.json"
        changed = json.loads(path.read_text(encoding="utf-8"))
        next(item for item in changed["elements"] if "histogram_bin" in item)["h"] += .5
        with self.assertRaises(AssertionError):
            with_changed_spec(path, changed, validate_image)

    def test_low_contrast_confusion_cell_fails(self):
        path = ROOT / "figure_specs/quant/Q04_iris_confusion.json"
        changed = json.loads(path.read_text(encoding="utf-8"))
        next(item for item in changed["elements"] if "source_rows" in item)["fill"] = "#26343C"
        with self.assertRaises(AssertionError):
            check_text_contrast("Q04_iris_confusion", changed)

    def test_low_contrast_raw_trend_point_fails(self):
        path = ROOT / "figure_specs/quant/Q06_iris_trend_interval.json"
        changed = json.loads(path.read_text(encoding="utf-8"))
        next(item for item in changed["elements"] if "data_row" in item)["fill"] = "#9CB4BA"
        with self.assertRaises(AssertionError):
            check_mark_contrast("Q06_iris_trend_interval", changed)

    def test_low_contrast_critical_arrow_fails(self):
        path = ROOT / "figure_specs/c01/C01_composite_defense_slide.json"
        changed = json.loads(path.read_text(encoding="utf-8"))
        next(item for item in changed["elements"] if item.get("semantic_link"))["color"] = "#D7DEE3"
        with self.assertRaises(AssertionError):
            check_arrow_contrast("C01_composite_defense_slide", changed)


if __name__ == "__main__":
    unittest.main()
