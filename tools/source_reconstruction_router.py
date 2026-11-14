"""Evidence-based advisory reconstruction routing for reviewed PDF figure regions.

This module never executes a reconstruction route or edits FigureSpec. It only
produces provenance-locked recommendations from source objects and human review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

from source_layout_review import validate_source_layout_review


def _area(box: Sequence[float]) -> float:
    return max(0.0, float(box[2]) - float(box[0])) * max(0.0, float(box[3]) - float(box[1]))


def _intersection(a: Sequence[float], b: Sequence[float]) -> float:
    width = max(0.0, min(float(a[2]), float(b[2])) - max(float(a[0]), float(b[0])))
    height = max(0.0, min(float(a[3]), float(b[3])) - max(float(a[1]), float(b[1])))
    return width * height


def _valid_box(box: Any) -> bool:
    return (
        isinstance(box, (list, tuple)) and len(box) == 4
        and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in box)
        and float(box[2]) > float(box[0]) and float(box[3]) > float(box[1])
    )


def _source_objects(layout: dict) -> list[dict]:
    objects: dict[str, dict] = {}
    for item in layout.get("layout_elements", []):
        object_id = item.get("id")
        if object_id:
            objects[object_id] = {
                "id": object_id,
                "kind": item.get("kind", "unknown"),
                "source_order": item.get("source_order"),
                "bbox_pt": item.get("bbox_pt"),
            }
    for item in layout.get("image_assets", []):
        object_id = item.get("id")
        if object_id and object_id not in objects:
            objects[object_id] = {
                "id": object_id,
                "kind": "image",
                "source_order": item.get("source_order"),
                "bbox_pt": item.get("bbox_pt"),
            }
    return sorted(objects.values(), key=lambda item: (
        item["source_order"] is None,
        item["source_order"] if item["source_order"] is not None else 0,
        item["id"],
    ))


def _route_region(
    region_id: str,
    scope: str,
    bbox: Sequence[float],
    objects: list[dict],
) -> dict:
    images, vectors, texts, unknown = [], [], [], []
    ambiguous = []
    evidence = []
    for item in objects:
        source_box = item.get("bbox_pt")
        if not _valid_box(source_box):
            unknown.append(item["id"])
            continue
        intersection = _intersection(source_box, bbox)
        if intersection <= 0:
            continue
        ratio = min(1.0, intersection / max(_area(source_box), 1e-9))
        record = {
            "source_object_id": item["id"],
            "kind": item["kind"],
            "source_order": item["source_order"],
            "overlap_ratio": round(ratio, 6),
        }
        evidence.append(record)
        if ratio < 0.90:
            ambiguous.append(record)
            continue
        kind = item["kind"]
        if kind == "image":
            images.append(item["id"])
        elif kind in ("filled_path", "stroke_path"):
            vectors.append(item["id"])
        elif kind == "text_span":
            texts.append(item["id"])
        else:
            unknown.append(item["id"])

    counts = {
        "image_assets": len(images),
        "vector_primitives": len(vectors),
        "native_text_spans": len(texts),
        "ambiguous_objects": len(ambiguous),
        "unclassified_objects": len(unknown),
    }
    if ambiguous or unknown:
        route = "manual_review_required"
        reason = (
            "One or more intersecting source objects cross the reviewed boundary."
            if ambiguous else
            "One or more intersecting source objects have unknown type or invalid geometry."
        )
    elif not evidence:
        route = "unsupported_source"
        reason = "No recoverable source PDF object intersects the reviewed bounds."
    elif images and (vectors or texts):
        route = "mixed_native_picture"
        reason = "Raster image content coexists with editable PDF vector and/or text objects."
    elif images:
        route = "source_picture_only"
        reason = "The reviewed bounds contain raster image assets without native text/vector content."
    elif vectors:
        route = "native_vector"
        reason = "The reviewed bounds contain native vector primitives and no raster image assets."
    elif texts:
        route = "native_text"
        reason = "The reviewed bounds contain native PDF text spans without raster or vector content."
    else:
        route = "manual_review_required"
        reason = "The source-object composition is insufficient for a safe route decision."

    return {
        "scope": scope,
        "reviewed_region_id": region_id,
        "bbox_pt": [float(v) for v in bbox],
        "recommended_route": route,
        "status": "ADVISORY_ONLY",
        "execution_authorized": False,
        "counts": counts,
        "source_object_ids": {
            "images": images,
            "vectors": vectors,
            "texts": texts,
            "ambiguous": [item["source_object_id"] for item in ambiguous],
            "unclassified": unknown,
        },
        "object_evidence": evidence,
        "reason": reason,
    }


def build_reconstruction_routes(layout_path: Path, review_path: Path) -> dict:
    layout_path, review_path = Path(layout_path), Path(review_path)
    layout = json.loads(layout_path.read_text(encoding="utf-8"))
    audit = validate_source_layout_review(layout_path, review_path)
    if audit["status"] == "INVALID":
        raise ValueError("INVALID_SOURCE_LAYOUT_REVIEW: " + "; ".join(audit["errors"]))
    if audit["status"] != "VALIDATED_WITH_ACCEPTED_FACTS":
        raise ValueError("HUMAN_REVIEWED_SOURCE_FACTS_REQUIRED")

    objects = _source_objects(layout)
    figure_route = _route_region(
        "full_figure", "figure", layout["figure_region_pt"], objects
    )
    panel_routes = []
    region_routes = []
    for item in audit["accepted_source_panels"]:
        if not _valid_box(item.get("bbox_pt")):
            raise ValueError(f"INVALID_ACCEPTED_PANEL_BOUNDS:{item.get('candidate_id')}")
        panel_routes.append(_route_region(
            item["candidate_id"], "panel", item["bbox_pt"], objects
        ))
    for item in audit["accepted_source_layout_regions"]:
        if not _valid_box(item.get("bbox_pt")):
            raise ValueError(f"INVALID_ACCEPTED_REGION_BOUNDS:{item.get('candidate_id')}")
        region_routes.append(_route_region(
            item["candidate_id"], "region", item["bbox_pt"], objects
        ))

    return {
        "schema_version": "1.0.0",
        "status": "ADVISORY_RECONSTRUCTION_ROUTES",
        "source": {
            "filename": layout["source"]["filename"],
            "sha256": layout["source"]["sha256"],
            "page_index": layout["source"]["page_index"],
            "figure_region_pt": layout["figure_region_pt"],
        },
        "source_layout_sha256": audit["source_layout_sha256"],
        "human_review_sha256": audit["review_file_sha256"],
        "reviewed_panel_count": len(panel_routes),
        "reviewed_region_count": len(region_routes),
        "figure_route": figure_route,
        "panel_routes": panel_routes,
        "region_routes": region_routes,
        "policy": {
            "execution_authorized": False,
            "scientific_relations_verified": False,
            "route_basis": "source PDF object composition and human-reviewed bounds",
            "boundary_overlap_threshold": 0.90,
        },
    }


def write_reconstruction_routes(layout_path: Path, review_path: Path, output_path: Path) -> dict:
    output_path = Path(output_path)
    if output_path.exists():
        output_path.unlink()
    result = build_reconstruction_routes(layout_path, review_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result["output"] = str(output_path)
    result["output_sha256"] = hashlib.sha256(output_path.read_bytes()).hexdigest()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_layout", type=Path)
    parser.add_argument("human_review", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = write_reconstruction_routes(args.source_layout, args.human_review, args.output)
    print(json.dumps({
        "status": result["status"],
        "figure_route": result["figure_route"]["recommended_route"],
        "panel_routes": len(result["panel_routes"]),
        "region_routes": len(result["region_routes"]),
        "execution_authorized": False,
        "output": result["output"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
