"""Create and validate human review records for SourceLayout candidates."""
from __future__ import annotations

import argparse
import hashlib
import math
import json
from pathlib import Path


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _candidate_index(layout: dict) -> dict:
    detection = layout.get("panel_detection", {})
    index = {}
    for item in detection.get("unlabeled_panel_candidates", []):
        index[item["id"]] = {
            "candidate_type": item["candidate_type"],
            "bbox_pt": item["bbox_pt"],
            "confidence": item["confidence"],
        }
    by_id = {item["id"]: item for item in detection.get("unlabeled_panel_candidates", [])}
    for group in detection.get("alignment_groups", []):
        members = [by_id[item_id] for item_id in group["member_candidate_ids"] if item_id in by_id]
        if members:
            boxes = [item["bbox_pt"] for item in members]
            bbox = [
                min(item[0] for item in boxes),
                min(item[1] for item in boxes),
                max(item[2] for item in boxes),
                max(item[3] for item in boxes),
            ]
        else:
            bbox = None
        index[group["id"]] = {
            "candidate_type": "alignment_group",
            "bbox_pt": bbox,
            "confidence": group["confidence"],
            "member_candidate_ids": group["member_candidate_ids"],
            "axis": group["axis"],
        }
    for gutter in detection.get("raster_gutter_candidates", []):
        index[gutter["id"]] = {
            "candidate_type": "raster_gutter",
            "axis": gutter["axis"],
            "start_pt": gutter["start_pt"],
            "end_pt": gutter["end_pt"],
            "width_pt": gutter["width_pt"],
            "confidence": gutter["confidence"],
            "source_image_id": gutter["source_image_id"],
        }
    return index


def _split_source_region(candidate_id: str, actual: dict, item: dict, region: list) -> list[dict]:
    """Generate two evidence-linked *geometric* regions, never semantic panels."""
    if actual["candidate_type"] not in ("source_enclosure", "nested_source_enclosure"):
        raise ValueError("CANDIDATE_CANNOT_BE_SPLIT")
    axis = item.get("split_axis")
    value = item.get("split_position_pt")
    if axis not in ("horizontal", "vertical") or isinstance(value, bool):
        raise ValueError("INVALID_SPLIT_GEOMETRY")
    if not isinstance(value, (float, int)) or not math.isfinite(float(value)):
        raise ValueError("INVALID_SPLIT_GEOMETRY")
    box = actual.get("bbox_pt")
    if not isinstance(box, list) or len(box) != 4:
        raise ValueError("INVALID_SPLIT_GEOMETRY")
    x0, y0, x1, y1 = (float(n) for n in box)
    rx0, ry0, rx1, ry1 = (float(n) for n in region)
    if (not all(math.isfinite(v) for v in (x0,y0,x1,y1,rx0,ry0,rx1,ry1))
        or x0 < rx0 or y0 < ry0 or x1 > rx1 or y1 > ry1
        or x1 <= x0 or y1 <= y0):
        raise ValueError("INVALID_SPLIT_GEOMETRY")
    cut = float(value)
    low, high = (y0, y1) if axis == "horizontal" else (x0, x1)
    min_gap = max(2.0, (high - low) * 0.05)
    if cut <= low + min_gap or cut >= high - min_gap:
        raise ValueError("INVALID_SPLIT_GEOMETRY")
    boxes = (
        [[x0,y0,x1,cut], [x0,cut,x1,y1]]
        if axis == "horizontal" else
        [[x0,y0,cut,y1], [cut,y0,x1,y1]]
    )
    result = []
    for index, child in enumerate(boxes, 1):
        normalized = [
            round((child[0] - rx0) / (rx1 - rx0), 6),
            round((child[1] - ry0) / (ry1 - ry0), 6),
            round((child[2] - child[0]) / (rx1 - rx0), 6),
            round((child[3] - child[1]) / (ry1 - ry0), 6),
        ]
        result.append({
            "candidate_id": f"{candidate_id}__part{index}",
            "candidate_type": "human_split_region",
            "bbox_pt": [round(v, 6) for v in child],
            "bbox_normalized": normalized,
            "derived_from_candidate": candidate_id,
            "split_axis": axis,
            "split_position_pt": cut,
            "confidence": actual["confidence"],
            "semantic_role": "geometric_region_only",
            "review_state": "human_accepted_geometry_not_science",
            "rationale": str(item.get("rationale","")).strip(),
            "evidence_locator": str(item.get("evidence_locator","")).strip(),
        })
    return result


