#!/usr/bin/env python3
"""Audit one reconstructed slide for editability, exact text, and geometry."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from audit_pptx import audit as audit_pptx


def _normalise(value: str) -> str:
    return " ".join(str(value or "").split()).casefold()


def _full_slide_picture(shape, slide_width: int, slide_height: int) -> bool:
    tolerance = 1000  # EMU; allows only sub-pixel placement noise.
    return (
        shape.shape_type == MSO_SHAPE_TYPE.PICTURE
        and shape.left <= tolerance
        and shape.top <= tolerance
        and shape.width >= slide_width - tolerance
        and shape.height >= slide_height - tolerance
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_reconstruction(pptx_path: Path, slide_index: int,
                           required_text: list[str]) -> tuple[dict, dict]:
    deck = Presentation(str(pptx_path))
    if slide_index < 1 or slide_index > len(deck.slides):
        raise ValueError(f"SLIDE_INDEX_OUT_OF_RANGE:{slide_index}")
    slide = deck.slides[slide_index - 1]
    shapes = list(slide.shapes)
    text_shapes = [
        shape for shape in shapes
        if getattr(shape, "has_text_frame", False) and shape.text.strip()
    ]
    visible_text = _normalise("\n".join(shape.text for shape in text_shapes))
    missing = [value for value in required_text if _normalise(value) not in visible_text]
    full_slide_images = sum(
        _full_slide_picture(shape, deck.slide_width, deck.slide_height) for shape in shapes
    )
    inventory = {
        "native_text_shapes": len(text_shapes),
        "native_shape_objects": sum(shape.shape_type != MSO_SHAPE_TYPE.PICTURE for shape in shapes),
        "native_connectors": sum(shape.shape_type == MSO_SHAPE_TYPE.LINE for shape in shapes),
        "native_charts": sum(shape.shape_type == MSO_SHAPE_TYPE.CHART for shape in shapes),
        "picture_objects": sum(shape.shape_type == MSO_SHAPE_TYPE.PICTURE for shape in shapes),
        "full_slide_image_backgrounds": full_slide_images
    }
    layout_audit = audit_pptx(pptx_path)["slides"][slide_index - 1]
    coverage = (len(required_text) - len(missing)) / len(required_text) if required_text else 1.0
    failures = []
    if layout_audit["out_of_bounds"]:
        failures.append("OBJECTS_OUT_OF_BOUNDS")
    if layout_audit["text_box_overlaps"]:
        failures.append("TEXT_BOX_OVERLAPS")
    if full_slide_images:
        failures.append("FULL_SLIDE_RASTER_BACKGROUND")
    if missing:
        failures.append("REQUIRED_TEXT_MISSING")
    if not text_shapes:
        failures.append("NO_NATIVE_TEXT_OBJECTS")
    if inventory["native_shape_objects"] <= len(text_shapes):
        failures.append("NO_NATIVE_GRAPHIC_OBJECTS")
    audit = {
        "status": "pass" if not failures else "fail",
        "out_of_bounds": layout_audit["out_of_bounds"],
        "text_box_overlaps": layout_audit["text_box_overlaps"],
        "full_slide_image_backgrounds": full_slide_images,
        "editable_text_coverage": round(coverage, 6),
        "missing_text": missing,
        "office_2016_roundtrip": "pending",
        "failures": failures,
        "office_2016_evidence": None
    }
    return inventory, audit


def audit_manifest(manifest_path: Path, repository_root: Path | None = None) -> dict:
    manifest_path = Path(manifest_path).resolve()
    root = Path(repository_root).resolve() if repository_root else Path(__file__).resolve().parents[1]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    stage_a = manifest["stage_a"]
    stage_b = manifest["stage_b"]
    if stage_a["status"] not in {"approved", "locked"} or not stage_a.get("target_image"):
        raise ValueError("STAGE_A_IMAGE_NOT_APPROVED")
    if stage_b["status"] not in {"reconstructed", "audited", "accepted"}:
        raise ValueError("STAGE_B_PPTX_NOT_AVAILABLE")
    target = (root / stage_a["target_image"]["path"]).resolve()
    pptx = (root / stage_b["pptx"]["path"]).resolve()
    preview = (root / stage_b["rendered_preview"]["path"]).resolve()
    for path in (target, pptx, preview):
        if not path.is_relative_to(root):
            raise ValueError(f"ASSET_OUTSIDE_REPOSITORY:{path}")
        if not path.is_file():
            raise FileNotFoundError(path)
    inventory, audit = inspect_reconstruction(
        pptx, manifest["slide_index"], manifest["content_lock"]["on_slide"]
    )
    return {
        "workflow_id": manifest["workflow_id"],
        "slide_id": manifest["slide_id"],
        "slide_index": manifest["slide_index"],
        "target_image_sha256": sha256_file(target),
        "pptx_sha256": sha256_file(pptx),
        "rendered_preview_sha256": sha256_file(preview),
        "object_inventory": inventory,
        "audit": audit
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit_manifest(args.manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(f"{report['audit']['status'].upper()} Image-first PPTX audit: {args.output}")


if __name__ == "__main__":
    main()
