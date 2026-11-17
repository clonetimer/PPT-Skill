#!/usr/bin/env python3
"""Run FigureAST dual-writer parity against independent-paper generalization figures."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from figure_ast import load_figure_ast
from figure_ast_writers import render_ast
from render_with_libreoffice import render_pptx
from validate_ast_parity import validate
from calibrate_text_fit_against_pdf import calibrate as calibrate_text_fit

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIGURES = ("Mamba_Figure1", "Swin_Figure2")
PROFILE = ROOT / "profiles/renderer/lo_headless_v1.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_figure(figure_name: str, output_root: Path, profile: Path = PROFILE) -> dict:
    spec_path = ROOT / "dist/skill_tests/generalization" / f"{figure_name}.json"
    legacy_pptx = ROOT / "dist/skill_tests/generalization" / f"{figure_name}.pptx"
    if not spec_path.is_file() or not legacy_pptx.is_file():
        raise FileNotFoundError(f"GENERALIZATION_INPUT_MISSING:{figure_name}")

    ast = load_figure_ast(str(spec_path))
    round_trip = ast.to_spec()
    source_spec = json.loads(spec_path.read_text(encoding="utf-8"))
    expected_round_trip = dict(source_spec)
    expected_round_trip.setdefault("id", "unnamed-figure")
    if round_trip != expected_round_trip:
        raise AssertionError(f"AST_SPEC_ROUND_TRIP_MISMATCH:{figure_name}")

    figure_dir = output_root / figure_name
    ast_dir = figure_dir / "ast"
    legacy_render_dir = figure_dir / "legacy_render"
    ast_render_dir = figure_dir / "ast_render"
    ast_dir.mkdir(parents=True, exist_ok=True)

    ast_svg = ast_dir / f"{figure_name}.svg"
    ast_pptx = ast_dir / f"{figure_name}.pptx"
    ast_json = ast_dir / "figure_ast.json"
    render_result = render_ast(
        ast, ast_svg, ast_pptx, root=ROOT, preserve_source_ids=True
    )
    ast_json.write_text(ast.to_json(), encoding="utf-8")

    legacy_record = render_pptx(legacy_pptx, legacy_render_dir, profile_path=profile)
    ast_record = render_pptx(ast_pptx, ast_render_dir, profile_path=profile)
    if len(legacy_record["outputs"]["pages"]) != 1 or len(ast_record["outputs"]["pages"]) != 1:
        raise AssertionError(f"GENERALIZATION_EXPECTED_SINGLE_SLIDE:{figure_name}")

    legacy_png = Path(legacy_record["outputs"]["pages"][0]["path"])
    ast_png = Path(ast_record["outputs"]["pages"][0]["path"])
    diff_png = figure_dir / "legacy_vs_ast_diff.png"
    parity = validate(
        legacy_pptx, ast_pptx, legacy_png, ast_png, diff_png,
        max_mae=1.0, max_changed_ratio=0.005,
    )
    parity_path = figure_dir / "parity.json"
    parity_path.write_text(json.dumps(parity, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    text_calibration = calibrate_text_fit(ast_pptx, Path(ast_record["outputs"]["pdf"]["path"]))
    text_calibration_path = figure_dir / "text_fit_calibration.json"
    text_calibration_path.write_text(
        json.dumps(text_calibration, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    primitive_counts = dict(Counter(node.kind for node in ast.nodes))
    legacy_slide = parity["legacy"]["slides"][0]
    ast_slide = parity["ast"]["slides"][0]
    summary = {
        "figure": figure_name,
        "paper": source_spec.get("meta", {}).get("paper"),
        "status": parity["status"],
        "element_count": len(ast.nodes),
        "primitive_counts": primitive_counts,
        "source_spec_sha256": ast.source_sha256,
        "ast_sha256": ast.ast_sha256,
        "legacy_pptx_sha256": sha256(legacy_pptx),
        "ast_pptx_sha256": sha256(ast_pptx),
        "legacy_png_sha256": sha256(legacy_png),
        "ast_png_sha256": sha256(ast_png),
        "legacy_shape_count": legacy_slide["shape_count"],
        "ast_shape_count": ast_slide["shape_count"],
        "picture_count": ast_slide["pictures"],
        "raster": parity["raster"],
        "issues": parity["issues"],
        "text_fit_calibration": {
            "status": text_calibration["status"],
            "text_shapes": text_calibration["text_shapes"],
            "pdf_text_matches": text_calibration["pdf_text_matches"],
            "missing_text_count": text_calibration["missing_text_count"],
            "rendered_text_outside_frame_count": text_calibration["rendered_text_outside_frame_count"],
            "line_count_mismatch_count": text_calibration["line_count_mismatch_count"],
            "font_metric_unavailable_count": text_calibration["font_metric_unavailable_count"],
            "font_metric_false_negative_overflow_count": text_calibration["font_metric_false_negative_overflow_count"],
        },
        "artifacts": {
            "ast_json": str(ast_json.relative_to(ROOT)),
            "ast_svg": str(ast_svg.relative_to(ROOT)),
            "ast_pptx": str(ast_pptx.relative_to(ROOT)),
            "legacy_render_record": str((legacy_render_dir / "render_record.json").relative_to(ROOT)),
            "ast_render_record": str((ast_render_dir / "render_record.json").relative_to(ROOT)),
            "parity": str(parity_path.relative_to(ROOT)),
            "text_fit_calibration": str(text_calibration_path.relative_to(ROOT)),
            "diff": str(diff_png.relative_to(ROOT)),
        },
        "render_result": render_result,
    }
    (figure_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--figures", nargs="+", default=list(DEFAULT_FIGURES))
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist/ast_generalization")
    parser.add_argument("--profile", type=Path, default=PROFILE)
    args = parser.parse_args()

    output_root = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    profile = args.profile if args.profile.is_absolute() else ROOT / args.profile
    if not profile.is_file():
        raise FileNotFoundError(f"RENDER_PROFILE_NOT_FOUND:{profile}")

    results = [run_figure(name, output_root, profile) for name in args.figures]
    combined = {
        "schema_version": "1.0.0",
        "status": "PASS" if all(item["status"] == "PASS" for item in results) else "FAIL",
        "renderer_profile": str(profile.relative_to(ROOT)),
        "figures": results,
    }
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "summary.json").write_text(
        json.dumps(combined, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "status": combined["status"],
        "figures": [{
            "figure": item["figure"],
            "status": item["status"],
            "elements": item["element_count"],
            "legacy_shapes": item["legacy_shape_count"],
            "ast_shapes": item["ast_shape_count"],
            "raster": item["raster"],
            "issues": item["issues"],
        } for item in results],
    }, ensure_ascii=False, indent=2))
    if combined["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
