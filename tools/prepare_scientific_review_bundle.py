#!/usr/bin/env python3
"""Package the frozen benchmark inputs and outputs for an independent reviewer."""
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

from scientific_ir import ROOT
from validate_release_readiness import prepare_template
from validate_research_benchmark import artifact_paths


UNBLIND_EXTRA = {
    "SKILL.md", "README.md", "MANIFEST_V7.json",
    "specs/research_figure_benchmark_v76.json", "specs/output_profiles_v76.json",
    "specs/figure_contracts_v76.json",
    "docs/SCIENTIFIC_FIGURE_GAP_AND_UPGRADE_PLAN_2026.md",
    "docs/SCIENTIFIC_FIGURE_V76_COMPLETION_AUDIT.md",
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
    unblind |= blind  # Stage 2 is self-contained for the release validator.
    missing = [str(path) for path in unblind if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Review inputs missing: {missing}")
    return sorted(blind), sorted(unblind)


def build(output: Path) -> None:
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    note = (
        "Independent scientific figure review bundle\n"
        "Stage 1: inspect blind_review/ sources and rendered figures at final viewing size.\n"
        "Record an initial score and evidence for each task before opening unblind_review/.\n"
        "Stage 2: inspect unblind_review/ benchmark expectations, traps, specs and methods.\n"
        "Reconcile any differences, then complete review_template.json for all 15 tasks.\n"
        "The second stage includes source data, build scripts and validators.\n"
        "Example checks: python unblind_review/tools/validate_quantitative_examples.py\n"
        "                python unblind_review/tools/validate_wine_scatter.py\n"
        "                python unblind_review/tools/validate_publication_example.py\n"
        "Read review_form.md before scoring.\n"
        "Run: python unblind_review/tools/validate_release_readiness.py --review review_template.json\n"
        "The template is unfilled; this archive does not assert scientific or journal approval.\n"
        "Publisher-owned source artwork is linked in source docs rather than redistributed.\n"
    )
    blind, unblind = bundle_paths()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in blind:
            archive.write(path, "blind_review/" + path.relative_to(ROOT).as_posix())
        for path in unblind:
            archive.write(path, "unblind_review/" + path.relative_to(ROOT).as_posix())
        archive.writestr("review_form.md", (ROOT / "docs/SCIENTIFIC_FIGURE_REVIEW_FORM_V76.md").read_text(encoding="utf-8"))
        archive.writestr("review_template.json", json.dumps(prepare_template(), ensure_ascii=False, indent=2)+"\n")
        archive.writestr("REVIEW_README.txt", note)
    print(f"Prepared unfilled review bundle: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    build(parser.parse_args().output)
