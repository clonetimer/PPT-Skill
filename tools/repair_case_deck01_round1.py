#!/usr/bin/env python3
"""Execute DECK01 v7.6 local evidence-boundary repair with immutable artifacts."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Inches

from build_deck_benchmark import OUTPUT as FINAL_OUTPUT, build as build_v76
from build_deck_benchmark_v75 import build as build_v75
from repair_case_artifacts import (
    compare_pngs,
    pptx_object_diff,
    render_pptx,
    sha256_file,
    write_json,
)
from scientific_ir import ROOT

ACCEPTED_OUTPUT = ROOT / "dist/accepted_repairs/DECK01_c01_defense_v76.pptx"


def _deck_spec_diff(before_path: Path, after_path: Path) -> list[dict]:
    before = json.loads(Path(before_path).read_text(encoding="utf-8"))
    after = json.loads(Path(after_path).read_text(encoding="utf-8"))
    changes = []

    def walk(path, left, right):
        if isinstance(left, dict) and isinstance(right, dict):
            for key in sorted(set(left) | set(right)):
                if key not in left:
                    changes.append({"path": f"{path}.{key}", "kind": "added", "after": right[key]})
                elif key not in right:
                    changes.append({"path": f"{path}.{key}", "kind": "removed", "before": left[key]})
                else:
                    walk(f"{path}.{key}", left[key], right[key])
        elif isinstance(left, list) and isinstance(right, list):
            if left != right:
                changes.append({"path": path, "kind": "modified", "before": left, "after": right})
        elif left != right:
            changes.append({"path": path, "kind": "modified", "before": left, "after": right})

    walk("deck_spec", before, after)
    return changes


def mechanical_audit(path: Path) -> dict:
    prs = Presentation(path)
    if len(prs.slides) != 3:
        raise AssertionError("DECK01_EXPECTS_THREE_SLIDES")
    picture_count = 0
    out_of_bounds = []
    text_overlaps = []
    slide3 = prs.slides[2]
    text_shapes = [s for s in slide3.shapes if s.has_text_frame and s.text.strip()]
    for slide_index, slide in enumerate(prs.slides, 1):
        for shape in slide.shapes:
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                picture_count += 1
            if (shape.left < 0 or shape.top < 0
                    or shape.left + shape.width > prs.slide_width
                    or shape.top + shape.height > prs.slide_height):
                out_of_bounds.append((slide_index, shape.name))
    for index, a in enumerate(text_shapes):
        for b in text_shapes[index + 1:]:
            iw = max(0, min(a.left + a.width, b.left + b.width) - max(a.left, b.left))
            ih = max(0, min(a.top + a.height, b.top + b.height) - max(a.top, b.top))
            if iw > Inches(.03) and ih > Inches(.03):
                text_overlaps.append((a.name, b.name))
    card_count = sum(1 for s in slide3.shapes if s.name in {"s03_card_1", "s03_card_2", "s03_card_3"})
    if picture_count:
        raise AssertionError("DECK01_UNEXPECTED_RASTERIZED_OBJECTS")
    if out_of_bounds:
        raise AssertionError("DECK01_OBJECTS_OUT_OF_BOUNDS:" + repr(out_of_bounds))
    if text_overlaps:
        raise AssertionError("DECK01_SLIDE3_TEXT_OVERLAPS:" + repr(text_overlaps))
    if card_count != 3:
        raise AssertionError("DECK01_THREE_EVIDENCE_CARDS_REQUIRED")
    return {
        "status": "PASS",
        "slide_count": len(prs.slides),
        "pptx_shapes": sum(len(s.shapes) for s in prs.slides),
        "picture_count": picture_count,
        "slide3_text_boxes": len(text_shapes),
        "slide3_evidence_cards": card_count,
        "text_overlaps": 0,
        "out_of_bounds": 0,
    }


def run_case(
    output_dir: Path,
    accepted_output: Path = ACCEPTED_OUTPUT,
    final_output: Path = FINAL_OUTPUT,
    publish: bool = True,
) -> dict:
    output_dir = Path(output_dir).resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("DECK01_REPAIR_CASE_OUTPUT_DIR_MUST_BE_EMPTY")
    output_dir.mkdir(parents=True, exist_ok=True)
    rounds = output_dir / "rounds"
    rounds.mkdir(parents=True, exist_ok=True)

    first_pass = rounds / "first_pass.pptx"
    round_01 = rounds / "round_01.pptx"
    build_v75(first_pass)
    build_v76(round_01)

    object_diff = pptx_object_diff(first_pass, round_01)
    spec_diff = _deck_spec_diff(
        ROOT / "specs/deck_spec_v75.example.json",
        ROOT / "specs/deck_spec_v76.example.json",
    )
    write_json(output_dir / "round_01_object_diff.json", object_diff)
    write_json(output_dir / "round_01_deck_spec_diff.json", {"changes": spec_diff})

    quality = mechanical_audit(round_01)
    write_json(output_dir / "round_01_quality_audit.json", quality)
    subprocess.run(
        [sys.executable, str(ROOT / "tools/audit_pptx.py"), str(round_01), "--strict"],
        check=True,
    )

    renders = output_dir / "renders"
    pdf0, pages0 = render_pptx(first_pass, renders, "first_pass")
    pdf1, pages1 = render_pptx(round_01, renders, "round_01")
    if len(pages0) != 3 or len(pages1) != 3:
        raise AssertionError("DECK01_REPAIR_REQUIRES_THREE_RENDERED_PAGES")
    comparison = compare_pngs(
        pages0[2], pages1[2], renders / "first_pass_vs_round_01_slide_3.png"
    )

    final_output = Path(final_output)
    accepted_output = Path(accepted_output)
    final_output.parent.mkdir(parents=True, exist_ok=True)
    accepted_output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(round_01, final_output)
    shutil.copy2(round_01, accepted_output)

    dist = ROOT / "dist"
    final_pages = []
    if publish:
        shutil.copy2(pdf1, dist / "DECK01_c01_defense_v76.pdf")
        for index, page in enumerate(pages1, 1):
            destination = dist / f"DECK01_c01_defense_v76_slide_{index}.png"
            shutil.copy2(page, destination)
            final_pages.append(str(destination.relative_to(ROOT)))
    else:
        final_pages = [str(page.relative_to(output_dir)) for page in pages1]

    history = {
        "schema_version": "1.0.0",
        "case": "DECK01",
        "status": "COMPLETED",
        "diagnosis": {
            "confirmed_defect": "The first-pass evidence-boundary slide contained only two vague labels and left most of the slide unused. It did not distinguish source-visible route checks, schematic substitutions, and human review gates.",
            "scope": "Slide 3 only. Problem slide and method slide are retained without content changes.",
            "repair_rationale": "Replace the sparse two-line list with three evidence cards. The card content is sourced from the C01 v7.6 source-correction and QA records; no performance or numerical-adjacency claim is added.",
        },
        "first_pass": {
            "path": str(first_pass.relative_to(output_dir)),
            "sha256": sha256_file(first_pass),
            "immutable": True,
        },
        "rounds": [{
            "round": 1,
            "path": str(round_01.relative_to(output_dir)),
            "sha256": sha256_file(round_01),
            "operation": "re-layout evidence-boundary slide into source-visible, schematic-substitution and pending-human-review cards",
            "accepted": True,
            "rejected": False,
            "object_diff": "round_01_object_diff.json",
            "deck_spec_diff": "round_01_deck_spec_diff.json",
            "quality_audit": "round_01_quality_audit.json",
            "render_evidence": [
                str(pdf0.relative_to(output_dir)),
                *[str(p.relative_to(output_dir)) for p in pages0],
                str(pdf1.relative_to(output_dir)),
                *[str(p.relative_to(output_dir)) for p in pages1],
                str(comparison.relative_to(output_dir)),
            ],
        }],
        "accepted_rounds": 1,
        "rejected_rounds": 0,
        "final_path": str(final_output),
        "final_sha256": sha256_file(final_output),
        "human_final_review": "PENDING",
        "office_2016_host_round_trip": "PENDING",
    }
    write_json(output_dir / "repair_history.json", history)
    summary = {
        "case": "DECK01",
        "status": "ROUND_01_REPAIR_EXECUTED_AND_AUDITED",
        "initial_sha256": sha256_file(first_pass),
        "round_01_sha256": sha256_file(round_01),
        "accepted_rounds": 1,
        "rejected_rounds": 0,
        "pptx_object_changes": object_diff["changed_objects"],
        "deck_spec_changes": len(spec_diff),
        "quality": quality,
        "human_final_review": "PENDING",
        "office_2016_host_round_trip": "PENDING",
        "final_pdf": "dist/DECK01_c01_defense_v76.pdf",
        "final_pages": final_pages,
    }
    write_json(output_dir / "repair_case_summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--accepted-output", type=Path, default=ACCEPTED_OUTPUT)
    parser.add_argument("--final-output", type=Path, default=FINAL_OUTPUT)
    args = parser.parse_args()
    result = run_case(args.output_dir, args.accepted_output, args.final_output)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
