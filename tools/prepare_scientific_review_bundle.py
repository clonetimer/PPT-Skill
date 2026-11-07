#!/usr/bin/env python3
"""Package the frozen benchmark inputs and outputs for an independent reviewer."""
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

from scientific_ir import ROOT
from validate_release_readiness import prepare_template, review_input_paths
from validate_research_benchmark import artifact_paths


UNBLIND_EXTRA = {
    "SKILL.md", "README.md", "MANIFEST_V7.json",
    "specs/research_figure_benchmark_v76.json", "specs/output_profiles_v76.json",
    "specs/figure_contracts_v76.json",
    "docs/SCIENTIFIC_FIGURE_GAP_AND_UPGRADE_PLAN_2026.md",
    "docs/SCIENTIFIC_FIGURE_V76_COMPLETION_AUDIT.md",
    "docs/C01_V76_SOURCE_CORRECTION.md",
    "docs/SCIENTIFIC_FIGURE_REVIEW_FORM_V76.md",
    "docs/Q03_NATURE_PUBLICATION_CAPTION.md",
    "data/README.md",
    "dist/render_record_v76.json", "dist/export_quantitative_metadata_v76.json",
    "tools/validate_release_readiness.py", "tools/validate_research_benchmark.py",
    "tools/scientific_ir.py",
}


def bundle_paths() -> tuple[list[Path], list[Path]]:
    benchmark = json.loads((ROOT / "specs/research_figure_benchmark_v76.json").read_text(encoding="utf-8"))
    blind = set()
    unblind = {ROOT / rel for rel in UNBLIND_EXTRA}
    unblind.update((ROOT / "tools").glob("*.py"))
    unblind.update((ROOT / "tools").glob("*.ps1"))
    unblind.update((ROOT / "specs").glob("*.json"))
    for task in benchmark["tasks"]:
        blind.add(ROOT / task["source"])
        blind.update(ROOT / path for path in artifact_paths(task["id"]))
        unblind.add(ROOT / task["input"])
        unblind.update(ROOT / path for path in review_input_paths(task))
    unblind |= blind  # Stage 2 is self-contained for the release validator.
    missing = [str(path) for path in unblind if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Review inputs missing: {missing}")
    return sorted(blind), sorted(unblind)


def initial_review_form() -> str:
    benchmark = json.loads((ROOT / "specs/research_figure_benchmark_v76.json").read_text(encoding="utf-8"))
    lines = [
        "# Stage 1 independent review record",
        "",
        "Inspect only blind_review/ sources and rendered figures. Record the initial score and evidence",
        "at actual viewing size before receiving the reconciliation archive.",
        "File names and sources can disclose project identity; benchmark expectations and implementation are withheld.",
        "",
        "Reviewer name, field, date and time:",
        "Display or print size, viewing distance, and equipment:",
        "Archive SHA-256 and source links checked:",
        "",
        "| Task | Initial score (0–4) | Source/figure evidence | Final-size observations | Critical concern |",
        "|---|---:|---|---|---|",
    ]
    lines.extend(f"| {task['id']} | | | | |" for task in benchmark["tasks"])
    lines.extend(["", "Freeze this record before opening the reconciliation archive.", ""])
    return "\n".join(lines)


def build(output: Path, stage: str = "combined") -> None:
    if stage not in {"initial", "reconciliation", "combined"}:
        raise ValueError(stage)
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    initial_note = (
        "Independent scientific figure review: initial stage\n"
        "Inspect blind_review/ sources and rendered figures at actual viewing size.\n"
        "Record each initial score, evidence and size observation in initial_review_form.md.\n"
        "Freeze that record before receiving any benchmark expectations or implementation.\n"
        "Some file names and sources may reveal project identity. Publisher-owned artwork\n"
        "is linked in source documents rather than redistributed.\n"
    )
    reconciliation_note = (
        "Independent scientific figure review: reconciliation stage\n"
        "Open only after the initial review record has been frozen.\n"
        "Inspect unblind_review/ expectations, traps, inputs, builders and validators.\n"
        "Complete review_template.json for all 15 tasks using review_form.md.\n"
        "Example: python unblind_review/tools/validate_quantitative_examples.py\n"
        "Run: python unblind_review/tools/validate_release_readiness.py --review review_template.json\n"
        "The template is unfilled and does not assert scientific or journal approval.\n"
    )
    note = (initial_note if stage == "initial" else reconciliation_note if stage == "reconciliation"
            else initial_note + "\n" + reconciliation_note)
    blind, unblind = bundle_paths()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        if stage in {"initial", "combined"}:
            for path in blind:
                archive.write(path, "blind_review/" + path.relative_to(ROOT).as_posix())
            archive.writestr("initial_review_form.md", initial_review_form())
        if stage in {"reconciliation", "combined"}:
            for path in unblind:
                archive.write(path, "unblind_review/" + path.relative_to(ROOT).as_posix())
            archive.writestr("review_form.md", (ROOT / "docs/SCIENTIFIC_FIGURE_REVIEW_FORM_V76.md").read_text(encoding="utf-8"))
            archive.writestr("review_template.json", json.dumps(prepare_template(), ensure_ascii=False, indent=2)+"\n")
        archive.writestr("REVIEW_README.txt", note)
    print(f"Prepared unfilled review bundle: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stage", choices=("initial", "reconciliation", "combined"), default="combined")
    args = parser.parse_args()
    build(args.output, args.stage)
