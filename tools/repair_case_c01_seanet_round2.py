#!/usr/bin/env python3
"""Execute C01-SEANet structural repair round 02 with immutable evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

from repair_case_c01_seanet import run_case as run_first_repair
from validate_c01_seanet_v74 import validate as validate_v74

ROOT = Path(__file__).resolve().parents[1]
BASE_SPEC = ROOT / "figure_specs/c01/C01_SEANet_graph_level.json"
FINAL_SPEC = ROOT / "figure_specs/c01/C01_SEANet_graph_level_v74.json"
FINAL_PPTX = ROOT / "dist/C01_SEANet_graph_level_v74.pptx"


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def spec_diff(before_path: Path, after_path: Path) -> list[dict]:
    before = json.loads(Path(before_path).read_text(encoding="utf-8"))
    after = json.loads(Path(after_path).read_text(encoding="utf-8"))
    a = {x["id"]: x for x in before["elements"]}
    b = {x["id"]: x for x in after["elements"]}
    changes = []
    for object_id in sorted(set(a) | set(b)):
        if object_id not in a:
            changes.append({"id": object_id, "kind": "added", "after": b[object_id]})
        elif object_id not in b:
            changes.append({"id": object_id, "kind": "removed", "before": a[object_id]})
        else:
            fields = {
                key: {"before": a[object_id].get(key), "after": b[object_id].get(key)}
                for key in sorted(set(a[object_id]) | set(b[object_id]))
                if a[object_id].get(key) != b[object_id].get(key)
            }
            if fields:
                changes.append({"id": object_id, "kind": "modified", "fields": fields})
    return changes


def render_pptx(pptx: Path, output_dir: Path, stem: str) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    profile = output_dir / f"lo-profile-{stem}"
    profile.mkdir(parents=True, exist_ok=True)
    cmd = [
        "libreoffice",
        "-env:UserInstallation=" + profile.as_uri(),
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(output_dir),
        str(pptx),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    pdf = output_dir / (pptx.stem + ".pdf")
    if result.returncode != 0 or not pdf.is_file():
        raise RuntimeError("LIBREOFFICE_RENDER_FAILED:" + result.stdout + result.stderr)
    png_stem = output_dir / stem
    result = subprocess.run(
        ["pdftoppm", "-png", "-r", "120", str(pdf), str(png_stem), "-singlefile"],
        capture_output=True,
        text=True,
    )
    png = output_dir / (stem + ".png")
    if result.returncode != 0 or not png.is_file():
        raise RuntimeError("PDF_TO_PNG_FAILED:" + result.stdout + result.stderr)
    return pdf, png


def run_case(output_dir: Path, accepted_output: Path) -> dict:
    output_dir = Path(output_dir).resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("REPAIR_CASE_OUTPUT_DIR_MUST_BE_EMPTY")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Preserve the original first-pass and the accepted alignment-only round.
    first = run_first_repair(output_dir)
    rounds_dir = output_dir / "rounds"
    round_01 = rounds_dir / "round_01.pptx"
    round_02 = rounds_dir / "round_02.pptx"
    if not round_01.is_file() or round_02.exists():
        raise RuntimeError("ROUND_01_MISSING_OR_ROUND_02_ALREADY_EXISTS")
    if not FINAL_PPTX.is_file():
        subprocess.run([sys.executable, str(ROOT / "tools/build_c01_seanet_v74.py")], check=True)
    shutil.copy2(FINAL_PPTX, round_02)

    # Source-object diff is calculated from stable FigureSpec IDs.
    changes = spec_diff(BASE_SPEC, FINAL_SPEC)
    diff_path = output_dir / "round_02_object_diff.json"
    diff_path.write_text(json.dumps(changes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    quality = validate_v74()
    if quality.get("status") != "PASS":
        raise RuntimeError("ROUND_02_QUALITY_AUDIT_FAILED")
    quality_path = output_dir / "round_02_quality_audit.json"
    quality_path.write_text(json.dumps(quality, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Render first pass, round 01 and round 02 independently; Office 2016 remains a separate gate.
    renders = output_dir / "renders"
    first_pass = rounds_dir / "first_pass.pptx"
    pdf0, png0 = render_pptx(first_pass, renders, "first_pass")
    pdf1, png1 = render_pptx(round_01, renders, "round_01")
    pdf2, png2 = render_pptx(round_02, renders, "round_02")
    (ROOT / "dist").mkdir(parents=True, exist_ok=True)
    shutil.copy2(pdf2, ROOT / "dist/C01_SEANet_graph_level_v74.pdf")
    shutil.copy2(png2, ROOT / "dist/C01_SEANet_graph_level_v74.preview.png")
    im1 = Image.open(png1).convert("RGB")
    im2 = Image.open(png2).convert("RGB")
    comparison = Image.new("RGB", (im1.width + im2.width, max(im1.height, im2.height)), "white")
    comparison.paste(im1, (0, 0))
    comparison.paste(im2, (im1.width, 0))
    comparison.save(renders / "round_01_vs_round_02.png")

    accepted_output = Path(accepted_output)
    accepted_output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(round_02, accepted_output)

    history = {
        "schema_version": "1.0.0",
        "status": "COMPLETED",
        "case": "C01_SEANet",
        "first_pass": {
            "path": str(first_pass.relative_to(output_dir)),
            "sha256": sha(first_pass),
            "immutable": True,
        },
        "rounds": [
            {
                "round": 1,
                "path": str(round_01.relative_to(output_dir)),
                "sha256": sha(round_01),
                "operation": "set_alignment center -> right on el_0052",
                "accepted": True,
                "rejected": False,
            },
            {
                "round": 2,
                "path": str(round_02.relative_to(output_dir)),
                "base_sha256": sha(round_01),
                "sha256": sha(round_02),
                "operation": "source-grounded structural rebuild from C01-SEANet FigureSpec v7.4",
                "rationale": "Restore the stacked schematic total-graph input, source-like pooling silhouettes, five independent class-output squares, explicit lower-panel excerpt scope and object alt text. Center the revised two-line class label beneath the five-square stack.",
                "accepted": True,
                "rejected": False,
                "figure_spec_diff": str(diff_path.relative_to(output_dir)),
                "quality_audit": str(quality_path.relative_to(output_dir)),
                "render_evidence": [
                    str(png0.relative_to(output_dir)),
                    str(png1.relative_to(output_dir)),
                    str(png2.relative_to(output_dir)),
                    str((renders / "round_01_vs_round_02.png").relative_to(output_dir)),
                ],
            },
        ],
        "accepted_rounds": 2,
        "rejected_rounds": 0,
        "final_path": str(round_02),
        "final_sha256": sha(round_02),
        "human_final_review": "PENDING",
        "office_2016_host_round_trip": "PENDING",
        "scope": "SEANet graph-level excerpt; C01-FBG construction is separate",
    }
    history_path = output_dir / "repair_history.json"
    history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    summary = {
        "case": "C01_SEANet",
        "status": "ROUND_02_REPAIR_EXECUTED_AND_AUDITED",
        "initial_sha256": sha(first_pass),
        "round_01_sha256": sha(round_01),
        "round_02_sha256": sha(round_02),
        "accepted_rounds": 2,
        "rejected_rounds": 0,
        "figure_spec_changes": len(changes),
        "quality": quality,
        "human_final_review": "PENDING",
        "office_2016_host_round_trip": "PENDING",
        "source_limit": "Graph topology remains schematic; this is a lower-panel excerpt, not the complete two-panel graphical abstract.",
    }
    (output_dir / "repair_case_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--accepted-output", type=Path, required=True)
    args = parser.parse_args()
    result = run_case(args.output_dir, args.accepted_output)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
