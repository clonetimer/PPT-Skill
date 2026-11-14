#!/usr/bin/env python3
"""Evidence-aware, fail-closed source-PDF / FigureSpec to editable PPTX pipeline."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from audit_office2016_compat import audit_pptx
from audit_figure_spec import audit_figure_spec_semantics, audit_figurespec_output
from figure_first_pass_gate import (
    source_profile, candidate_profile, compare_rendered_pages,
    _export_with_libreoffice,
)
from reproduction_release_gate import classify_release
from extract_source_layout import extract_source_layout


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _empty_candidate() -> dict:
    return {
        "shape_count": 0, "native_vectors": 0, "text_objects": 0,
        "picture_objects": 0, "full_page_pictures": 0, "out_of_bounds": 0,
        "slide_pt": [0.0, 0.0],
    }


def _clear_previous_outputs(destination: Path) -> None:
    for name in (
        "candidate_editable.pptx", "candidate.svg", "source_preflight.json", "source_layout.json",
        "import_report.json", "semantic_audit.json", "structure_audit.json",
        "text_geometry_audit.json", "visual_audit.json",
        "office2016_ooxml_preflight.json", "quality_report.json",
        "delivery_manifest.json", "pipeline_error.json",
    ):
        target = destination / name
        if target.is_file():
            target.unlink()
    rendered = destination / "rendered"
    if rendered.exists():
        shutil.rmtree(rendered)


def run_pipeline(source_pdf: Path, destination: Path, *, mode: str = "import",
                 figure_spec: Path | None = None, render_host: str = "auto",
                 approvals: dict | None = None, require_native: bool = True,
                 require_office_host: bool = True,
                 max_drawings: int = 10000,
                 max_source_segments: int = 100000,
                 max_vertices: int = 250000,
                 max_seconds: float = 60.0,
                 page_index: int = 0,
                 figure_region: tuple[float, float, float, float] | None = None) -> dict:
    source_pdf = Path(source_pdf).resolve()
    destination = Path(destination).resolve()
    if not source_pdf.is_file():
        raise FileNotFoundError(f"Source PDF missing: {source_pdf}")
    if mode not in ("import", "figurespec"):
        raise ValueError("mode must be import or figurespec")
    if mode == "figurespec" and (figure_spec is None or not Path(figure_spec).is_file()):
        raise ValueError("FigureSpec mode requires an existing --figure-spec")
    if render_host not in ("auto", "none"):
        raise ValueError("render_host must be auto or none")
    if min(max_drawings, max_source_segments, max_vertices) <= 0 or max_seconds <= 0:
        raise ValueError("All PDF import resource budgets must be positive")

    destination.mkdir(parents=True, exist_ok=True)
    _clear_previous_outputs(destination)
    figure_spec = Path(figure_spec).resolve() if figure_spec else None
    candidate = destination / "candidate_editable.pptx"
    source_info = {}
    source_layout = {}
    source_layout_error = None
    import_report = {}
    semantic_audit = None
    structure = None
    text_geometry = None
    visual = None
    office = {"status": "FAIL", "failures": ["CANDIDATE_NOT_CREATED"], "warnings": []}
    candidate_info = _empty_candidate()
    error = None
    rendered_pdf = None
    render_error = None

    try:
        source_info = source_profile(source_pdf, page=page_index)
        _write_json(destination / "source_preflight.json", source_info)
        try:
            source_layout = extract_source_layout(
                source_pdf, page_index=page_index, figure_region=figure_region
            )
            _write_json(destination / "source_layout.json", source_layout)
        except Exception as exc:
            source_layout_error = f"{type(exc).__name__}: {exc}"
    except Exception as exc:
        error = f"SOURCE_PREFLIGHT_ERROR: {type(exc).__name__}: {exc}"

    if error is None:
        try:
            if mode == "import":
                from pdf_figure_import import convert_pdf_page
                import_report = convert_pdf_page(
                    source_pdf, candidate, page_index=page_index,
                    max_drawings=max_drawings,
                    max_source_segments=max_source_segments,
                    max_vertices=max_vertices,
                    max_seconds=max_seconds,
                )
                _write_json(destination / "import_report.json", import_report)
            else:
                renderer = Path(__file__).with_name("render_figure_spec.py")
                command = [
                    sys.executable, str(renderer), str(figure_spec),
                    "--svg", str(destination / "candidate.svg"),
                    "--pptx", str(candidate),
                ]
                subprocess.run(command, check=True, capture_output=True, text=True, timeout=180)
                semantic_audit = audit_figure_spec_semantics(figure_spec)
                _write_json(destination / "semantic_audit.json", semantic_audit)
                output_audits = audit_figurespec_output(figure_spec, candidate)
                structure = output_audits["structure"]
                text_geometry = output_audits["text_geometry"]
                _write_json(destination / "structure_audit.json", structure)
                _write_json(destination / "text_geometry_audit.json", text_geometry)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            _write_json(destination / "pipeline_error.json", {
                "error": error, "route": mode,
                "source_sha256": sha256(source_pdf),
            })

    if candidate.is_file():
        try:
            candidate_info = candidate_profile(candidate)
        except Exception as exc:
            error = error or f"CANDIDATE_PROFILE_ERROR: {type(exc).__name__}: {exc}"
            candidate_info = _empty_candidate()
        try:
            office = audit_pptx(candidate)
        except Exception as exc:
            office = {"status": "FAIL", "failures": [f"{type(exc).__name__}: {exc}"], "warnings": []}
        _write_json(destination / "office2016_ooxml_preflight.json", office)

        if mode == "import" and error is None:
            try:
                from audit_imported_pdf_figure import audit_figure
                from audit_text_geometry import audit_text_geometry
                structure = audit_figure(source_pdf, candidate, page_index=page_index)
                text_geometry = audit_text_geometry(source_pdf, candidate, page_index=page_index)
                _write_json(destination / "structure_audit.json", structure)
                _write_json(destination / "text_geometry_audit.json", text_geometry)
            except Exception as exc:
                error = f"IMPORT_AUDIT_ERROR: {type(exc).__name__}: {exc}"

        if render_host == "auto" and error is None:
            try:
                rendered_pdf = _export_with_libreoffice(candidate, destination / "rendered")
                if rendered_pdf is None:
                    render_error = "NO_SUPPORTED_PDF_RENDERER"
                elif mode == "import":
                    visual = compare_rendered_pages(
                        source_pdf, rendered_pdf,
                        preview=destination / "source_candidate_diff.png",
                        source_page_index=page_index,
                        candidate_page_index=0,
                    )
                    visual.update({
                        "status": "PASS",
                        "evidence_type": "source_comparison",
                        "renderer": "LibreOffice PDF export",
                        "rendered_pdf_sha256": sha256(rendered_pdf),
                    })
                else:
                    # FigureSpec is a scientific reinterpretation and may be
                    # intentionally re-laid-out; source SSIM is not its fidelity
                    # contract. Rendering success is technical evidence only.
                    visual = {
                        "status": "PASS",
                        "evidence_type": "candidate_render",
                        "renderer": "LibreOffice PDF export",
                        "rendered_pdf_sha256": sha256(rendered_pdf),
                        "requires_visual_review": False,
                        "comparison": "not_applicable_for_relaid_out_figurespec",
                    }
                _write_json(destination / "visual_audit.json", visual)
            except Exception as exc:
                render_error = f"{type(exc).__name__}: {exc}"
        elif render_host == "none":
            render_error = "RENDER_HOST_DISABLED"

    release = classify_release(
        route=mode,
        candidate=candidate_info,
        import_report=import_report,
        structure=structure,
        text_geometry=text_geometry,
        visual=visual,
        office=office if candidate.is_file() else None,
        semantic_audit=semantic_audit,
        approvals=approvals,
        source_risks=(
            list(source_info.get("risk_flags", [])) +
            ([{"code": "SOURCE_LAYOUT_EXTRACTION_FAILED", "severity": "high"}]
             if source_layout_error else [])
        ),
        error=error,
        require_native=require_native,
        require_office_host=require_office_host,
    )

    manifest = {
        "schema_version": 2,
        "route": mode,
        "status": release["status"],
        "full_release_accepted": release["full_accepted"],
        "blockers": release["blockers"],
        "pending_approvals": release["pending_approvals"],
        "reconstruction_class": (
            import_report.get("reconstruction_class") if mode == "import"
            else "figurespec_science_grounded_reinterpretation"
        ),
        "source": {"path": str(source_pdf), "sha256": sha256(source_pdf),
                   "page_index": page_index},
        "source_layout": ({
            "path": str(destination / "source_layout.json"),
            "sha256": sha256(destination / "source_layout.json"),
            "panel_detection": source_layout.get("panel_detection"),
            "layout_element_count": len(source_layout.get("layout_elements", [])),
            "edge_candidate_count": len(source_layout.get("edge_candidates", [])),
            "image_asset_count": len(source_layout.get("image_assets", [])),
        } if source_layout else None),
        "source_layout_error": source_layout_error,
        "candidate": ({
            "path": str(candidate), "sha256": sha256(candidate),
            **candidate_info,
        } if candidate.is_file() else None),
        "figure_spec": ({
            "path": str(figure_spec), "sha256": sha256(figure_spec),
        } if figure_spec else None),
        "rendered_pdf": ({
            "path": str(rendered_pdf), "sha256": sha256(rendered_pdf),
        } if rendered_pdf and rendered_pdf.is_file() else None),
        "reports": {
            "source_preflight": source_info,
            "import": import_report or None,
            "structure": structure,
            "text_geometry": text_geometry,
            "semantic": semantic_audit,
            "visual": visual,
            "office_ooxml": office if candidate.is_file() else None,
        },
        "error": error,
        "render_error": render_error,
        "approvals": approvals or {},
        "office2016_host_test": "not run",
        "scientific_review": "required unless explicitly approved",
        "visual_review": "required unless explicitly approved",
        "rights_review": "required unless explicitly cleared",
        "final_release_approved": release["full_accepted"],
        "evidence_class": (
            "source-visible imported object reconstruction" if mode == "import"
            else "FigureSpec science-grounded reinterpretation"
        ),
    }
    _write_json(destination / "quality_report.json", release)
    _write_json(destination / "delivery_manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_pdf", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=["import", "figurespec"], default="import")
    parser.add_argument("--figure-spec", type=Path)
    parser.add_argument("--render-host", choices=["auto", "none"], default="auto")
    parser.add_argument("--approvals-json", type=Path,
                        help="explicit human approval record; never inferred by automation")
    parser.add_argument("--allow-source-picture-only", action="store_true",
                        help="report SOURCE_PICTURE_ONLY instead of rejecting non-native recovery")
    parser.add_argument("--no-require-office-host", action="store_true",
                        help="disable the PowerPoint host approval gate for non-release diagnostics")
    parser.add_argument("--max-drawings", type=int, default=10000)
    parser.add_argument("--max-source-segments", type=int, default=100000)
    parser.add_argument("--max-vertices", type=int, default=250000)
    parser.add_argument("--max-seconds", type=float, default=60.0)
    parser.add_argument("--page", type=int, default=1, help="1-based source PDF page")
    parser.add_argument("--region", type=float, nargs=4, metavar=("X0", "Y0", "X1", "Y1"),
                        help="optional figure crop in PDF points")
    args = parser.parse_args()
    approvals = json.loads(args.approvals_json.read_text(encoding="utf-8")) if args.approvals_json else None
    result = run_pipeline(
        args.source_pdf, args.output, mode=args.mode,
        figure_spec=args.figure_spec, render_host=args.render_host,
        approvals=approvals, require_native=not args.allow_source_picture_only,
        require_office_host=not args.no_require_office_host,
        max_drawings=args.max_drawings,
        max_source_segments=args.max_source_segments,
        max_vertices=args.max_vertices,
        max_seconds=args.max_seconds,
        page_index=args.page - 1,
        figure_region=tuple(args.region) if args.region else None,
    )
    print(json.dumps({
        "status": result["status"],
        "full_release_accepted": result["full_release_accepted"],
        "manifest": str(args.output / "delivery_manifest.json"),
        "blockers": result["blockers"],
        "pending_approvals": result["pending_approvals"],
    }, ensure_ascii=False))
    if result["status"] in {"STRUCTURE_FAIL", "UNSUPPORTED_SOURCE", "RESOURCE_LIMIT"}:
        sys.exit(1)
    if result["status"] != "FULL_ACCEPTED":
        sys.exit(2)


if __name__ == "__main__":
    main()
