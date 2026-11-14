"""Optional visual proposals and conservative SourceLayout evidence fusion.

The base extractor stays model-free. This module has no import-time dependency
on PaddleOCR; model adapters are loaded only when explicitly requested.
"""
from __future__ import annotations

import math
import re
from typing import Any, Iterable, Sequence


_VISUAL_LAYOUT_LABELS = {"figure", "image", "chart", "table", "algorithm"}
_PARENTHESES_RE = re.compile(r"^\(\s*([a-z])\s*\)$", re.IGNORECASE)
_PUNCTUATED_RE = re.compile(r"^([a-z])[\).]$", re.IGNORECASE)
_BARE_RE = re.compile(r"^([a-z])$", re.IGNORECASE)


def _as_list(value: Any) -> list:
    if value is None:
        return []
    if hasattr(value, "tolist"):
        value = value.tolist()
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _unwrap_result(value: Any) -> dict:
    """Unwrap PaddleOCR result objects, dicts, JSON strings, or result lists."""
    if isinstance(value, (list, tuple)):
        if not value:
            return {}
        value = value[0]
    if not isinstance(value, dict) and hasattr(value, "json"):
        value = getattr(value, "json")
        if callable(value):
            value = value()
    if isinstance(value, str):
        import json
        try:
            value = json.loads(value)
        except (TypeError, ValueError):
            return {}
    if not isinstance(value, dict):
        return {}
    if isinstance(value.get("res"), dict):
        return value["res"]
    return value


