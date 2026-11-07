#!/usr/bin/env python3
"""Check frozen benchmark coverage and release-gate completeness."""
from __future__ import annotations

import json

from scientific_ir import ROOT

OUTPUTS = {
    "B01": "dist/B01_engineering_fdir_v71.pptx",
    "F07": "dist/F07_telemetry_embedding_v71.pptx",
    "C01_FBG": "dist/C01_FBG_construction_v73.pptx",
    "C01_SEANet": "dist/C01_SEANet_graph_level_v73.pptx",
    "C01_composite": "dist/C01_composite_defense_slide_v74.pptx",
    **{f"Q{i:02d}": f"dist/{stem}.pptx" for i, stem in enumerate((
        "Q01_iris_scatter", "Q02_iris_strip", "Q03_iris_mean_ci", "Q04_iris_confusion",
        "Q05_iris_ablation", "Q06_iris_trend_interval"), 1)},
    "I01": "dist/I01_cell_image_quant.pptx",
    "DECK01": "dist/DECK01_c01_defense.pptx",
}


def main():
    benchmark = json.loads((ROOT / "specs/research_figure_benchmark_v76.json").read_text(encoding="utf-8"))
    tasks = benchmark["tasks"]
    assert 12 <= len(tasks) <= 15
    assert len({task["id"] for task in tasks}) == len(tasks)
    assert len(benchmark["scoring"]["dimensions"]) == 6
    assert len(benchmark["scoring"]["hard_fail"]) == 4
    categories = {task["category"] for task in tasks}
    assert {"paper_figure_redraw", "full_defense_narrative", "engineering_mechanism",
            "quant_interval", "ablation_comparison", "image_plus_quant"} <= categories
    for task in tasks:
        assert task["mode"] in {"presentation", "publication"}
        assert (ROOT / task["source"]).is_file() and (ROOT / task["input"]).is_file()
        assert task["expected"] and task["traps"]
        assert task["status"] in {"automated_fixture", "contract_only"}
        if task["status"] == "automated_fixture":
            assert (ROOT / OUTPUTS[task["id"]]).is_file()
    ready = sum(task["status"] == "automated_fixture" for task in tasks)
    assert ready == len(tasks) == 13
    print(f"PASS benchmark contract: {len(tasks)} automated fixtures; expert review pending")


if __name__ == "__main__":
    main()
