"""Audits the declared FigureSpec science contract and rendered PPTX output."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE


def _norm_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).replace("\v", "\n")
    return re.sub(r"\s+", " ", value).strip()


def audit_figure_spec_semantics(spec_path: Path) -> dict:
    """Verify evidence references and declared directed edges against FigureSpec links.

    This is an internal-consistency audit, not a substitute for domain-expert
    confirmation that the source paper itself supports those relationships.
    """
    spec_path = Path(spec_path)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    elements = spec.get("elements", [])
    evidence = spec.get("evidence_records", [])
    evidence_ids = [item.get("id") for item in evidence]
    evidence_set = {item for item in evidence_ids if item}
    element_ids = [item.get("id") for item in elements]
    semantic_ids = {item.get("semantic_id") for item in elements if item.get("semantic_id")}
    blockers = []
    unknown_evidence = sorted({
        item.get("evidence_ref") for item in elements
        if item.get("evidence_ref") not in evidence_set
    })
    if not evidence or len(evidence_set) != len(evidence_ids):
        blockers.append("EVIDENCE_RECORDS_MISSING_OR_DUPLICATED")
    if len(element_ids) != len(set(element_ids)):
        blockers.append("DUPLICATE_ELEMENT_ID")
    if unknown_evidence:
        blockers.append("UNKNOWN_EVIDENCE_REFERENCE")
    if not spec.get("figure_contract", {}).get("claim"):
        blockers.append("FIGURE_CLAIM_MISSING")

    declared = {
        (str(edge[0]), str(edge[1]))
        for edge in spec.get("semantic_edges", [])
        if isinstance(edge, (list, tuple)) and len(edge) == 2
    }
    malformed_edges = len(declared) != len(spec.get("semantic_edges", []))
    if malformed_edges:
        blockers.append("MALFORMED_SEMANTIC_EDGE")
    endpoint_missing = sorted({
        endpoint for edge in declared for endpoint in edge
        if endpoint not in semantic_ids
    })
    if endpoint_missing:
        blockers.append("SEMANTIC_ENDPOINT_NOT_REPRESENTED")

    represented = set()
    malformed_links = []
    for item in elements:
        link = item.get("semantic_link")
        if not link:
            continue
        parts = str(link).split("__")
        if len(parts) != 2 or not all(parts):
            malformed_links.append(str(link))
            continue
        represented.add((parts[0], parts[1]))
    if malformed_links:
        blockers.append("MALFORMED_SEMANTIC_LINK")
    missing = sorted(declared - represented)
    extra = sorted(represented - declared)
    if missing:
        blockers.append("DECLARED_EDGE_NOT_RENDERED")
    if extra:
        blockers.append("UNDECLARED_EDGE_RENDERED")

    if not declared:
        if blockers:
            status = "FAIL"
        else:
            status = "NEEDS_REVIEW"
            blockers.append("SEMANTIC_RELATION_AUDIT_MISSING")
    else:
        status = "FAIL" if blockers else "PASS"

    return {
        "status": status,
        "source_spec_sha256": hashlib.sha256(spec_path.read_bytes()).hexdigest(),
        "figure_id": spec.get("id"),
        "claim": spec.get("figure_contract", {}).get("claim"),
        "evidence_record_count": len(evidence),
        "element_count": len(elements),
        "semantic_node_count": len(semantic_ids),
        "declared_edge_count": len(declared),
        "represented_edge_count": len(represented),
        "missing_edges": [list(edge) for edge in missing],
        "extra_edges": [list(edge) for edge in extra],
        "missing_semantic_endpoints": endpoint_missing,
        "unknown_evidence_refs": unknown_evidence,
        "unverified_claims": spec.get("figure_contract", {}).get("unverified", []),
        "blockers": sorted(set(blockers)),
        "scope": "FigureSpec internal consistency only; source-science approval remains separate",
    }


def audit_figurespec_output(spec_path: Path, candidate_pptx: Path) -> dict:
    """Check rendered PPTX labels, local pictures, bounds and text collisions."""
    spec_path, candidate_pptx = Path(spec_path), Path(candidate_pptx)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    deck = Presentation(candidate_pptx)
    if len(deck.slides) != 1:
        raise ValueError("FigureSpec output must contain exactly one slide")
    slide = deck.slides[0]
    shapes = list(slide.shapes)
    text_shapes = [
        shape for shape in shapes
        if getattr(shape, "has_text_frame", False) and shape.text.strip()
    ]
    expected_text = Counter(
        _norm_text(item.get("text", ""))
        for item in spec.get("elements", [])
        if item.get("type") == "text" and item.get("text", "").strip()
    )
    actual_text = Counter(_norm_text(shape.text) for shape in text_shapes)
    missing = list((expected_text - actual_text).elements())
    extra = list((actual_text - expected_text).elements())
    expected_pictures = sum(item.get("type") == "image" for item in spec.get("elements", []))
    pictures = [shape for shape in shapes if shape.shape_type == MSO_SHAPE_TYPE.PICTURE]
    out_of_bounds = []
    for shape in shapes:
        if (shape.left < -9144 or shape.top < -9144 or
            shape.left + shape.width > deck.slide_width + 9144 or
            shape.top + shape.height > deck.slide_height + 9144):
            out_of_bounds.append(shape.name)

    overlaps = []
    threshold = 27432  # 0.03 inch
    for i, left in enumerate(text_shapes):
        for right in text_shapes[i + 1:]:
            iw = max(0, min(left.left + left.width, right.left + right.width)
                     - max(left.left, right.left))
            ih = max(0, min(left.top + left.height, right.top + right.height)
                     - max(left.top, right.top))
            if iw > threshold and ih > threshold:
                overlaps.append({"left": left.name, "right": right.name,
                                 "left_text": left.text[:80], "right_text": right.text[:80]})

    full_page_pictures = [
        shape.name for shape in pictures
        if shape.width >= deck.slide_width * .9 and shape.height >= deck.slide_height * .9
    ]
    structure_blockers = []
    if not shapes:
        structure_blockers.append("EMPTY_CANDIDATE")
    if len(pictures) != expected_pictures:
        structure_blockers.append("FIGURESPEC_IMAGE_COUNT_MISMATCH")
    if out_of_bounds:
        structure_blockers.append("OUT_OF_BOUNDS_OBJECTS")
    if full_page_pictures:
        structure_blockers.append("FLATTENED_FULL_FIGURE")
    if missing or extra:
        structure_blockers.append("FIGURESPEC_TEXT_CONTENT_MISMATCH")

    text_blockers = []
    if missing or extra:
        text_blockers.append("FIGURESPEC_TEXT_CONTENT_MISMATCH")
    if overlaps:
        text_blockers.append("TEXT_OBJECT_OVERLAP")
    if out_of_bounds:
        text_blockers.append("OUT_OF_BOUNDS_TEXT_OR_OBJECTS")

    return {
        "structure": {
            "status": "PASS" if not structure_blockers else "FAIL",
            "shape_count": len(shapes),
            "native_shape_count": len(shapes) - len(pictures),
            "picture_count": len(pictures),
            "expected_picture_count": expected_pictures,
            "out_of_bounds": out_of_bounds,
            "full_page_pictures": full_page_pictures,
            "blockers": structure_blockers,
        },
        "text_geometry": {
            "status": "PASS" if not text_blockers else "FAIL",
            "expected_text_count": sum(expected_text.values()),
            "candidate_text_count": sum(actual_text.values()),
            "missing_text": missing,
            "extra_text": extra,
            "overlap_count": len(overlaps),
            "overlaps": overlaps,
            "introduced_out_of_bounds_count": len(out_of_bounds),
            "blockers": text_blockers,
        },
        "candidate_sha256": hashlib.sha256(candidate_pptx.read_bytes()).hexdigest(),
        "spec_sha256": hashlib.sha256(spec_path.read_bytes()).hexdigest(),
    }
