#!/usr/bin/env python3
"""Write hashes and tool versions for the five reproducible research examples."""
from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path

import PIL
import pptx

from audit_pptx import audit
from scientific_ir import ROOT

IDS = ["Q01_iris_scatter", "Q02_iris_strip", "Q03_iris_mean_ci",
       "Q04_iris_confusion", "Q05_iris_ablation", "Q06_iris_trend_interval", "I01_cell_image_quant"]


def digest(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    records = []
    for figure_id in IDS:
        folder = "image" if figure_id.startswith("I") else "quant"
        spec = ROOT / f"figure_specs/{folder}/{figure_id}.json"
        outputs = {kind: ROOT / f"{base}/{figure_id}.{kind}"
                   for kind, base in (("svg", "examples"), ("pptx", "dist"),
                                      ("pdf", "dist"), ("preview.png", "dist"))}
        assert spec.is_file() and all(path.is_file() for path in outputs.values())
        qa = audit(outputs["pptx"])
        assert not qa["theme_first_effect_has_shadow"]
        assert all(s["out_of_bounds"] == s["text_box_overlaps"] == 0 for s in qa["slides"])
        assert all(s["non_svg_picture_objects"] == (1 if figure_id.startswith("I") else 0)
                   for s in qa["slides"])
        records.append({"figure_id": figure_id, "figure_spec": str(spec.relative_to(ROOT)).replace("\\", "/"),
                        "input_sha256": digest(spec),
                        "outputs_sha256": {kind: digest(path) for kind, path in outputs.items()},
                        "qa": {"automated": "pass", "manual_final_size": "pending_independent_review"}})
    record = {
        "schema_version": "7.6.0-dev", "build_commands": ["python tools/build_quantitative_examples.py",
            "python tools/build_image_quant_example.py", "pwsh tools/export_quantitative_pdf.ps1"],
        "tool_versions": {"python": platform.python_version(), "python_pptx": pptx.__version__,
                          "pillow": PIL.__version__, "pdf_exporter": "Microsoft PowerPoint 16.0"},
        "platform": platform.platform(), "font_substitution": "not_measured",
        "source_assets_sha256": {"data/iris_uci.csv": digest(ROOT / "data/iris_uci.csv"),
                                 "data/cell_scikit_image_v026.png": digest(ROOT / "data/cell_scikit_image_v026.png")},
        "figures": records,
    }
    destination = ROOT / "dist/render_record_v76.json"
    destination.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS render record: {len(records)} figures; manual final-size review pending")


if __name__ == "__main__":
    main()