def _finite_number(value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError("INVALID_RASTER_BBOX")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("INVALID_RASTER_BBOX")
    return result


def _validated_region(region: Sequence[float]) -> tuple[float, float, float, float]:
    if len(region) != 4:
        raise ValueError("INVALID_FIGURE_REGION")
    x0, y0, x1, y1 = (_finite_number(value) for value in region)
    if x1 <= x0 or y1 <= y0:
        raise ValueError("INVALID_FIGURE_REGION")
    return x0, y0, x1, y1


def map_raster_bbox_to_pdf(
    bbox_px: Sequence[float],
    raster_size: tuple[int, int],
    figure_region_pt: Sequence[float],
) -> list[float]:
    """Map [x0,y0,x1,y1] raster pixels to the exact PDF-point crop."""
    if len(bbox_px) != 4 or len(raster_size) != 2:
        raise ValueError("INVALID_RASTER_BBOX")
    x0, y0, x1, y1 = (_finite_number(value) for value in bbox_px)
    width_px, height_px = raster_size
    if (isinstance(width_px, bool) or isinstance(height_px, bool)
        or not isinstance(width_px, int) or not isinstance(height_px, int)
        or width_px <= 0 or height_px <= 0
        or x0 < 0 or y0 < 0 or x1 > width_px or y1 > height_px
        or x1 <= x0 or y1 <= y0):
        raise ValueError("INVALID_RASTER_BBOX")
    rx0, ry0, rx1, ry1 = _validated_region(figure_region_pt)
    scale_x = (rx1 - rx0) / width_px
    scale_y = (ry1 - ry0) / height_px
    return [
        round(rx0 + x0 * scale_x, 3),
        round(ry0 + y0 * scale_y, 3),
        round(rx0 + x1 * scale_x, 3),
        round(ry0 + y1 * scale_y, 3),
    ]


def _normalized_bbox(bbox_pt: Sequence[float], region: Sequence[float]) -> list[float]:
    x0, y0, x1, y1 = (float(value) for value in bbox_pt)
    rx0, ry0, rx1, ry1 = _validated_region(region)
    return [
        round((x0 - rx0) / (rx1 - rx0), 6),
        round((y0 - ry0) / (ry1 - ry0), 6),
        round((x1 - x0) / (rx1 - rx0), 6),
        round((y1 - y0) / (ry1 - ry0), 6),
    ]


def _confidence(score: float) -> str:
    if score >= 0.85:
        return "high"
    if score >= 0.65:
        return "medium"
    return "low"


def normalize_layout_detections(
    raw_result: Any,
    raster_size: tuple[int, int],
    figure_region_pt: Sequence[float],
) -> list[dict]:
    """Normalize PaddleOCR layout boxes into stable PDF-coordinate candidates."""
    payload = _unwrap_result(raw_result)
    boxes = _as_list(payload.get("boxes"))
    deduplicated: dict[tuple, dict] = {}
    for raw in boxes:
        if not isinstance(raw, dict):
            continue
        label = str(raw.get("label", "")).strip().lower()
        if label not in _VISUAL_LAYOUT_LABELS:
            continue
        try:
            bbox = map_raster_bbox_to_pdf(
                raw.get("coordinate", raw.get("bbox", [])),
                raster_size,
                figure_region_pt,
            )
            score = min(1.0, max(0.0, _finite_number(raw.get("score", 0.0))))
        except (TypeError, ValueError):
            continue
        key = (label, tuple(round(value, 1) for value in bbox))
        item = {
            "model_label": label,
            "model_score": round(score, 6),
            "bbox_pt": bbox,
            "bbox_normalized": _normalized_bbox(bbox, figure_region_pt),
            "candidate_type": "visual_region",
            "evidence_source": "paddleocr_layout_detection",
            "confidence": _confidence(score),
            "confidence_basis": "general document-layout model proposal; not scientific panel confirmation",
            "needs_human_review": True,
        }
        if key not in deduplicated or score > deduplicated[key]["model_score"]:
            deduplicated[key] = item
    ordered = sorted(
        deduplicated.values(),
        key=lambda item: (
            item["bbox_pt"][1], item["bbox_pt"][0],
            -((item["bbox_pt"][2] - item["bbox_pt"][0]) *
              (item["bbox_pt"][3] - item["bbox_pt"][1])),
            item["model_label"],
        ),
    )
    for index, item in enumerate(ordered, 1):
        item["id"] = f"visual_region_{index:03d}"
    return ordered


def _panel_marker(text: str) -> tuple[str, str] | None:
    cleaned = re.sub(r"\s+", "", str(text or ""))
    match = _PARENTHESES_RE.fullmatch(cleaned)
    if match:
        return match.group(1).lower(), "parenthesized"
    match = _PUNCTUATED_RE.fullmatch(cleaned)
    if match:
        return match.group(1).lower(), "punctuated"
    match = _BARE_RE.fullmatch(cleaned)
    if match:
        return match.group(1).lower(), "bare"
    return None


def _polygon_bbox(polygon: Any) -> list[float]:
    values = _as_list(polygon)
    if len(values) == 4 and all(
        isinstance(value, (int, float)) and not isinstance(value, bool)
        for value in values
    ):
        x0, y0, x1, y1 = (_finite_number(value) for value in values)
        return [x0, y0, x1, y1]
    points = []
    for point in values:
        pair = _as_list(point)
        if len(pair) < 2:
            raise ValueError("INVALID_OCR_POLYGON")
        points.append((_finite_number(pair[0]), _finite_number(pair[1])))
    if not points:
        raise ValueError("INVALID_OCR_POLYGON")
    return [
        min(point[0] for point in points),
        min(point[1] for point in points),
        max(point[0] for point in points),
        max(point[1] for point in points),
    ]


def normalize_ocr_detections(
    raw_result: Any,
    raster_size: tuple[int, int],
    figure_region_pt: Sequence[float],
) -> list[dict]:
    """Normalize OCR output; only isolated panel-like tokens become candidates."""
    payload = _unwrap_result(raw_result)
    texts = _as_list(payload.get("rec_texts", payload.get("texts")))
    scores = _as_list(payload.get("rec_scores", payload.get("scores")))
    polygons = _as_list(payload.get("dt_polys", payload.get("rec_polys", payload.get("rec_boxes"))))
    markers = []
    for index, text in enumerate(texts):
        parsed = _panel_marker(str(text))
        if parsed is None or index >= len(polygons):
            continue
        score = _finite_number(scores[index]) if index < len(scores) else 0.0
        if score < 0.55:
            continue
        label, marker_style = parsed
        if marker_style == "bare" and score < 0.85:
            continue
        try:
            bbox_px = _polygon_bbox(polygons[index])
            bbox_pt = map_raster_bbox_to_pdf(bbox_px, raster_size, figure_region_pt)
        except (TypeError, ValueError):
            continue
        markers.append({
            "id": f"ocr_marker_{index + 1:03d}",
            "label": label,
            "text": str(text),
            "marker_style": marker_style,
            "ocr_score": round(min(1.0, max(0.0, score)), 6),
            "bbox_pt": bbox_pt,
            "bbox_normalized": _normalized_bbox(bbox_pt, figure_region_pt),
            "candidate_type": "ocr_panel_marker",
            "confidence": "low" if marker_style == "bare" else _confidence(score),
            "confidence_basis": (
                "isolated single-letter OCR token; panel identity is unverified"
                if marker_style == "bare"
                else "punctuated OCR token resembling a figure panel label"
            ),
            "needs_human_review": True,
            "anchor_status": "UNRESOLVED",
            "matched_region_candidate_id": None,
        })
    return sorted(markers, key=lambda item: (item["bbox_pt"][1], item["bbox_pt"][0], item["id"]))


def _area(box: Sequence[float]) -> float:
    return max(0.0, float(box[2]) - float(box[0])) * max(0.0, float(box[3]) - float(box[1]))


def _intersection_area(a: Sequence[float], b: Sequence[float]) -> float:
    width = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    height = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    return width * height


def _contains(outer: Sequence[float], inner: Sequence[float], tolerance: float = 0.0) -> bool:
    return (
        outer[0] <= inner[0] + tolerance
        and outer[1] <= inner[1] + tolerance
        and outer[2] >= inner[2] - tolerance
        and outer[3] >= inner[3] - tolerance
    )


def _union_bbox(boxes: Iterable[Sequence[float]]) -> list[float]:
    values = list(boxes)
    return [
        round(min(box[0] for box in values), 3),
        round(min(box[1] for box in values), 3),
        round(max(box[2] for box in values), 3),
        round(max(box[3] for box in values), 3),
    ]


def _alignment_groups(candidates: list[dict], region: Sequence[float]) -> list[dict]:
    rx0, ry0, rx1, ry1 = _validated_region(region)
    groups = []
    for axis in ("horizontal_row", "vertical_stack"):
        siblings: dict[str | None, list[dict]] = {}
        for item in candidates:
            siblings.setdefault(item.get("parent_candidate_id"), []).append(item)
        group_index = 0
        for parent_id, members in siblings.items():
            members = sorted(members, key=lambda item: (
                item["bbox_pt"][0] if axis == "horizontal_row" else item["bbox_pt"][1]
            ))
            components: list[list[dict]] = []
            for item in members:
                box = item["bbox_pt"]
                placed = False
                for component in components:
                    previous = component[-1]["bbox_pt"]
                    if axis == "horizontal_row":
                        center_delta = abs((box[1] + box[3]) / 2 - (previous[1] + previous[3]) / 2)
                        gap = box[0] - previous[2]
                        aligned = center_delta <= max(3.0, (ry1 - ry0) * 0.04)
                        size_ratio = min(box[3] - box[1], previous[3] - previous[1]) / max(
                            box[3] - box[1], previous[3] - previous[1], 1e-6
                        )
                        plausible = aligned and size_ratio >= 0.5 and 0 <= gap <= (rx1 - rx0) * 0.4
                    else:
                        center_delta = abs((box[0] + box[2]) / 2 - (previous[0] + previous[2]) / 2)
                        gap = box[1] - previous[3]
                        size_ratio = min(box[2] - box[0], previous[2] - previous[0]) / max(
                            box[2] - box[0], previous[2] - previous[0], 1e-6
                        )
                        aligned = center_delta <= max(3.0, (rx1 - rx0) * 0.04)
                        plausible = aligned and size_ratio >= 0.5 and 0 <= gap <= (ry1 - ry0) * 0.4
                    if plausible:
                        component.append(item)
                        placed = True
                        break
                if not placed:
                    components.append([item])
            for component in components:
                if len(component) < 2:
                    continue
                group_index += 1
                ids = [item["id"] for item in component]
                scores = [float(item.get("model_score", 0.0)) for item in component]
                groups.append({
                    "id": f"visual_alignment_{axis}_{group_index:03d}",
                    "candidate_type": "visual_alignment_group",
                    "axis": axis,
                    "parent_candidate_id": parent_id,
                    "member_candidate_ids": ids,
                    "bbox_pt": _union_bbox(item["bbox_pt"] for item in component),
                    "confidence_score": round(sum(scores) / len(scores), 6),
                    "confidence": _confidence(sum(scores) / len(scores)),
                    "needs_human_review": True,
                    "confidence_basis": "shared parent, repeated alignment, and comparable region dimensions",
                })
    return groups


def fuse_visual_evidence(
    layout_candidates: list[dict],
    ocr_markers: list[dict],
    layout_elements: list[dict],
    image_assets: list[dict],
    figure_region_pt: Sequence[float],
) -> dict:
    """Fuse model proposals with PDF-native geometry without asserting semantics."""
    region = _validated_region(figure_region_pt)
    candidates = [dict(item) for item in layout_candidates]
    for item in candidates:
        item["parent_candidate_id"] = None
        item["depth"] = 0
        item["source_object_ids"] = []
        item["owned_source_object_ids"] = []
        item["source_object_count"] = 0
        item["ownership_coverage"] = 0.0

    for item in candidates:
        box = item["bbox_pt"]
        parents = [
            other for other in candidates
            if other["id"] != item["id"]
            and _area(other["bbox_pt"]) > _area(box) * 1.001
            and _contains(other["bbox_pt"], box, tolerance=0.1)
        ]
        if parents:
            parent = min(parents, key=lambda candidate: _area(candidate["bbox_pt"]))
            item["parent_candidate_id"] = parent["id"]
            item["candidate_type"] = "nested_visual_region"

    by_id = {item["id"]: item for item in candidates}
    for item in candidates:
        parent_id = item["parent_candidate_id"]
        depth = 0
        visited = set()
        while parent_id and parent_id in by_id and parent_id not in visited:
            visited.add(parent_id)
            depth += 1
            parent_id = by_id[parent_id]["parent_candidate_id"]
        item["depth"] = depth

    def is_descendant(candidate_id: str, ancestor_id: str) -> bool:
        current = by_id[candidate_id].get("parent_candidate_id")
        visited = set()
        while current and current in by_id and current not in visited:
            if current == ancestor_id:
                return True
            visited.add(current)
            current = by_id[current].get("parent_candidate_id")
        return False

    objects_by_id = {}
    for source in list(layout_elements) + list(image_assets):
        object_id = source.get("id")
        if object_id and object_id not in objects_by_id:
            objects_by_id[object_id] = source
    ownership = []
    contained_by_candidate: dict[str, list[str]] = {item["id"]: [] for item in candidates}
    owned_by_candidate: dict[str, list[str]] = {item["id"]: [] for item in candidates}

    for object_id, source in sorted(objects_by_id.items()):
        box = source.get("bbox_pt")
        if not isinstance(box, (list, tuple)) or len(box) != 4:
            ownership.append({
                "source_object_id": object_id, "candidate_id": None,
                "source_order": source.get("source_order"), "overlap_ratio": 0.0,
                "status": "UNRESOLVED", "ownership_scope": None,
                "reason": "MISSING_SOURCE_BBOX",
            })
            continue
        object_area = max(_area(box), 1e-6)
        overlaps = []
        for candidate in candidates:
            intersection = _intersection_area(box, candidate["bbox_pt"])
            ratio = min(1.0, intersection / object_area)
            if intersection > 0:
                if ratio >= 0.9:
                    contained_by_candidate[candidate["id"]].append(object_id)
                overlaps.append((ratio, _area(candidate["bbox_pt"]), candidate["id"]))
        eligible = [item for item in overlaps if item[0] >= 0.9]
        if not eligible:
            ownership.append({
                "source_object_id": object_id, "candidate_id": None,
                "source_order": source.get("source_order"),
                "overlap_ratio": round(max((item[0] for item in overlaps), default=0.0), 6),
                "status": "UNRESOLVED", "ownership_scope": None,
                "reason": "CROSSES_REGION_BOUNDARY" if overlaps else "NO_REGION_OVERLAP",
            })
            continue
        eligible.sort(key=lambda item: (item[1], -item[0], item[2]))
        best = eligible[0]
        tied = len(eligible) > 1 and abs(eligible[1][1] - best[1]) <= 1e-6
        if tied:
            ownership.append({
                "source_object_id": object_id, "candidate_id": None,
                "source_order": source.get("source_order"),
                "overlap_ratio": round(best[0], 6),
                "status": "UNRESOLVED", "ownership_scope": None,
                "reason": "AMBIGUOUS_REGION_OWNERSHIP",
            })
            continue
        intersecting_children = [
            candidate for candidate in candidates
            if candidate["id"] != best[2]
            and is_descendant(candidate["id"], best[2])
            and _intersection_area(box, candidate["bbox_pt"]) > 0
        ]
        if intersecting_children:
            status = "CONTAINER_ONLY"
            scope = "container"
            reason = "OBJECT_CROSSES_CHILD_REGIONS"
        else:
            status = "ASSIGNED"
            scope = "region"
            reason = "DEEPEST_UNAMBIGUOUS_CONTAINING_REGION"
        owned_by_candidate[best[2]].append(object_id)
        ownership.append({
            "source_object_id": object_id, "candidate_id": best[2],
            "source_order": source.get("source_order"),
            "overlap_ratio": round(best[0], 6),
            "status": status, "ownership_scope": scope, "reason": reason,
        })

    for item in candidates:
        contained = contained_by_candidate[item["id"]]
        intersecting_count = sum(
            1 for source in objects_by_id.values()
            if isinstance(source.get("bbox_pt"), (list, tuple))
            and _intersection_area(source["bbox_pt"], item["bbox_pt"]) > 0
        )
        item["source_object_ids"] = sorted(contained)
        item["owned_source_object_ids"] = sorted(owned_by_candidate[item["id"]])
        item["source_object_count"] = len(contained)
        item["ownership_coverage"] = round(
            len(contained) / max(1, intersecting_count), 6
        )
        model_score = float(item.get("model_score", 0.0))
        item["confidence_score"] = round(
            0.7 * model_score + 0.3 * item["ownership_coverage"], 6
        )
        item["confidence"] = _confidence(item["confidence_score"])
        item["confidence_basis"] = (
            "heuristic fusion of general layout-model score and source-object containment; "
            "not a calibrated probability or scientific panel confirmation"
        )
        item["review_status"] = "needs_human_review"
        item["needs_human_review"] = True

    markers = [dict(item) for item in ocr_markers]
    hypotheses = []
    for marker in markers:
        box = marker["bbox_pt"]
        center_x = (box[0] + box[2]) / 2
        center_y = (box[1] + box[3]) / 2
        containing = [
            item for item in candidates
            if _contains(item["bbox_pt"], [center_x, center_y, center_x, center_y])
        ]
        containing.sort(key=lambda item: _area(item["bbox_pt"]))
        anchor = None
        anchor_strength = 0.0
        if containing:
            candidate = containing[0]
            region_box = candidate["bbox_pt"]
            x_fraction = (center_x - region_box[0]) / max(region_box[2] - region_box[0], 1e-6)
            y_fraction = (center_y - region_box[1]) / max(region_box[3] - region_box[1], 1e-6)
            near_top_left = x_fraction <= 0.35 and y_fraction <= 0.35
            bare_allowed = (
                marker.get("marker_style") != "bare"
                or (x_fraction <= 0.2 and y_fraction <= 0.2
                    and float(marker.get("ocr_score", 0.0)) >= 0.97)
            )
            if near_top_left and bare_allowed:
                anchor = candidate
                anchor_strength = max(0.0, 1.0 - (x_fraction + y_fraction) / 0.7)
        if anchor is None:
            marker["anchor_status"] = "UNRESOLVED"
            marker["matched_region_candidate_id"] = None
            continue
        marker["anchor_status"] = "ANCHORED_CANDIDATE"
        marker["matched_region_candidate_id"] = anchor["id"]
        model_score = float(anchor.get("model_score", 0.0))
        ocr_score = float(marker.get("ocr_score", 0.0))
        score = round(0.45 * model_score + 0.4 * ocr_score + 0.15 * anchor_strength, 6)
        hypotheses.append({
            "id": f"panel_hypothesis_{marker['label']}_{len(hypotheses) + 1:03d}",
            "candidate_id": anchor["id"],
            "candidate_type": "label_anchored_visual_region",
            "region_candidate_id": anchor["id"],
            "marker_candidate_id": marker["id"],
            "label": marker["label"],
            "marker_text": marker["text"],
            "bbox_pt": list(anchor["bbox_pt"]),
            "bbox_normalized": list(anchor["bbox_normalized"]),
            "confidence_score": score,
            "confidence": _confidence(score),
            "confidence_basis": "heuristic fusion of region model score, OCR score, and top-left marker anchor",
            "needs_human_review": True,
            "review_status": "needs_human_review",
        })

    return {
        "visual_region_candidates": candidates,
        "ocr_panel_markers": markers,
        "panel_hypotheses": hypotheses,
        "visual_alignment_groups": _alignment_groups(candidates, region),
        "source_object_ownership": ownership,
    }
