#!/usr/bin/env python3
"""Package the frozen benchmark inputs and outputs for an independent reviewer."""
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

from scientific_ir import ROOT
from validate_release_readiness import prepare_template
from validate_research_benchmark import OUTPUTS


EXTRA = {
    "SKILL.md", "README.md", "MANIFEST_V7.json",
    "specs/research_figure_benchmark_v76.json", "specs/output_profiles_v76.json",
    "specs/figure_contracts_v76.json",
    "docs/SCIENTIFIC_FIGURE_GAP_AND_UPGRADE_PLAN_2026.md",
    "docs/SCIENTIFIC_FIGURE_REVIEW_FORM_V76.md",
    "docs/Q03_NATURE_PUBLICATION_CAPTION.md",
    "dist/render_record_v76.json", "dist/export_quantitative_metadata_v76.json",
    "tools/validate_release_readiness.py", "tools/validate_research_benchmark.py",
    "tools/scientific_ir.py",
}


def bundle_paths() -> list[Path]:
    benchmark = json.loads((ROOT / "specs/research_figure_benchmark_v76.json").read_text(encoding="utf-8"))
    paths = {ROOT / rel for rel in EXTRA}
    for task in benchmark["tasks"]:
        paths.update(ROOT / task[key] for key in ("source", "input"))
        output = ROOT / OUTPUTS[task["id"]]
        paths.add(output)
        stem = output.stem
        for candidate in (ROOT / f"examples/{stem}.svg", ROOT / f"dist/{stem}.pdf",
                          ROOT / f"dist/{stem}_preview.pdf", ROOT / f"dist/{stem}.preview.png",
                          ROOT / f"dist/{stem}.grayscale.png", ROOT / f"dist/{stem}.protanopia.png",
                          ROOT / f"dist/{stem}.deuteranopia.png"):
            if candidate.is_file():
                paths.add(candidate)
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Review inputs missing: {missing}")
    return sorted(paths)


def build(output: Path) -> None:
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    note = (
        "V7.6 independent scientific figure review bundle\n"
        "Review the source documents/data and rendered SVG/PPTX/PDF at their final viewing size.\n"
        "Read docs/SCIENTIFIC_FIGURE_REVIEW_FORM_V76.md before scoring.\n"
        "Fill review_template_v76.json only after independently checking each of the 14 tasks.\n"
        "Run: python tools/validate_release_readiness.py --review review_template_v76.json\n"
        "The template is unfilled; this archive does not assert scientific or journal approval.\n"
        "Publisher-owned source artwork is linked in source docs rather than redistributed.\n"
    )
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in bundle_paths():
            archive.write(path, path.relative_to(ROOT).as_posix())
        archive.writestr("review_template_v76.json", json.dumps(prepare_template(), ensure_ascii=False, indent=2)+"\n")
        archive.writestr("REVIEW_README.txt", note)
    print(f"Prepared unfilled review bundle: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    build(parser.parse_args().output)
