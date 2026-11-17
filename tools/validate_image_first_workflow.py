#!/usr/bin/env python3
"""Validate an Image-first V8 workflow manifest and its real PPTX/image artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

from audit_image_first_reconstruction import inspect_reconstruction, sha256_file
from compare_image_first_renders import compare_images
from image_first_source_contract import load_source_figure_contract

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "specs/image_first_workflow_v8.schema.json"
APPROVAL_CHECKS = (
    "scientific_content",
    "exact_text",
    "source_fidelity",
    "visual_hierarchy",
    "projection_readability",
    "reconstruction_feasibility",
)


class WorkflowValidationError(ValueError):
    pass


def _resolve(root: Path, relative: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute():
        raise WorkflowValidationError(f"ABSOLUTE_PATH_NOT_ALLOWED:{relative}")
    resolved = (root / candidate).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise WorkflowValidationError(f"PATH_ESCAPES_REPOSITORY:{relative}")
    return resolved


def _check_asset(root: Path, asset: dict, label: str) -> Path:
    path = _resolve(root, asset["path"])
    if not path.is_file():
        raise WorkflowValidationError(f"ASSET_MISSING:{label}:{asset['path']}")
    observed = sha256_file(path)
    if observed != asset["sha256"]:
        raise WorkflowValidationError(f"ASSET_SHA256_MISMATCH:{label}")
    return path


def _check_image(root: Path, asset: dict, label: str, expected_size: tuple[int, int] | None = None) -> Path:
    path = _check_asset(root, asset, label)
    try:
        with Image.open(path) as image:
            size = image.size
            media = {
                "PNG": "image/png",
                "JPEG": "image/jpeg",
                "WEBP": "image/webp"
            }.get(image.format)
    except Exception as exc:
        raise WorkflowValidationError(f"IMAGE_UNREADABLE:{label}:{exc}") from exc
    if media != asset["media_type"]:
        raise WorkflowValidationError(f"IMAGE_MEDIA_TYPE_MISMATCH:{label}")
    if size != (asset["width_px"], asset["height_px"]):
        raise WorkflowValidationError(f"IMAGE_DIMENSION_METADATA_MISMATCH:{label}")
    if expected_size and size != expected_size:
        raise WorkflowValidationError(f"IMAGE_DIMENSION_CONTRACT_MISMATCH:{label}")
    return path


def _validate_schema(manifest: dict, schema_path: Path) -> None:
    try:
        import jsonschema
    except ImportError as exc:
        raise WorkflowValidationError("JSONSCHEMA_DEPENDENCY_REQUIRED") from exc
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    errors = sorted(jsonschema.Draft202012Validator(schema).iter_errors(manifest),
                    key=lambda item: list(item.absolute_path))
    if errors:
        first = errors[0]
        location = ".".join(str(value) for value in first.absolute_path) or "<root>"
        raise WorkflowValidationError(f"SCHEMA_INVALID:{location}:{first.message}")


def _validate_deck_lock(root: Path, manifest: dict) -> dict:
    deck_path = _resolve(root, manifest["deck_spec_ref"])
    if not deck_path.is_file():
        raise WorkflowValidationError("DECK_SPEC_MISSING")
    deck = json.loads(deck_path.read_text(encoding="utf-8"))
    slides = deck.get("slides", [])
    matches = [(index, slide) for index, slide in enumerate(slides, 1)
               if slide.get("id") == manifest["slide_id"]]
    if len(matches) != 1:
        raise WorkflowValidationError("DECK_SLIDE_ID_NOT_UNIQUE_OR_MISSING")
    index, slide = matches[0]
    if index != manifest["slide_index"]:
        raise WorkflowValidationError("DECK_SLIDE_INDEX_MISMATCH")
    lock = manifest["content_lock"]
    try:
        source_figure = load_source_figure_contract(root, slide)
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        raise WorkflowValidationError(f"SOURCE_FIGURE_CONTRACT_INVALID:{exc}") from exc
    expected = {
        "claim": slide["claim"],
        "on_slide": slide["on_slide"],
        "speaker_notes": slide["speaker_notes"],
        "evidence": slide["evidence"],
        "source_figure": source_figure
    }
    for key, value in expected.items():
        observed = lock.get(key)
        if observed != value:
            if isinstance(value, dict) and isinstance(observed, dict):
                fields = sorted(set(value) | set(observed))
                mismatched = [
                    field for field in fields
                    if observed.get(field) != value.get(field)
                ]
                detail = ",".join(mismatched)
                raise WorkflowValidationError(
                    f"CONTENT_LOCK_MISMATCH:{key}:{detail}"
                )
            raise WorkflowValidationError(f"CONTENT_LOCK_MISMATCH:{key}")
    for item in lock["evidence"]:
        if not _resolve(root, item["source"]).is_file():
            raise WorkflowValidationError(f"EVIDENCE_SOURCE_MISSING:{item['source']}")
    return deck


def _validate_stage_a(root: Path, stage_a: dict) -> str | None:
    template = _resolve(root, stage_a["prompt"]["template_ref"])
    if not template.is_file():
        raise WorkflowValidationError("IMAGE2_PROMPT_TEMPLATE_MISSING")
    rendered = stage_a["prompt"]["rendered_asset"]
    if rendered is not None:
        _check_asset(root, rendered, "rendered_prompt")

    for index, item in enumerate(stage_a["reference_assets"]):
        _check_asset(root, item["asset"], f"reference_{index + 1}")

    status = stage_a["status"]
    image = stage_a["target_image"]
    if status == "planned":
        if image is not None:
            raise WorkflowValidationError("PLANNED_STAGE_HAS_TARGET_IMAGE")
        return None
    if image is None:
        raise WorkflowValidationError("STAGE_A_TARGET_IMAGE_REQUIRED")
    target_path = _check_image(
        root, image, "target_image",
        (stage_a["generation"]["width_px"], stage_a["generation"]["height_px"])
    )
    review = stage_a["review"]
    if status in {"approved", "locked"}:
        if review["decision"] != "approved":
            raise WorkflowValidationError("STAGE_A_APPROVAL_DECISION_MISSING")
        if review["reviewer"] is None or review["reviewer"]["type"] != "human":
            raise WorkflowValidationError("STAGE_A_APPROVAL_REQUIRES_HUMAN")
        if not review["reviewed_at"]:
            raise WorkflowValidationError("STAGE_A_REVIEW_TIMESTAMP_MISSING")
        if not all(review["checks"][key] for key in APPROVAL_CHECKS):
            raise WorkflowValidationError("STAGE_A_REVIEW_CHECKS_INCOMPLETE")
        if review["issues"]:
            raise WorkflowValidationError("STAGE_A_BLOCKING_ISSUES_REMAIN")
    elif status == "needs_revision" and review["decision"] != "revise":
        raise WorkflowValidationError("STAGE_A_REVISION_DECISION_MISSING")
    return sha256_file(target_path)


def _validate_parity(root: Path, stage_b: dict, target_path: Path, preview_path: Path) -> None:
    parity = stage_b["parity"]
    if parity["target_image_sha256"] != sha256_file(target_path):
        raise WorkflowValidationError("PARITY_TARGET_HASH_MISMATCH")
    if parity["rendered_preview_sha256"] != sha256_file(preview_path):
        raise WorkflowValidationError("PARITY_PREVIEW_HASH_MISMATCH")
    observed = compare_images(target_path, preview_path)
    for key, value in observed["metrics"].items():
        actual = parity["metrics"][key]
        if key == "dhash_hamming_distance":
            equal = actual == value
        else:
            equal = abs(float(actual) - float(value)) <= 0.000002
        if not equal:
            raise WorkflowValidationError(f"PARITY_METRIC_MISMATCH:{key}")
    thresholds = parity["thresholds"]
    metrics = parity["metrics"]
    failures = []
    if metrics["global_ssim"] < thresholds["global_ssim_min"]:
        failures.append("GLOBAL_SSIM_BELOW_THRESHOLD")
    if metrics["mean_absolute_error"] > thresholds["mean_absolute_error_max"]:
        failures.append("MEAN_ABSOLUTE_ERROR_ABOVE_THRESHOLD")
    if metrics["dhash_hamming_distance"] > thresholds["dhash_hamming_distance_max"]:
        failures.append("DHASH_DISTANCE_ABOVE_THRESHOLD")
    if failures:
        raise WorkflowValidationError("PARITY_THRESHOLD_FAILED:" + ",".join(failures))


def validate_manifest(manifest_path: Path, repository_root: Path | None = None,
                      schema_path: Path | None = None) -> dict:
    manifest_path = Path(manifest_path).resolve()
    root = Path(repository_root).resolve() if repository_root else ROOT
    schema_file = Path(schema_path).resolve() if schema_path else SCHEMA
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    _validate_schema(manifest, schema_file)
    _validate_deck_lock(root, manifest)

    target_sha = _validate_stage_a(root, manifest["stage_a"])
    stage_b = manifest["stage_b"]
    status = stage_b["status"]
    if status == "not_started":
        if any(stage_b[key] is not None for key in (
            "target_image_sha256", "pptx", "rendered_preview",
            "object_inventory", "parity", "audit"
        )):
            raise WorkflowValidationError("NOT_STARTED_STAGE_B_CONTAINS_OUTPUTS")
        return {
            "status": "PASS",
            "workflow_id": manifest["workflow_id"],
            "stage": "STAGE_A_PLANNED" if manifest["stage_a"]["status"] == "planned"
                     else "STAGE_A_REVIEW_OR_RECONSTRUCTION_READY"
        }

    if manifest["stage_a"]["status"] not in {"approved", "locked"}:
        raise WorkflowValidationError("STAGE_B_REQUIRES_APPROVED_STAGE_A")
    if status == "in_progress":
        if stage_b["target_image_sha256"] not in (None, target_sha):
            raise WorkflowValidationError("STAGE_B_TARGET_IMAGE_HASH_MISMATCH")
        return {
            "status": "PASS",
            "workflow_id": manifest["workflow_id"],
            "stage": "STAGE_B_IN_PROGRESS"
        }

    if stage_b["target_image_sha256"] != target_sha:
        raise WorkflowValidationError("STAGE_B_TARGET_IMAGE_HASH_MISMATCH")
    target_asset = manifest["stage_a"]["target_image"]
    target_path = _check_image(
        root, target_asset, "target_image",
        (manifest["stage_a"]["generation"]["width_px"],
         manifest["stage_a"]["generation"]["height_px"])
    )
    pptx_path = _check_asset(root, stage_b["pptx"], "pptx")
    preview_path = _check_image(root, stage_b["rendered_preview"], "rendered_preview")
    if preview_path.stat().st_size == 0:
        raise WorkflowValidationError("RENDERED_PREVIEW_EMPTY")

    inventory, observed_audit = inspect_reconstruction(
        pptx_path, manifest["slide_index"], manifest["content_lock"]["on_slide"]
    )
    if stage_b["object_inventory"] != inventory:
        raise WorkflowValidationError("OBJECT_INVENTORY_DOES_NOT_MATCH_PPTX")
    recorded_audit = stage_b["audit"]
    for key in (
        "status", "out_of_bounds", "text_box_overlaps",
        "full_slide_image_backgrounds", "editable_text_coverage", "missing_text", "failures"
    ):
        if recorded_audit[key] != observed_audit[key]:
            raise WorkflowValidationError(f"PPTX_AUDIT_MISMATCH:{key}")

    if status in {"audited", "accepted"}:
        if observed_audit["status"] != "pass":
            raise WorkflowValidationError("STRUCTURAL_AUDIT_NOT_PASSED")
        _validate_parity(root, stage_b, target_path, preview_path)

    if status == "accepted":
        human = stage_b["parity"]["human_review"]
        if human["decision"] != "approved":
            raise WorkflowValidationError("FINAL_VISUAL_REVIEW_NOT_APPROVED")
        if human["reviewer"] is None or human["reviewer"]["type"] != "human":
            raise WorkflowValidationError("FINAL_VISUAL_REVIEW_REQUIRES_HUMAN")
        if not recorded_audit["office_2016_roundtrip"] == "passed":
            raise WorkflowValidationError("OFFICE_2016_ROUNDTRIP_NOT_PASSED")
        evidence = recorded_audit["office_2016_evidence"]
        if evidence is None:
            raise WorkflowValidationError("OFFICE_2016_EVIDENCE_REQUIRED")
        _check_asset(root, evidence, "office_2016_roundtrip_evidence")
        if not stage_b["parity"]["human_review"]["reviewed_at"]:
            raise WorkflowValidationError("FINAL_VISUAL_REVIEW_TIMESTAMP_MISSING")

    return {
        "status": "PASS",
        "workflow_id": manifest["workflow_id"],
        "stage": {
            "reconstructed": "STAGE_B_RECONSTRUCTED",
            "audited": "AUDITED_PENDING_HUMAN_ACCEPTANCE",
            "accepted": "FINAL_ACCEPTANCE"
        }[status],
        "object_inventory": inventory,
        "audit": observed_audit
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--schema", type=Path, default=SCHEMA)
    parser.add_argument(
        "--diagnostics",
        type=Path,
        default=Path("dist/validation_diagnostics/image_first_workflow_failure.json"),
        help="Write a machine-readable failure report here before exiting non-zero.",
    )
    args = parser.parse_args()
    try:
        report = validate_manifest(args.manifest, args.root, args.schema)
    except WorkflowValidationError as exc:
        diagnostic_path = args.diagnostics
        if not diagnostic_path.is_absolute():
            diagnostic_path = args.root / diagnostic_path
        diagnostic_path.parent.mkdir(parents=True, exist_ok=True)
        diagnostic_path.write_text(
            json.dumps({
                "status": "FAIL",
                "manifest": str(args.manifest),
                "error_type": type(exc).__name__,
                "error": str(exc),
            }, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        raise
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except WorkflowValidationError as exc:
        raise SystemExit(f"FAIL Image-first workflow: {exc}") from exc
