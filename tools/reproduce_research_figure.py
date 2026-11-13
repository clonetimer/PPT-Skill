#!/usr/bin/env python3
"""One entrypoint for evidence-aware editable research-figure production.

The PDF-import route is source-visible; a FigureSpec render is a structured
scientific reinterpretation. Do not conflate their evidence/QA contracts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from audit_office2016_compat import audit_pptx
from figure_first_pass_gate import (
    source_profile, evaluate, candidate_profile, _export_with_libreoffice,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_pipeline(source_pdf: Path, destination: Path, *, mode: str = "import",
                 figure_spec: Path | None = None, render_host: str = "auto") -> dict:
    source_pdf = source_pdf.resolve()
    destination = destination.resolve()
    if not source_pdf.is_file():
        raise FileNotFoundError(f"Source PDF missing: {source_pdf}")
    if mode not in ("import", "figurespec"):
        raise ValueError("mode must be import or figurespec")
    if mode == "figurespec" and (figure_spec is None or not figure_spec.is_file()):
        raise ValueError("FigureSpec mode requires an existing --figure-spec")
    if render_host not in ("auto", "none"):
        raise ValueError("render_host must be auto or none")
    destination.mkdir(parents=True, exist_ok=True)
    source_info = source_profile(source_pdf)
    (destination/"source_preflight.json").write_text(
        json.dumps(source_info, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    candidate = destination/"candidate_editable.pptx"
    if mode == "import":
        from pdf_figure_import import convert_pdf_page
        importer = convert_pdf_page(source_pdf, candidate)
        (destination/"import_report.json").write_text(
            json.dumps(importer, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    else:
        renderer = Path(__file__).with_name("render_figure_spec.py")
        if not renderer.is_file():
            raise FileNotFoundError(f"FigureSpec renderer missing: {renderer}")
        command = [
            sys.executable, str(renderer), str(figure_spec.resolve()),
            "--svg", str(destination/"candidate.svg"), "--pptx", str(candidate)
        ]
        subprocess.run(command, check=True)
    pdf = None
    if render_host == "auto":
        pdf = _export_with_libreoffice(candidate, destination/"rendered")
    preview = destination/"source_candidate_diff.png" if pdf else None
    if mode == "import":
        quality = evaluate(source_pdf, candidate, exported_pdf=pdf, preview=preview)
    else:
        # Source text parity is NOT expected for an intentionally re-laid-out
        # FigureSpec; no false editable-PDF import audit is performed here.
        quality = {
            "status": "NEEDS_REVIEW",
            "source": source_info,
            "candidate": candidate_profile(candidate),
            "structure": None, "visual": None,
            "blockers": ["MANUAL_SOURCE_TO_FIGURESPEC_SEMANTIC_MAPPING_REQUIRED"],
            "scientific_release_approval": False,
            "office2016_host_verified": False,
        }
    office = audit_pptx(candidate)
    (destination/"office2016_ooxml_preflight.json").write_text(
        json.dumps(office, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    status = quality["status"]
    if office["status"] != "PASS":
        status = "FAIL"
    elif status == "TECHNICAL_PASS" and office.get("warnings"):
        status = "NEEDS_REVIEW"
    manifest = {
        "schema_version": 1, "mode": mode, "status": status,
        "source": {"path": str(source_pdf), "sha256": sha256(source_pdf)},
        "candidate": {"path": str(candidate), "sha256": sha256(candidate)},
        "figure_spec": ({
            "path": str(figure_spec.resolve()), "sha256": sha256(figure_spec)
        } if figure_spec else None),
        "rendered_pdf": ({
            "path": str(pdf), "sha256": sha256(pdf)
        } if pdf else None),
        "quality_status": quality["status"],
        "quality_blockers": quality.get("blockers", []),
        "office_ooxml_status": office["status"],
        "office_warnings": office.get("warnings", []),
        "scientific_review": "required",
        "office2016_host_test": "not run",
        "final_release_approved": False,
        "evidence_class": (
            "source-visible imported object reconstruction" if mode == "import"
            else "FigureSpec science-grounded reinterpretation"
        ),
    }
    for filename, obj in (
        ("quality_report.json", quality),
        ("delivery_manifest.json", manifest),
    ):
        (destination/filename).write_text(
            json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_pdf", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=["import", "figurespec"], default="import")
    parser.add_argument("--figure-spec", type=Path)
    parser.add_argument("--render-host", choices=["auto", "none"], default="auto")
    args = parser.parse_args()
    result = run_pipeline(
        args.source_pdf, args.output, mode=args.mode,
        figure_spec=args.figure_spec, render_host=args.render_host,
    )
    print(json.dumps({
        "status": result["status"],
        "manifest": str(args.output/"delivery_manifest.json")
    }, ensure_ascii=False))
    if result["status"] == "FAIL":
        sys.exit(1)


if __name__ == "__main__":
    main()