def create_source_layout_review_template(layout_path: Path, output_path: Path) -> dict:
    layout_path, output_path = Path(layout_path), Path(output_path)
    layout = json.loads(layout_path.read_text(encoding="utf-8"))
    candidates = _candidate_index(layout)
    decisions = []
    for candidate_id, snapshot in sorted(candidates.items()):
        decisions.append({
            "candidate_id": candidate_id,
            "candidate_snapshot": snapshot,
            "decision": "pending",
            "rationale": "",
            "evidence_locator": "",
        })
    review = {
        "schema_version": "1.0.0",
        "source_layout_sha256": _sha256(layout_path),
        "source": {
            "filename": layout["source"]["filename"],
            "sha256": layout["source"]["sha256"],
            "page_index": layout["source"]["page_index"],
            "figure_region_pt": layout["figure_region_pt"],
        },
        "reviewer": {"name": "", "type": "human"},
        "decisions": decisions,
        "policy": {
            "accept_panel_requires_human": True,
            "raster_gutter_can_only_be_accepted_as_region": True,
            "assistant_triage_cannot_accept_or_reject": True,
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return review


def validate_source_layout_review(layout_path: Path, review_path: Path) -> dict:
    layout_path, review_path = Path(layout_path), Path(review_path)
    layout = json.loads(layout_path.read_text(encoding="utf-8"))
    review = json.loads(review_path.read_text(encoding="utf-8"))
    candidates = _candidate_index(layout)
    errors = []

    if review.get("schema_version") != "1.0.0":
        errors.append("UNSUPPORTED_REVIEW_SCHEMA")
    if review.get("source_layout_sha256") != _sha256(layout_path):
        errors.append("SOURCE_LAYOUT_HASH_MISMATCH")
    source = review.get("source", {})
    expected_source = layout.get("source", {})
    if source.get("sha256") != expected_source.get("sha256"):
        errors.append("SOURCE_PDF_HASH_MISMATCH")
    if source.get("page_index") != expected_source.get("page_index"):
        errors.append("SOURCE_PAGE_MISMATCH")
    if source.get("figure_region_pt") != layout.get("figure_region_pt"):
        errors.append("FIGURE_REGION_MISMATCH")

    reviewer = review.get("reviewer", {})
    reviewer_type = reviewer.get("type")
    reviewer_name = str(reviewer.get("name", "")).strip()
    if reviewer_type not in ("human", "assistant_visual_triage"):
        errors.append("INVALID_REVIEWER_TYPE")

    decisions = review.get("decisions", [])
    decision_ids = [item.get("candidate_id") for item in decisions]
    if len(decision_ids) != len(set(decision_ids)):
        errors.append("DUPLICATE_CANDIDATE_DECISION")
    missing = sorted(set(candidates) - set(decision_ids))
    unknown = sorted(set(decision_ids) - set(candidates))
    if missing:
        errors.append("REVIEW_COVERAGE_INCOMPLETE")
    if unknown:
        errors.append("UNKNOWN_CANDIDATE_ID")

    accepted_regions = []
    accepted_panels = []
    split_region_count = 0
    rejected = []
    pending = []
    for item in decisions:
        candidate_id = item.get("candidate_id")
        if candidate_id not in candidates:
            continue
        actual = candidates[candidate_id]
        if item.get("candidate_snapshot") != actual:
            errors.append(f"CANDIDATE_SNAPSHOT_MISMATCH:{candidate_id}")
        decision = item.get("decision")
        rationale = str(item.get("rationale", "")).strip()
        locator = str(item.get("evidence_locator", "")).strip()

        if decision not in ("pending", "accept_region", "accept_panel", "split_region", "reject", "defer"):
            errors.append(f"INVALID_DECISION:{candidate_id}")
            continue
        if reviewer_type == "assistant_visual_triage" and decision in ("accept_region", "accept_panel", "split_region", "reject"):
            errors.append(f"ASSISTANT_CANNOT_APPROVE_OR_REJECT:{candidate_id}")
            continue
        if decision in ("accept_region", "accept_panel", "reject"):
            if reviewer_type != "human" or not reviewer_name:
                errors.append(f"HUMAN_REVIEWER_REQUIRED:{candidate_id}")
            if not rationale:
                errors.append(f"REVIEW_RATIONALE_REQUIRED:{candidate_id}")
        if decision in ("accept_region", "accept_panel", "split_region") and not locator:
            errors.append(f"EVIDENCE_LOCATOR_REQUIRED:{candidate_id}")
        if decision == "accept_panel" and actual["candidate_type"] not in (
            "source_enclosure", "nested_source_enclosure", "interstitial_band"
        ):
            errors.append(f"CANDIDATE_CANNOT_BE_PROMOTED_TO_PANEL:{candidate_id}")
            continue

        if decision == "split_region":
            try:
                children = _split_source_region(
                    candidate_id, actual, item, layout["figure_region_pt"]
                )
            except ValueError as exc:
                errors.append(f"{exc}:{candidate_id}")
                continue
            split_region_count += 1
            accepted_regions.extend({**child, "reviewer": reviewer} for child in children)
            continue

        record = {
            "candidate_id": candidate_id,
            **actual,
            "rationale": rationale,
            "evidence_locator": locator,
            "reviewer": reviewer,
        }
        if decision == "accept_region":
            accepted_regions.append(record)
        elif decision == "accept_panel":
            accepted_panels.append(record)
        elif decision == "reject":
            rejected.append(candidate_id)
        else:
            pending.append(candidate_id)

    valid = not errors
    if not valid:
        # Prevent consumers from using partially approved geometry when any
        # part of the file failed integrity, provenance or review checks.
        accepted_regions.clear()
        accepted_panels.clear()
        split_region_count = 0
        rejected.clear()
    return {
        "status": (
            "INVALID" if not valid else
            "VALIDATED_WITH_ACCEPTED_FACTS" if accepted_regions or accepted_panels else
            "REVIEW_PENDING"
        ),
        "source_layout_sha256": _sha256(layout_path),
        "review_file_sha256": _sha256(review_path),
        "candidate_count": len(candidates),
        "decision_count": len(decisions),
        "accepted_region_count": len(accepted_regions),
        "accepted_panel_count": len(accepted_panels),
        "split_region_count": split_region_count,
        "rejected_count": len(rejected),
        "pending_count": len(pending),
        "accepted_source_layout_regions": accepted_regions,
        "accepted_source_panels": accepted_panels,
        "rejected_candidate_ids": rejected,
        "pending_candidate_ids": pending,
        "errors": sorted(set(errors)),
        "policy": "Only human-reviewed accepted facts may be consumed downstream; geometric/raster evidence alone never confirms a scientific panel or relation",
    }


def recommend_source_route(layout: dict) -> dict:
    elements = layout.get("layout_elements", [])
    drawing_count = sum(
        item.get("kind") in ("filled_path", "stroke_path")
        for item in elements
    )
    image_count = len(layout.get("image_assets", []))
    if image_count and drawing_count:
        route = "mixed_native_picture"
        rationale = "Source image assets and vector drawing records coexist; preserve both as separate objects."
    elif image_count:
        route = "source_picture_only"
        rationale = "The selected crop contains recovered image assets but no vector drawing records."
    elif drawing_count:
        route = "native_only"
        rationale = "The selected crop contains vector drawing records and no recovered image assets."
    else:
        route = "unsupported_source"
        rationale = "No recoverable image or vector drawing records were found in the selected crop."
    return {
        "status": "ADVISORY_ONLY",
        "recommended_reconstruction_class": route,
        "image_asset_count": image_count,
        "vector_drawing_record_count": drawing_count,
        "rationale": rationale,
        "source_layout_sha256": layout.get("source", {}).get("sha256"),
        "human_review_required": True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("template", help="create a pending review template from SourceLayout JSON")
    create.add_argument("source_layout", type=Path)
    create.add_argument("--output", type=Path, required=True)
    validate = sub.add_parser("validate", help="validate human decisions against SourceLayout JSON")
    validate.add_argument("source_layout", type=Path)
    validate.add_argument("review", type=Path)
    validate.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "template":
        result = create_source_layout_review_template(args.source_layout, args.output)
        print(json.dumps({
            "status": "TEMPLATE_CREATED",
            "candidate_count": len(result["decisions"]),
            "output": str(args.output),
        }, ensure_ascii=False))
    else:
        result = validate_source_layout_review(args.source_layout, args.review)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({
            "status": result["status"],
            "accepted_regions": result["accepted_region_count"],
            "accepted_panels": result["accepted_panel_count"],
            "pending": result["pending_count"],
            "errors": result["errors"],
            "output": str(args.output),
        }, ensure_ascii=False))
        if result["status"] == "INVALID":
            raise SystemExit(1)




# Extend the legacy review index additively; model evidence remains review-only.
_legacy_candidate_index = _candidate_index


def _candidate_index(layout):
    base = _legacy_candidate_index(layout)
    detection = layout.get("panel_detection", {})
    visual_items = []
    for field in ("visual_region_candidates", "panel_hypotheses", "visual_alignment_groups"):
        for source in detection.get(field, []):
            item = dict(source)
            candidate_id = item.get("id")
            if not candidate_id:
                continue
            # Keep the review decision key distinct from the source-region link.
            item["candidate_id"] = candidate_id
            visual_items.append(item)

    if isinstance(base, dict):
        result = dict(base)
        for item in visual_items:
            result[item["candidate_id"]] = item
        return result
    result = list(base)
    existing = {
        item.get("id", item.get("candidate_id"))
        for item in result if isinstance(item, dict)
    }
    result.extend(item for item in visual_items if item["candidate_id"] not in existing)
    return result

if __name__ == "__main__":
    main()
