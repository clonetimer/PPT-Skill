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
    "Q03P": "dist/Q03_iris_mean_ci_nature.pptx",
    "DECK01": "dist/DECK01_c01_defense.pptx",
}


def artifact_paths(task_id):
    """Every artifact an independent reviewer must inspect for this task."""
    output = OUTPUTS[task_id]
    stem = output.removeprefix("dist/").removesuffix(".pptx")
    paths = [output]
    if task_id != "DECK01":
        paths.append(f"examples/{stem}.svg")
    if task_id.startswith("Q") or task_id == "I01":
        paths.extend(f"dist/{stem}.{suffix}" for suffix in
                     ("pdf", "preview.png", "grayscale.png", "protanopia.png", "deuteranopia.png"))
    elif task_id == "C01_composite":
        paths.append(f"dist/{stem}_preview.pdf")
    elif task_id == "DECK01":
        paths.append(f"dist/{stem}.pdf")
    return paths


def main():
    benchmark = json.loads((ROOT / "specs/research_figure_benchmark_v76.json").read_text(encoding="utf-8"))
    tasks = benchmark["tasks"]
    assert 12 <= len(tasks) <= 15
    assert len({task["id"] for task in tasks}) == len(tasks)
    assert len(benchmark["scoring"]["dimensions"]) == 6
    assert len(benchmark["scoring"]["hard_fail"]) == 4
    assert set(benchmark["scoring"]["dimension_checks"]) == set(benchmark["scoring"]["dimensions"])
    assert set(benchmark["scoring"]["score_anchors"]) == {str(value) for value in range(5)}
    assert all(benchmark["scoring"]["score_anchors"].values())
    assert type(benchmark["scoring"]["minimum_passing_score_per_dimension"]) is int
    assert 1 <= benchmark["scoring"]["minimum_passing_score_per_dimension"] <= 4
    categories = {task["category"] for task in tasks}
    assert {"paper_figure_redraw", "full_defense_narrative", "engineering_mechanism",
            "quant_interval", "ablation_comparison", "image_plus_quant"} <= categories
    disciplines = {task["discipline"] for task in tasks}
    assert disciplines == {"aerospace_systems", "machinery_fault_diagnosis",
                           "applied_statistics", "cell_imaging"}
    for task in tasks:
        assert task["mode"] in {"presentation", "publication"}
        assert task["discipline"] in disciplines
        assert (ROOT / task["source"]).is_file() and (ROOT / task["input"]).is_file()
        assert task["expected"] and task["traps"]
        assert task["status"] in {"automated_fixture", "contract_only"}
        if task["status"] == "automated_fixture":
            assert all((ROOT / path).is_file() for path in artifact_paths(task["id"]))
    ready = sum(task["status"] == "automated_fixture" for task in tasks)
    assert ready == len(tasks) == 14
    print(f"PASS benchmark contract: {len(tasks)} automated fixtures; expert review pending")


if __name__ == "__main__":
    main()
