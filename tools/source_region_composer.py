"""Build a provenance-locked composition manifest from reviewed source routes.

This is a planning/audit layer. It does not edit FigureSpec or create PPTX files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _object_class(kind: str) -> str:
    if kind == "image":
        return "image"
    if kind in ("filled_path", "stroke_path"):
        return "vector"
    if kind == "text_span":
        return "text"
    return "unsupported"


def _source_inventory(layout: dict) -> list[dict]:
    by_id: dict[str, dict] = {}
    for item in layout.get("layout_elements", []):
        object_id = item.get("id")
        if not object_id:
            continue
        record = {
            "id": object_id,
            "kind": item.get("kind", "unknown"),
            "object_class": _object_class(item.get("kind", "unknown")),
            "source_order": item.get("source_order"),
            "bbox_pt": item.get("bbox_pt"),
            "text": item.get("text") if item.get("kind") == "text_span" else None,
        }
        if object_id in by_id and by_id[object_id] != record:
            raise ValueError(f"DUPLICATE_SOURCE_OBJECT_ID_CONFLICT:{object_id}")
        by_id[object_id] = record
    for item in layout.get("image_assets", []):
        object_id = item.get("id")
        if not object_id:
            continue
        record = {
            "id": object_id,
            "kind": "image",
            "object_class": "image",
            "source_order": item.get("source_order"),
            "bbox_pt": item.get("bbox_pt"),
            "text": None,
        }
        if object_id in by_id and by_id[object_id]["object_class"] != "image":
            raise ValueError(f"DUPLICATE_SOURCE_OBJECT_ID_CONFLICT:{object_id}")
        by_id.setdefault(object_id, record)
    return sorted(by_id.values(), key=lambda item: (
        item["source_order"] is None,
        item["source_order"] if item["source_order"] is not None else 0,
        item["bbox_pt"][1] if isinstance(item.get("bbox_pt"), list) else float("inf"),
        item["bbox_pt"][0] if isinstance(item.get("bbox_pt"), list) else float("inf"),
        item["id"],
    ))


def _treatment(route: str, object_class: str) -> str:
    if route == "native_vector" and object_class == "vector":
        return "editable_vector"
    if route == "native_text" and object_class == "text":
        return "editable_text"
    if route == "mixed_native_picture":
        return {
            "vector": "editable_vector",
            "text": "editable_text",
            "image": "picture_asset",
        }.get(object_class, "unsupported")
    if route == "source_picture_only" and object_class == "image":
        return "picture_asset"
    return "unsupported"


def _route_units(routes: dict) -> list[dict]:
    units = []
    figure = routes.get("figure_route")
    if isinstance(figure, dict):
        units.append(figure)
    units.extend(routes.get("panel_routes", []))
    units.extend(routes.get("region_routes", []))
    return units


def build_source_composition_manifest(
    layout_path: Path,
    review_path: Path,
    routes_path: Path,
) -> dict:
    layout_path, review_path, routes_path = map(Path, (layout_path, review_path, routes_path))
    layout = json.loads(layout_path.read_text(encoding="utf-8"))
    review = json.loads(review_path.read_text(encoding="utf-8"))
    routes = json.loads(routes_path.read_text(encoding="utf-8"))

    from source_layout_review import validate_source_layout_review
    review_audit = validate_source_layout_review(layout_path, review_path)
    if review_audit["status"] != "VALIDATED_WITH_ACCEPTED_FACTS":
        raise ValueError("HUMAN_REVIEWED_SOURCE_FACTS_REQUIRED")
    layout_hash = _sha256(layout_path)
    review_hash = _sha256(review_path)
    if routes.get("status") != "ADVISORY_RECONSTRUCTION_ROUTES":
        raise ValueError("INVALID_RECONSTRUCTION_ROUTE_FILE")
    if routes.get("source_layout_sha256") != layout_hash:
        raise ValueError("ROUTE_SOURCE_LAYOUT_HASH_MISMATCH")
    if routes.get("human_review_sha256") != review_hash:
        raise ValueError("ROUTE_HUMAN_REVIEW_HASH_MISMATCH")
    if routes.get("policy", {}).get("execution_authorized") is not False:
        raise ValueError("ROUTE_EXECUTION_AUTHORIZATION_MUST_BE_FALSE")
    source = routes.get("source", {})
    if source.get("sha256") != layout.get("source", {}).get("sha256"):
        raise ValueError("ROUTE_SOURCE_PDF_HASH_MISMATCH")
    if source.get("page_index") != layout.get("source", {}).get("page_index"):
        raise ValueError("ROUTE_SOURCE_PAGE_MISMATCH")

    inventory = _source_inventory(layout)
    object_by_id = {item["id"]: item for item in inventory}
    units = _route_units(routes)
    accepted_ids = {
        item["candidate_id"]
        for item in review_audit["accepted_source_panels"] + review_audit["accepted_source_layout_regions"]
    }
    route_unit_ids = {item.get("reviewed_region_id") for item in units if item.get("scope") != "figure"}
    if route_unit_ids != accepted_ids:
        raise ValueError("ROUTE_REVIEWED_UNIT_COVERAGE_MISMATCH")

    blockers = []
    if not accepted_ids:
        blockers.append("NO_HUMAN_ACCEPTED_PANEL_OR_REGION")
    unit_records = []
    unit_object_refs: dict[str, list[str]] = {}
    for unit in units:
        if unit.get("scope") == "figure":
            continue
        route = unit.get("recommended_route")
        unit_id = unit.get("reviewed_region_id")
        if route in ("manual_review_required", "unsupported_source"):
            blockers.append(f"NON_EXECUTABLE_ROUTE:{unit_id}:{route}")
        if unit.get("execution_authorized") is not False:
            blockers.append(f"UNEXPECTED_ROUTE_AUTHORIZATION:{unit_id}")
        evidence = unit.get("object_evidence", [])
        seen = set()
        objects = []
        for entry in evidence:
            object_id = entry.get("source_object_id")
            if object_id in seen:
                raise ValueError(f"DUPLICATE_OBJECT_WITHIN_ROUTE:{unit_id}:{object_id}")
            seen.add(object_id)
            if object_id not in object_by_id:
                raise ValueError(f"ROUTE_REFERENCES_UNKNOWN_OBJECT:{object_id}")
            source_obj = object_by_id[object_id]
            overlap = float(entry.get("overlap_ratio", 0.0))
            treatment = _treatment(route, source_obj["object_class"])
            if overlap < 0.90:
                treatment = "shared_boundary_review"
            elif treatment == "unsupported":
                blockers.append(f"OBJECT_ROUTE_CLASS_MISMATCH:{unit_id}:{object_id}:{route}")
            objects.append({
                "source_object_id": object_id,
                "object_class": source_obj["object_class"],
                "kind": source_obj["kind"],
                "source_order": source_obj["source_order"],
                "overlap_ratio": overlap,
                "treatment": treatment,
                "editable_expected": treatment in ("editable_vector", "editable_text"),
                "bbox_pt": source_obj["bbox_pt"],
            })
            unit_object_refs.setdefault(object_id, []).append(unit_id)
        objects.sort(key=lambda item: (
            item["source_order"] is None,
            item["source_order"] if item["source_order"] is not None else 0,
            item["bbox_pt"][1] if item.get("bbox_pt") else float("inf"),
            item["bbox_pt"][0] if item.get("bbox_pt") else float("inf"),
            item["source_object_id"],
        ))
        unit_records.append({
            "unit_id": unit_id,
            "scope": unit.get("scope"),
            "bbox_pt": unit.get("bbox_pt"),
            "recommended_route": route,
            "status": "BLOCKED" if route in ("manual_review_required", "unsupported_source") else "PLANNED",
            "object_count": len(objects),
            "objects": objects,
            "editability_expectation": {
                "editable_vector_objects": sum(x["treatment"] == "editable_vector" for x in objects),
                "editable_text_objects": sum(x["treatment"] == "editable_text" for x in objects),
                "picture_objects": sum(x["treatment"] == "picture_asset" for x in objects),
                "shared_boundary_objects": sum(x["treatment"] == "shared_boundary_review" for x in objects),
            },
            "execution_authorized": False,
        })

    shared = []
    for object_id, unit_ids in sorted(unit_object_refs.items()):
        unique_units = sorted(set(unit_ids))
        if len(unique_units) > 1:
            shared.append({
                "source_object_id": object_id,
                "reviewed_unit_ids": unique_units,
                "treatment": "single_figure_level_object_requires_boundary_resolution",
                "duplicated": False,
            })
            blockers.append(f"OBJECT_REFERENCED_BY_MULTIPLE_REVIEWED_UNITS:{object_id}")

    figure_route = routes.get("figure_route", {})
    if figure_route.get("recommended_route") in ("manual_review_required", "unsupported_source"):
        blockers.append("FIGURE_LEVEL_ROUTE_NOT_EXECUTABLE")

    sequence = []
    for item in inventory:
        refs = sorted(set(unit_object_refs.get(item["id"], [])))
        if not refs:
            continue
        sequence.append({
            "source_object_id": item["id"],
            "source_order": item["source_order"],
            "object_class": item["object_class"],
            "reviewed_unit_ids": refs,
            "execution_order": len(sequence) + 1,
            "paint_order_available": item["source_order"] is not None,
        })

    blocked = bool(blockers)
    return {
        "schema_version": "1.0.0",
        "status": "BLOCKED" if blocked else "COMPOSITION_PLAN_READY",
        "source": routes["source"],
        "provenance": {
            "source_layout_sha256": layout_hash,
            "human_review_sha256": review_hash,
            "reconstruction_routes_sha256": _sha256(routes_path),
            "source_pdf_sha256": layout["source"]["sha256"],
        },
        "figure_composition": {
            "recommended_route": figure_route.get("recommended_route"),
            "object_inventory_count": len(inventory),
            "referenced_object_count": len(sequence),
            "unassigned_object_ids": sorted(set(object_by_id) - set(unit_object_refs)),
        },
        "composition_units": unit_records,
        "shared_boundary_objects": shared,
        "source_order_sequence": sequence,
        "blockers": sorted(set(blockers)),
        "policy": {
            "execution_authorized": False,
            "scientific_relations_verified": False,
            "each_source_object_represented_once": True,
            "mixed_content_flattening_allowed": False,
            "route_basis": "human-reviewed regions plus source PDF object inventory",
        },
        "next_stage": "P1-01D2_PPTX_PROVENANCE_ANNOTATION_AND_OUTPUT_AUDIT",
    }


def write_source_composition_manifest(
    layout_path: Path, review_path: Path, routes_path: Path, output_path: Path
) -> dict:
    output_path = Path(output_path)
    if output_path.exists():
        output_path.unlink()
    result = build_source_composition_manifest(layout_path, review_path, routes_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result["output"] = str(output_path)
    result["output_sha256"] = _sha256(output_path)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_layout", type=Path)
    parser.add_argument("human_review", type=Path)
    parser.add_argument("reconstruction_routes", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = write_source_composition_manifest(
        args.source_layout, args.human_review, args.reconstruction_routes, args.output
    )
    print(json.dumps({
        "status": result["status"],
        "composition_units": len(result["composition_units"]),
        "source_objects": result["figure_composition"]["referenced_object_count"],
        "shared_boundary_objects": len(result["shared_boundary_objects"]),
        "blockers": result["blockers"],
        "execution_authorized": False,
        "output": result["output"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
