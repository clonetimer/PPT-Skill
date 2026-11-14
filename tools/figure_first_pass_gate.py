#!/usr/bin/env python3
"""Source-aware first-pass quality gate for author PDF -> native PPTX figures.

This preflight catches predictable failure families *before* a generated picture
can be misreported as accepted. Scientific review and Office 2016 host tests
remain independent release requirements.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unicodedata

import fitz
import numpy as np
from PIL import Image, ImageChops, ImageOps
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from pdf_ellipse_recognition import ellipse_bounds
from audit_text_geometry import audit_text_geometry
from source_figure_crop import apply_figure_region, drawable_intersects_region


def _bad_glyphs(s: str) -> list[str]:
    return [f"U+{ord(c):04X}" for c in s
            if c == "\ufffd" or unicodedata.category(c) in ("Co", "Cs")]


def source_profile(source: Path, *, page: int = 0,
                   figure_region: tuple[float, float, float, float] | None = None) -> dict:
    """Freeze source evidence before candidate generation; do not infer meaning."""
    if page < 0:
        raise ValueError("INVALID_SOURCE_PAGE_INDEX: zero-based page index must be non-negative")
    with fitz.open(source) as doc:
        p = doc[page]
        original_page_pt = [round(p.rect.width, 3), round(p.rect.height, 3)]
        selected_region = apply_figure_region(p, figure_region)
        drawings = [d for d in p.get_drawings() if drawable_intersects_region(d, p.rect)]
        extended = p.get_drawings(extended=True)
        spans = [span for block in p.get_text("dict")["blocks"]
                 for line in block.get("lines", []) for span in line["spans"]
                 if span["text"].strip()]
        fonts = Counter(str(s.get("font", "")) for s in spans)
        glyphs = Counter(c for s in spans for c in _bad_glyphs(s["text"]))
        unusual_strokes = sum(1 for d in drawings if (d.get("width") or 0) > 1584)
        clip_count = sum(1 for d in extended if d["type"] == "clip")
        ellipse_count = sum(bool(ellipse_bounds(d)) for d in drawings)
        images = [b for b in p.get_text("dict")["blocks"] if b["type"] == 1]
        math_fonts = {name: n for name, n in fonts.items()
                      if any(t in name.lower() for t in
                             ("math", "symbol", "stix", "cmmi", "cmsy", "msam"))}
        risks = []
        def flag(code, severity, count, guidance):
            if count:
                risks.append(dict(code=code, severity=severity, count=int(count), guidance=guidance))
        flag("SUSPICIOUS_UNICODE", "high", sum(glyphs.values()),
             "Freeze formula transcription against the paper source; do not trust PDF ToUnicode blindly")
        flag("MATH_FONT", "medium", sum(math_fonts.values()),
             "Inspect exported glyphs in PowerPoint, especially superscripts, Greek and operators")
        flag("UNREPRESENTABLE_STROKE", "high", unusual_strokes,
             "Do not silently omit a visible path; verify clipping and source appearance")
        flag("CLIPPED_PLOTS", "medium", clip_count,
             "Compare every chart panel after export; rectangular scissor may not preserve pattern fills")
        flag("DENSE_VECTORS", "medium", 1 if len(drawings) > 1000 else 0,
             "Check lines, legends, pattern fills and source paint order in each figure panel")
        flag("TINY_LABELS", "medium", sum(s["size"] < 6 for s in spans),
             "Inspect at final intended size, not just the high-resolution preview")
        flag("RASTER_ONLY", "high", int(not drawings and bool(images)),
             "A raster-only figure cannot be assumed to have editable scientific primitives")
        return {
            "source": source.name,
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "page_index": page,
            "page_pt": [round(p.rect.width, 3), round(p.rect.height, 3)],
            "original_page_pt": original_page_pt,
            "figure_region_pt": selected_region,
            "source_drawings": len(drawings),
            "source_text_spans": len(spans),
            "source_pictures": len(images),
            "clipped_paths": clip_count,
            "recognizable_source_ellipses": ellipse_count,
            "font_families": dict(fonts),
            "suspicious_unicode": dict(glyphs),
            "risk_flags": risks,
            "requires_human_scientific_review": True,
        }


def candidate_profile(pptx_path: Path) -> dict:
    deck = Presentation(pptx_path)
    if len(deck.slides) != 1:
        raise ValueError("A figure candidate must occupy exactly one PPTX slide")
    slide = deck.slides[0]
    vector_types = (MSO_SHAPE_TYPE.LINE, MSO_SHAPE_TYPE.FREEFORM,
                    MSO_SHAPE_TYPE.AUTO_SHAPE)
    vector = [s for s in slide.shapes if s.shape_type in vector_types]
    pics = [s for s in slide.shapes if s.shape_type == MSO_SHAPE_TYPE.PICTURE]
    texts = [s for s in slide.shapes if s.has_text_frame and s.text.strip()]
    full_page = sum(s.width >= deck.slide_width * .9 and
                    s.height >= deck.slide_height * .9 for s in pics)
    out_of_bounds = sum(s.left < -9144 or s.top < -9144 or
                        s.left+s.width > deck.slide_width + 9144 or
                        s.top+s.height > deck.slide_height + 9144 for s in slide.shapes)
    return dict(shape_count=len(slide.shapes), native_vectors=len(vector), text_objects=len(texts),
                picture_objects=len(pics), full_page_pictures=full_page,
                out_of_bounds=out_of_bounds,
                slide_pt=[round(deck.slide_width.pt, 3), round(deck.slide_height.pt, 3)])


def _tile_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """SSIM-style single-window triage, not certified perceptual fidelity."""
    x, y = a.astype(np.float64)/255, b.astype(np.float64)/255
    mx, my = float(x.mean()), float(y.mean())
    vx, vy = float(x.var()), float(y.var())
    cov = float(((x-mx)*(y-my)).mean())
    c1, c2 = .01**2, .03**2
    return float(((2*mx*my+c1)*(2*cov+c2))/((mx*mx+my*my+c1)*(vx+vy+c2)))


def compare_rendered_pages(source_pdf: Path, candidate_pdf: Path,
                           *, dpi: int = 110, grid: int = 4,
                           preview: Path | None = None,
                           source_page_index: int = 0,
                           source_region: tuple[float, float, float, float] | None = None,
                           candidate_page_index: int = 0) -> dict:
    """Compare final PDF-exported appearance; identify weak spatial tiles."""
    def raster(pdf, page_index, region=None):
        with fitz.open(pdf) as doc:
            if page_index < 0 or page_index >= len(doc):
                raise IndexError(f"page index {page_index} is outside {pdf.name}")
            page = doc[page_index]
            apply_figure_region(page, region)
            pix = page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72), alpha=False)
            return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    src, dst = raster(source_pdf, source_page_index, source_region), raster(candidate_pdf, candidate_page_index)
    if src.size != dst.size:
        if abs(src.width/src.height - dst.width/dst.height) > .003:
            raise ValueError("Source and candidate page aspect ratios differ")
        dst = dst.resize(src.size, Image.Resampling.LANCZOS)
    a = np.asarray(ImageOps.grayscale(src))
    b = np.asarray(ImageOps.grayscale(dst))
    rows = []
    h, w = a.shape
    for iy in range(grid):
        for ix in range(grid):
            x0, x1 = int(ix*w/grid), int((ix+1)*w/grid)
            y0, y1 = int(iy*h/grid), int((iy+1)*h/grid)
            aa, bb = a[y0:y1,x0:x1], b[y0:y1,x0:x1]
            rows.append(dict(row=iy,col=ix,
                             similarity=round(_tile_similarity(aa,bb),4),
                             mean_abs_difference=round(float(np.abs(aa.astype(float)-bb).mean())/255,4)))
    global_sim = _tile_similarity(a,b)
    worst = sorted(rows,key=lambda t:t["similarity"])[:min(5,len(rows))]
    if preview is not None:
        preview.parent.mkdir(parents=True, exist_ok=True)
        composite = Image.new("RGB", (src.width*3,src.height), "white")
        composite.paste(src,(0,0))
        composite.paste(dst,(src.width,0))
        composite.paste(ImageOps.autocontrast(ImageChops.difference(src,dst)),(2*src.width,0))
        composite.save(preview)
    return {
        "renderer": "PDF-export comparison, not Office 2016 host certification",
        "source_region_pt": [float(x) for x in source_region] if source_region is not None else None,
        "dpi": dpi, "grid": grid,
        "global_similarity": round(global_sim,4),
        "mean_abs_difference": round(float(np.abs(a.astype(float)-b).mean())/255,4),
        "worst_tiles": worst,
        "below_0_70_tiles": sum(r["similarity"] < .70 for r in rows),
        "requires_visual_review": global_sim < .88 or any(r["similarity"] < .70 for r in rows),
    }


def _export_with_libreoffice(pptx: Path, destination: Path) -> Path | None:
    import shutil
    binary = shutil.which("libreoffice") or shutil.which("soffice")
    if binary is None:
        return None
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="lo-profile-") as prof:
        command = [binary, f"-env:UserInstallation=file://{prof}", "--headless",
                   "--convert-to", "pdf", "--outdir", str(destination), str(pptx)]
        proc = subprocess.run(command, capture_output=True, text=True, timeout=120)
        candidate = destination/(pptx.stem + ".pdf")
        if proc.returncode or not candidate.exists():
            raise RuntimeError(f"LibreOffice PDF export failed: {proc.stderr[:600]}")
        return candidate


def evaluate(source: Path, candidate: Path, *, exported_pdf: Path | None = None,
             preview: Path | None = None) -> dict:
    src = source_profile(source)
    cand = candidate_profile(candidate)
    from audit_imported_pdf_figure import audit_figure
    struct = audit_figure(source,candidate)
    text_geometry = audit_text_geometry(source, candidate)
    blockers = []
    if struct["status"] != "PASS":
        blockers.append("SOURCE_STRUCTURE_MISMATCH")
    if text_geometry["status"] == "FAIL":
        blockers.append("TEXT_GEOMETRY_FAILURE")
    elif text_geometry["status"] == "NEEDS_REVIEW":
        blockers.append("TEXT_GLYPH_REVIEW")
    if cand["full_page_pictures"]:
        blockers.append("FLATTENED_FULL_FIGURE")
    if cand["out_of_bounds"]:
        blockers.append("OUT_OF_BOUNDS_OBJECTS")
    if src["risk_flags"]:
        blockers.append("SOURCE_RISK_FLAGS_REQUIRE_REVIEW")
    visual = compare_rendered_pages(source,exported_pdf,preview=preview) if exported_pdf else None
    if visual is not None and visual["requires_visual_review"]:
        blockers.append("VISUAL_DISCREPANCY")
    status = "FAIL" if (struct["status"] != "PASS" or cand["full_page_pictures"] or
                         cand["out_of_bounds"] or text_geometry["status"] == "FAIL") else \
             "NEEDS_REVIEW" if blockers or visual is None else "TECHNICAL_PASS"
    return dict(status=status,source=src,candidate=cand,structure=struct,
                text_geometry=text_geometry,visual=visual,blockers=blockers,
                scientific_release_approval=False,office2016_host_verified=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_pdf",type=Path)
    parser.add_argument("--pptx",type=Path,required=True)
    parser.add_argument("--report",type=Path,required=True)
    parser.add_argument("--exported-pdf",type=Path)
    parser.add_argument("--auto-export",action="store_true")
    parser.add_argument("--preview",type=Path)
    parser.add_argument("--inspect-only",action="store_true")
    args=parser.parse_args()
    if args.inspect_only:
        result={"status":"PREFLIGHT_ONLY","source":source_profile(args.source_pdf)}
    else:
        if not args.pptx.exists():
            from pdf_figure_import import convert_pdf_page
            args.pptx.parent.mkdir(parents=True,exist_ok=True)
            convert_pdf_page(args.source_pdf,args.pptx)
        pdf=args.exported_pdf
        if pdf is None and args.auto_export:
            pdf=_export_with_libreoffice(args.pptx,args.report.parent/"pdf_export")
        result=evaluate(args.source_pdf,args.pptx,exported_pdf=pdf,preview=args.preview)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"status":result["status"],"report":str(args.report),
                      "blockers":result.get("blockers",[])},ensure_ascii=False))
    if result["status"]=="FAIL":
        raise SystemExit(1)


if __name__=="__main__":
    main()
