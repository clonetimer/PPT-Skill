#!/usr/bin/env python3
"""Execute C01 composite local repair rounds with immutable PPTX and object diffs."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Inches

from build_c01_v74 import make_spec as make_v74_spec
from build_c01_composite_v75 import (
    add_input_graph_icon,
    annotate_accessibility,
    build_spec,
)
from render_figure_spec import render
from validate_c01_composite_v75 import validate as validate_v75

ROOT = Path(__file__).resolve().parents[1]
INITIAL_PPTX = ROOT / "dist/C01_composite_defense_slide_v74.pptx"
FINAL_SPEC = ROOT / "figure_specs/c01/C01_composite_defense_slide_v75.json"
FINAL_SVG = ROOT / "examples/C01_composite_defense_slide_v75.svg"
FINAL_PPTX = ROOT / "dist/C01_composite_defense_slide_v75.pptx"


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def spec_diff(before: dict, after: dict) -> list[dict]:
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


def annotate_generic(path: Path) -> dict:
    prs = Presentation(path)
    if len(prs.slides) != 1:
        raise ValueError("C01_COMPOSITE_REPAIR_EXPECTS_ONE_SLIDE")
    slide = prs.slides[0]
    for index, shape in enumerate(slide.shapes):
        shape.name = f"C01_composite_round1_obj_{index:03d}"
        for node in shape._element.iter():
            if node.tag.endswith("}cNvPr"):
                if shape.has_text_frame and shape.text.strip():
                    alt = "Text label: " + shape.text.replace("\n", "; ")
                elif shape.shape_type == MSO_SHAPE_TYPE.LINE:
                    alt = "Editable connector in the two-panel FBG-SEANet method overview."
                else:
                    alt = "Editable vector object in the two-panel FBG-SEANet method overview."
                node.set("descr", alt)
                break
    prs.save(path)
    return {"shape_count": len(slide.shapes), "alt_text_coverage": 1.0}


def mechanical_audit(path: Path) -> dict:
    prs = Presentation(path)
    slide = prs.slides[0]
    shapes = list(slide.shapes)
    if any(s.shape_type == MSO_SHAPE_TYPE.PICTURE for s in shapes):
        raise AssertionError("RASTERIZED_INTERMEDIATE_NOT_ALLOWED")
    oob = [
        s.name for s in shapes
        if s.left < 0 or s.top < 0
        or s.left + s.width > prs.slide_width
        or s.top + s.height > prs.slide_height
    ]
    if oob:
        raise AssertionError("INTERMEDIATE_OBJECTS_OUT_OF_BOUNDS:" + ",".join(oob))
    texts = [s for s in shapes if s.has_text_frame and s.text.strip()]
    overlaps = []
    for i, a in enumerate(texts):
        for b in texts[i + 1:]:
            iw = max(0, min(a.left + a.width, b.left + b.width) - max(a.left, b.left))
            ih = max(0, min(a.top + a.height, b.top + b.height) - max(a.top, b.top))
            if iw > Inches(0.03) and ih > Inches(0.03):
                overlaps.append({
                    "shape_a":a.name,"shape_b":b.name,
                    "text_a":a.text,"text_b":b.text,
                    "bbox_a":[a.left,a.top,a.width,a.height],
                    "bbox_b":[b.left,b.top,b.width,b.height],
                })
    if overlaps:
        raise AssertionError("INTERMEDIATE_TEXT_OVERLAPS:" + repr(overlaps))
    missing_alt = [s.name for s in shapes if not any(
        node.tag.endswith("}cNvPr") and (node.get("descr") or "").strip()
        for node in s._element.iter()
    )]
    if missing_alt:
        raise AssertionError("INTERMEDIATE_ALT_TEXT_MISSING:" + ",".join(missing_alt))
    return {
        "status": "PASS",
        "pptx_shapes": len(shapes),
        "picture_count": 0,
        "alt_text_coverage": 1.0,
        "text_overlaps": 0,
        "out_of_bounds": 0,
    }


def render_pptx(pptx: Path, output_dir: Path, stem: str) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"ppt-skill-lo-{stem}-") as profile_root:
        result = subprocess.run(
            [
                "libreoffice",
                "-env:UserInstallation=" + Path(profile_root).as_uri(),
                "--headless", "--convert-to", "pdf", "--outdir", str(output_dir), str(pptx),
            ],
            capture_output=True, text=True,
        )
    pdf = output_dir / (pptx.stem + ".pdf")
    if result.returncode != 0 or not pdf.is_file():
        raise RuntimeError("LIBREOFFICE_RENDER_FAILED:" + result.stdout + result.stderr)
    result = subprocess.run(
        ["pdftoppm", "-png", "-r", "120", str(pdf), str(output_dir / stem), "-singlefile"],
        capture_output=True, text=True,
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
    if not INITIAL_PPTX.is_file():
        subprocess.run([sys.executable, str(ROOT / "tools/build_c01_v74.py")], check=True)
    if not INITIAL_PPTX.is_file():
        raise FileNotFoundError("C01_COMPOSITE_V74_INITIAL_PPTX_MISSING")

    rounds_dir = output_dir / "rounds"
    rounds_dir.mkdir(parents=True, exist_ok=True)
    first_pass = rounds_dir / "first_pass.pptx"
    round_01 = rounds_dir / "round_01.pptx"
    round_02 = rounds_dir / "round_02.pptx"
    shutil.copy2(INITIAL_PPTX, first_pass)

    # Round 01: restore four stacked, editable band subgraphs and nine inter-band connectors inside the Input block.
    base_spec = copy.deepcopy(make_v74_spec())
    round_01_spec = copy.deepcopy(base_spec)
    add_input_graph_icon(round_01_spec)
    round_01_spec["id"] = "C01_composite_defense_slide"
    round_01_spec["version"] = "7.4.1"
    round_01_svg = output_dir / "round_01.svg"
    render(round_01_spec, round_01_svg, round_01)
    annotate_generic(round_01)
    round_01_audit = mechanical_audit(round_01)

    # Round 02: add the source's five independent class-output squares and Dense endpoint.
    final_spec = build_spec()
    FINAL_SPEC.parent.mkdir(parents=True, exist_ok=True)
    FINAL_SVG.parent.mkdir(parents=True, exist_ok=True)
    FINAL_PPTX.parent.mkdir(parents=True, exist_ok=True)
    FINAL_SPEC.write_text(json.dumps(final_spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    render(final_spec, FINAL_SVG, FINAL_PPTX)
    final_accessibility = annotate_accessibility(FINAL_PPTX)
    shutil.copy2(FINAL_PPTX, round_02)

    diff_01 = spec_diff(base_spec, round_01_spec)
    diff_02 = spec_diff(round_01_spec, final_spec)
    (output_dir / "round_01_object_diff.json").write_text(
        json.dumps(diff_01, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "round_02_object_diff.json").write_text(
        json.dumps(diff_02, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    final_quality = validate_v75()
    if final_quality.get("status") != "PASS":
        raise RuntimeError("C01_COMPOSITE_V75_QUALITY_AUDIT_FAILED")
    (output_dir / "round_02_quality_audit.json").write_text(
        json.dumps(final_quality, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    subprocess.run(
        [sys.executable, str(ROOT / "tools/audit_pptx.py"), str(FINAL_PPTX), "--strict"],
        check=True,
    )

    renders = output_dir / "renders"
    pdf0, png0 = render_pptx(first_pass, renders, "first_pass")
    pdf1, png1 = render_pptx(round_01, renders, "round_01")
    pdf2, png2 = render_pptx(round_02, renders, "round_02")
    (ROOT / "dist").mkdir(parents=True, exist_ok=True)
    shutil.copy2(pdf2, ROOT / "dist/C01_composite_defense_slide_v75_preview.pdf")
    shutil.copy2(png2, ROOT / "dist/C01_composite_defense_slide_v75_preview.png")

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
        "case": "C01_composite",
        "first_pass": {"path": str(first_pass.relative_to(output_dir)), "sha256": sha(first_pass), "immutable": True},
        "rounds": [
            {
                "round": 1, "path": str(round_01.relative_to(output_dir)), "sha256": sha(round_01),
                "operation": "restore four stacked band subgraphs and nine dashed inter-band connectors inside Input block",
                "object_diff": str((output_dir / "round_01_object_diff.json").relative_to(output_dir)),
                "quality_audit": round_01_audit, "accepted": True, "rejected": False,
            },
            {
                "round": 2, "path": str(round_02.relative_to(output_dir)), "base_sha256": sha(round_01),
                "sha256": sha(round_02),
                "operation": "restore five independent class-output squares, second orange, and Dense-to-class-output route",
                "object_diff": str((output_dir / "round_02_object_diff.json").relative_to(output_dir)),
                "quality_audit": final_quality, "accessibility": final_accessibility,
                "accepted": True, "rejected": False,
            },
        ],
        "accepted_rounds": 2, "rejected_rounds": 0,
        "final_path": str(round_02), "final_sha256": sha(round_02),
        "human_final_review": "PENDING", "office_2016_host_round_trip": "PENDING",
    }
    (output_dir / "repair_history.json").write_text(
        json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    summary = {
        "case": "C01_composite",
        "status": "ROUND_02_REPAIR_EXECUTED_AND_AUDITED",
        "initial_sha256": sha(first_pass), "round_01_sha256": sha(round_01), "round_02_sha256": sha(round_02),
        "accepted_rounds": 2, "rejected_rounds": 0,
        "round_01_spec_changes": len(diff_01), "round_02_spec_changes": len(diff_02),
        "quality": final_quality, "accessibility": final_accessibility,
        "human_final_review": "PENDING", "office_2016_host_round_trip": "PENDING",
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
