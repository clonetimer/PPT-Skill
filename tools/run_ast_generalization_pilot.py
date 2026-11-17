#!/usr/bin/env python3
"""Run a source-backed, non-blocking FigureAST literature-corpus experiment."""
from __future__ import annotations

import argparse
import hashlib
import json
import traceback
from collections import Counter
from pathlib import Path
from typing import Any

from figure_ast import load_figure_ast
from figure_ast_writers import render_ast
from render_figure_spec import render as render_legacy
from render_with_libreoffice import render_pptx
from validate_ast_parity import validate
from calibrate_text_fit_against_pdf import calibrate as calibrate_text_fit
from audit_figure_spec_text_fit import audit_spec as audit_text_fit_preflight

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "specs/ast_generalization_corpus_v1.json"
PROFILE = ROOT / "profiles/renderer/lo_headless_v1.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repo_path(value: str) -> Path:
    path = (ROOT / value).resolve()
    if path != ROOT and ROOT not in path.parents:
        raise ValueError(f"CORPUS_PATH_ESCAPES_REPOSITORY:{value}")
    return path


def run_figure(entry: dict[str, Any], output_root: Path, profile: Path) -> dict:
    figure_name = entry["id"]
    spec_path = repo_path(entry["figure_spec"])
    if not spec_path.is_file():
        raise FileNotFoundError(f"FIGURE_SPEC_NOT_FOUND:{entry['figure_spec']}")

    source_spec = json.loads(spec_path.read_text(encoding="utf-8"))
    if str(source_spec.get("id", "unnamed-figure")) != figure_name:
        raise AssertionError(f"FIGURE_ID_MISMATCH:{figure_name}")

    ast = load_figure_ast(str(spec_path))
    round_trip = ast.to_spec()
    expected_round_trip = dict(source_spec)
    expected_round_trip.setdefault("id", "unnamed-figure")
    if round_trip != expected_round_trip:
        raise AssertionError(f"AST_SPEC_ROUND_TRIP_MISMATCH:{figure_name}")

    text_preflight = audit_text_fit_preflight(source_spec)

    figure_dir = output_root / figure_name
    legacy_dir = figure_dir / "legacy"
    ast_dir = figure_dir / "ast"
    legacy_render_dir = figure_dir / "legacy_render"
    ast_render_dir = figure_dir / "ast_render"
    for directory in (legacy_dir, ast_dir):
        directory.mkdir(parents=True, exist_ok=True)

    # Rebuild the legacy baseline from the exact same committed FigureSpec.
    # This prevents stale pre-generated PPTX files from contaminating parity.
    legacy_svg = legacy_dir / f"{figure_name}.svg"
    legacy_pptx = legacy_dir / f"{figure_name}.pptx"
    render_legacy(source_spec, legacy_svg, legacy_pptx, preserve_source_ids=True)

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
    parity_path.write_text(
        json.dumps(parity, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    text_preflight_path = figure_dir / "text_fit_preflight.json"
    text_preflight_path.write_text(
        json.dumps(text_preflight, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    text_calibration = calibrate_text_fit(
        ast_pptx, Path(ast_record["outputs"]["pdf"]["path"])
    )
    text_calibration_path = figure_dir / "text_fit_calibration.json"
    text_calibration_path.write_text(
        json.dumps(text_calibration, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    primitive_counts = dict(Counter(node.kind for node in ast.nodes))
    legacy_slide = parity["legacy"]["slides"][0]
    ast_slide = parity["ast"]["slides"][0]
    source_evidence = entry.get("source_evidence", {})
    source_path = source_evidence.get("path")
    source_hash = sha256(repo_path(source_path)) if source_path else None
    summary = {
        "figure": figure_name,
        "paper": entry["paper_title"],
        "figure_label": entry.get("figure_label"),
        "family": entry.get("family"),
        "source_evidence": source_evidence,
        "source_file_sha256_observed": source_hash,
        "asset_substitutions": entry.get("asset_substitutions", []),
        "status": "PASS" if parity["status"] == "PASS" and text_calibration["status"] == "PASS" else "FAIL",
        "parity_status": parity["status"],
        "text_fit_status": text_calibration["status"],
        "text_fit_preflight": {
            "status": text_preflight["status"],
            "text_elements": text_preflight["text_elements"],
            "estimated_overflow_count": text_preflight["estimated_overflow_count"],
            "contrast_fail_count": text_preflight["contrast_fail_count"],
            "elements_with_additional_height": [
                item["element_id"] for item in text_preflight["elements"]
                if item.get("additional_height_needed_pt", 0) > 0
            ],
        },
        "element_count": len(ast.nodes),
        "primitive_counts": primitive_counts,
        "spec_file_sha256": sha256(spec_path),
        "source_spec_sha256": ast.source_sha256,
        "ast_sha256": ast.ast_sha256,
        "legacy_svg_sha256": sha256(legacy_svg),
        "ast_svg_sha256": sha256(ast_svg),
        "legacy_pptx_sha256": sha256(legacy_pptx),
        "ast_pptx_sha256": sha256(ast_pptx),
        "legacy_png_sha256": sha256(legacy_png),
        "ast_png_sha256": sha256(ast_png),
        "legacy_shape_count": legacy_slide["shape_count"],
        "ast_shape_count": ast_slide["shape_count"],
        "legacy_picture_count": legacy_slide["pictures"],
        "ast_picture_count": ast_slide["pictures"],
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
            "missing_texts": [
                item["text"] for item in text_calibration["elements"]
                if item.get("match") == "not_found"
            ],
            "outside_texts": [
                item["text"] for item in text_calibration["elements"]
                if item.get("status") == "TEXT_OUTSIDE_FRAME"
            ],
        },
        "artifacts": {
            "legacy_svg": str(legacy_svg.relative_to(ROOT)),
            "legacy_pptx": str(legacy_pptx.relative_to(ROOT)),
            "ast_json": str(ast_json.relative_to(ROOT)),
            "ast_svg": str(ast_svg.relative_to(ROOT)),
            "ast_pptx": str(ast_pptx.relative_to(ROOT)),
            "legacy_render_record": str((legacy_render_dir / "render_record.json").relative_to(ROOT)),
            "ast_render_record": str((ast_render_dir / "render_record.json").relative_to(ROOT)),
            "parity": str(parity_path.relative_to(ROOT)),
            "text_fit_calibration": str(text_calibration_path.relative_to(ROOT)),
            "text_fit_preflight": str(text_preflight_path.relative_to(ROOT)),
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
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--figures", nargs="+", default=None)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist/ast_generalization")
    parser.add_argument("--profile", type=Path, default=PROFILE)
    args = parser.parse_args()

    manifest_path = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
    output_root = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    profile = args.profile if args.profile.is_absolute() else ROOT / args.profile
    if not manifest_path.is_file():
        raise FileNotFoundError(f"CORPUS_MANIFEST_NOT_FOUND:{manifest_path}")
    if not profile.is_file():
        raise FileNotFoundError(f"RENDER_PROFILE_NOT_FOUND:{profile}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = manifest.get("figures")
    if not isinstance(entries, list) or not entries:
        raise ValueError("CORPUS_MANIFEST_REQUIRES_FIGURES")
    if args.figures:
        requested = set(args.figures)
        known = {entry["id"] for entry in entries}
        unknown = sorted(requested - known)
        if unknown:
            raise ValueError(f"UNKNOWN_CORPUS_FIGURES:{','.join(unknown)}")
        entries = [entry for entry in entries if entry["id"] in requested]

    output_root.mkdir(parents=True, exist_ok=True)
    results = []
    for entry in entries:
        try:
            results.append(run_figure(entry, output_root, profile))
        except Exception as exc:
            figure_name = entry.get("id", "unknown-figure")
            figure_dir = output_root / figure_name
            figure_dir.mkdir(parents=True, exist_ok=True)
            failure = {
                "figure": figure_name,
                "paper": entry.get("paper_title"),
                "family": entry.get("family"),
                "status": "ERROR",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }
            (figure_dir / "failure.json").write_text(
                json.dumps(failure, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            results.append(failure)

    passed = sum(item.get("status") == "PASS" for item in results)
    combined_status = (
        "PASS" if passed == len(results)
        else "PARTIAL" if passed > 0
        else "FAIL"
    )
    combined = {
        "schema_version": manifest.get("schema_version", "1.0.0"),
        "corpus_id": manifest.get("corpus_id"),
        "status": combined_status,
        "experiment_role": "non_blocking_research_experiment",
        "renderer_profile": str(profile.relative_to(ROOT)),
        "figure_count": len(results),
        "passed_count": passed,
        "failed_or_error_count": len(results) - passed,
        "figures": results,
    }
    (output_root / "summary.json").write_text(
        json.dumps(combined, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": combined_status,
        "corpus_id": combined["corpus_id"],
        "passed": passed,
        "total": len(results),
        "figures": [{
            "figure": item["figure"],
            "paper": item.get("paper"),
            "status": item["status"],
            "elements": item.get("element_count"),
            "legacy_shapes": item.get("legacy_shape_count"),
            "ast_shapes": item.get("ast_shape_count"),
            "raster": item.get("raster"),
            "text_fit_status": item.get("text_fit_status"),
            "issues": item.get("issues", [item.get("error")]),
        } for item in results],
    }, ensure_ascii=False, indent=2))
    if combined_status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
