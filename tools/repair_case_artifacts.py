"""Reusable immutable repair-case evidence helpers for editable PowerPoint artifacts.

Domain-specific builders still own the scientific repair. This module standardizes
hashing, PPTX object diffs, isolated rendering, and before/after comparison assets.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image
from pptx import Presentation


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rgb(value):
    try:
        return str(value.rgb) if value and value.type else None
    except (AttributeError, TypeError, ValueError):
        return None


def pptx_object_snapshot(path: Path) -> dict:
    """Capture editable objects with stable per-slide object keys and visual attributes."""
    prs = Presentation(path)
    objects = {}
    for slide_index, slide in enumerate(prs.slides, 1):
        for shape_index, shape in enumerate(slide.shapes):
            key = f"{slide_index}:{shape_index}"
            text = shape.text if shape.has_text_frame else None
            runs = []
            if shape.has_text_frame:
                for paragraph_index, paragraph in enumerate(shape.text_frame.paragraphs):
                    for run_index, run in enumerate(paragraph.runs):
                        runs.append({
                            "paragraph": paragraph_index,
                            "run": run_index,
                            "text": run.text,
                            "font_name": run.font.name,
                            "font_size_pt": run.font.size.pt if run.font.size else None,
                            "bold": run.font.bold,
                            "italic": run.font.italic,
                            "color": _rgb(run.font.color),
                        })
            objects[key] = {
                "slide": slide_index,
                "shape_index": shape_index,
                "name": shape.name,
                "type": str(shape.shape_type),
                "left": shape.left,
                "top": shape.top,
                "width": shape.width,
                "height": shape.height,
                "rotation": float(shape.rotation),
                "text": text,
                "font_runs": runs,
                "fill": _rgb(shape.fill.fore_color) if shape.fill.type else None,
                "line": _rgb(shape.line.color) if shape.line.fill.type else None,
            }
    return objects


def pptx_object_diff(before_path: Path, after_path: Path) -> dict:
    before = pptx_object_snapshot(before_path)
    after = pptx_object_snapshot(after_path)
    changes = []
    for key in sorted(set(before) | set(after)):
        if key not in before:
            changes.append({"kind": "added", "key": key, "after": after[key]})
        elif key not in after:
            changes.append({"kind": "removed", "key": key, "before": before[key]})
        else:
            fields = {
                field: {"before": before[key][field], "after": after[key][field]}
                for field in sorted(set(before[key]) | set(after[key]))
                if before[key].get(field) != after[key].get(field)
            }
            if fields:
                changes.append({"kind": "modified", "key": key, "fields": fields})
    return {
        "initial_sha256": sha256_file(before_path),
        "final_sha256": sha256_file(after_path),
        "initial_objects": len(before),
        "final_objects": len(after),
        "added": sum(item["kind"] == "added" for item in changes),
        "removed": sum(item["kind"] == "removed" for item in changes),
        "modified": sum(item["kind"] == "modified" for item in changes),
        "changed_objects": len(changes),
        "changes": changes,
    }


def render_pptx(pptx_path: Path, output_dir: Path, stem: str, dpi: int = 120):
    """Render a PPTX to PDF/PNG without polluting the evidence directory with LO profiles."""
    pptx_path, output_dir = Path(pptx_path), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"ppt-skill-lo-{stem}-") as profile_root:
        result = subprocess.run(
            [
                "libreoffice",
                "-env:UserInstallation=" + Path(profile_root).as_uri(),
                "--headless", "--convert-to", "pdf",
                "--outdir", str(output_dir), str(pptx_path),
            ],
            capture_output=True, text=True,
        )
    pdf_path = output_dir / f"{stem}.pdf"
    if result.returncode != 0 or not pdf_path.is_file():
        raise RuntimeError("LIBREOFFICE_RENDER_FAILED:" + result.stdout + result.stderr)
    prefix = output_dir / stem
    result = subprocess.run(
        ["pdftoppm", "-png", "-r", str(dpi), str(pdf_path), str(prefix)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError("PDF_TO_PNG_FAILED:" + result.stdout + result.stderr)
    pages = sorted(output_dir.glob(f"{stem}-*.png"))
    if not pages:
        raise RuntimeError("PDF_RENDER_CREATED_NO_PAGES")
    return pdf_path, pages


def compare_pngs(before_png: Path, after_png: Path, output_png: Path) -> Path:
    before = Image.open(before_png).convert("RGB")
    after = Image.open(after_png).convert("RGB")
    height = max(before.height, after.height)
    canvas = Image.new("RGB", (before.width + after.width, height), "white")
    canvas.paste(before, (0, 0))
    canvas.paste(after, (before.width, 0))
    output_png = Path(output_png)
    output_png.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_png)
    return output_png


def write_json(path: Path, payload: dict) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
