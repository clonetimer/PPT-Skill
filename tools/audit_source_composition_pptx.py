"""Audit imported PPTX shapes against the P1-01D composition manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read_shape_metadata(shape):
    nodes = [node for node in shape._element.iter() if node.tag.endswith("}cNvPr")]
    if not nodes:
        return None
    descr = nodes[0].get("descr")
    if not descr:
        return None
    try:
        value = json.loads(descr)
    except (TypeError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def audit_imported_pptx_against_composition(manifest_path: Path, pptx_path: Path) -> dict:
    manifest_path, pptx_path = Path(manifest_path), Path(pptx_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "COMPOSITION_PLAN_READY":
        raise ValueError("COMPOSITION_MANIFEST_NOT_EXECUTABLE")
    if manifest.get("policy", {}).get("execution_authorized") is not False:
        raise ValueError("COMPOSITION_MANIFEST_AUTHORIZATION_INVALID")

    expected = {}
    for unit in manifest.get("composition_units", []):
        for item in unit.get("objects", []):
            treatment = item.get("treatment")
            if treatment not in ("editable_vector", "editable_text", "picture_asset"):
                continue
            object_id = item["source_object_id"]
            if object_id in expected:
                raise ValueError(f"DUPLICATE_EXPECTED_SOURCE_OBJECT:{object_id}")
            expected[object_id] = item

    deck = Presentation(pptx_path)
    if len(deck.slides) != 1:
        raise ValueError("SOURCE_PDF_IMPORT_EXPECTS_ONE_SLIDE")
    actual_shapes = []
    actual_by_id = {}
    malformed_metadata = []
    for index, shape in enumerate(deck.slides[0].shapes):
        metadata = _read_shape_metadata(shape)
        if metadata is None:
            malformed_metadata.append({"shape_index": index, "shape_name": shape.name})
            continue
        object_id = metadata.get("source_object_id")
        if not object_id:
            malformed_metadata.append({"shape_index": index, "shape_name": shape.name})
            continue
        record = {
            "shape_index": index,
            "shape_name": shape.name,
            "shape_type": str(shape.shape_type),
            "source_object_id": object_id,
            "source_order": metadata.get("source_order"),
            "object_class": metadata.get("object_class"),
            "is_picture": shape.shape_type == MSO_SHAPE_TYPE.PICTURE,
            "has_text_frame": bool(shape.has_text_frame),
        }
        actual_shapes.append(record)
        actual_by_id.setdefault(object_id, []).append(record)

    missing = sorted(set(expected) - set(actual_by_id))
    unexpected = sorted(set(actual_by_id) - set(expected))
    duplicates = sorted(object_id for object_id, records in actual_by_id.items() if len(records) != 1)
    class_mismatches = []
    for object_id, item in expected.items():
        records = actual_by_id.get(object_id, [])
        if len(records) != 1:
            continue
        actual = records[0]
        treatment = item["treatment"]
        valid = (
            actual["is_picture"] if treatment == "picture_asset"
            else actual["has_text_frame"] if treatment == "editable_text"
            else not actual["is_picture"]
        )
        if not valid:
            class_mismatches.append({
                "source_object_id": object_id,
                "expected_treatment": treatment,
                "actual_shape_type": actual["shape_type"],
                "actual_has_text_frame": actual["has_text_frame"],
            })

    expected_order = [
        object_id for object_id, item in expected.items()
        if item.get("source_order") is not None
    ]
    expected_order.sort(key=lambda object_id: (
        expected[object_id]["source_order"], object_id
    ))
    actual_order = [
        record["source_object_id"] for record in actual_shapes
        if record.get("source_order") is not None
        and record["source_object_id"] in expected
    ]
    order_matches = actual_order == expected_order
    order_missing = [object_id for object_id in expected_order if object_id not in actual_order]

    failures = []
    if missing:
        failures.append("MISSING_SOURCE_OBJECTS")
    if unexpected:
        failures.append("UNEXPECTED_SOURCE_OBJECTS")
    if duplicates:
        failures.append("DUPLICATED_SOURCE_OBJECTS")
    if malformed_metadata:
        failures.append("SHAPES_WITHOUT_VALID_SOURCE_METADATA")
    if class_mismatches:
        failures.append("OBJECT_CLASS_MISMATCH")
    if not order_matches:
        failures.append("SOURCE_PAINT_ORDER_MISMATCH")

    return {
        "schema_version": "1.0.0",
        "status": "PASS" if not failures else "FAIL",
        "manifest_sha256": _sha256(manifest_path),
        "pptx_sha256": _sha256(pptx_path),
        "expected_object_count": len(expected),
        "actual_annotated_shape_count": len(actual_shapes),
        "missing_source_object_ids": missing,
        "unexpected_source_object_ids": unexpected,
        "duplicate_source_object_ids": duplicates,
        "malformed_shape_metadata": malformed_metadata,
        "class_mismatches": class_mismatches,
        "expected_source_order": expected_order,
        "actual_source_order": actual_order,
        "source_order_matches": order_matches,
        "source_order_missing_ids": order_missing,
        "object_class_counts": dict(Counter(item["object_class"] for item in actual_shapes)),
        "failures": failures,
        "policy": {
            "scientific_relations_verified": False,
            "visual_fidelity_verified": False,
            "office2016_host_verified": False,
            "this_audit_verifies": "source-object provenance, object class, count, uniqueness, and paint-order metadata",
        },
    }


def write_audit(manifest_path: Path, pptx_path: Path, output_path: Path) -> dict:
    output_path = Path(output_path)
    if output_path.exists():
        output_path.unlink()
    result = audit_imported_pptx_against_composition(manifest_path, pptx_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result["output"] = str(output_path)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("composition_manifest", type=Path)
    parser.add_argument("imported_pptx", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = write_audit(args.composition_manifest, args.imported_pptx, args.output)
    print(json.dumps({
        "status": result["status"],
        "expected_objects": result["expected_object_count"],
        "actual_shapes": result["actual_annotated_shape_count"],
        "failures": result["failures"],
        "output": result["output"],
    }, ensure_ascii=False))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
