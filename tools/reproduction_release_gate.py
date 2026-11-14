"""Fail-closed release classification for source-PDF import and FigureSpec routes.

A generated PPTX, a valid OOXML package, and a visually similar raster are
technical evidence only. Full acceptance additionally requires explicit
scientific, visual, rights and target-host approval.
"""
from __future__ import annotations

VALID_ROUTES = {"import", "figurespec"}
IMPORT_CLASSES = {"native_only", "mixed_native_picture", "source_picture_only"}


def _status(report: dict | None) -> str | None:
    return report.get("status") if isinstance(report, dict) else None


def _result(status: str, route: str, *, blockers=None, pending=None,
            reconstruction_class=None, approvals=None, error=None,
            full_accepted=False) -> dict:
    result = {
        "status": status,
        "full_accepted": bool(full_accepted),
        "blockers": list(blockers or []),
        "pending_approvals": list(pending or []),
        "route": route,
    }
    if reconstruction_class is not None:
        result["reconstruction_class"] = reconstruction_class
    if approvals is not None:
        result["approvals"] = approvals
    if error is not None:
        result["error"] = error
    return result


def classify_release(*, route: str, candidate: dict | None = None,
                     import_report: dict | None = None,
                     structure: dict | None = None,
                     text_geometry: dict | None = None,
                     visual: dict | None = None,
                     office: dict | None = None,
                     semantic_audit: dict | None = None,
                     approvals: dict | None = None,
                     source_risks: list | None = None,
                     error: str | None = None,
                     require_native: bool = True,
                     require_office_host: bool = True) -> dict:
    """Classify a candidate with explicit route-specific evidence requirements."""
    if route not in VALID_ROUTES:
        raise ValueError(f"route must be one of {sorted(VALID_ROUTES)}")

    candidate = candidate or {}
    import_report = import_report or {}
    approvals = approvals or {}
    source_risks = source_risks or []
    reconstruction_class = None

    if error:
        if "RESOURCE_LIMIT" in error:
            return _result("RESOURCE_LIMIT", route, blockers=["RESOURCE_LIMIT"], error=error)
        if any(token in error for token in ("UNRESOLVED_SOURCE_IMAGES", "UNSUPPORTED_SOURCE")):
            return _result("UNSUPPORTED_SOURCE", route, blockers=["UNSUPPORTED_SOURCE"], error=error)
        if "NO_VISIBLE_SOURCE_CONTENT" in error:
            return _result("STRUCTURE_FAIL", route, blockers=["NO_VISIBLE_SOURCE_CONTENT"], error=error)
        return _result("STRUCTURE_FAIL", route, blockers=["CONVERSION_ERROR"], error=error)

    if int(candidate.get("shape_count", 0)) <= 0:
        return _result("STRUCTURE_FAIL", route, blockers=["EMPTY_CANDIDATE"])

    full_page_pictures = int(candidate.get("full_page_pictures", 0))
    picture_count = int(candidate.get("picture_objects", 0))
    vector_count = int(candidate.get("native_vectors", 0))
    if full_page_pictures:
        status = "UNSUPPORTED_SOURCE" if require_native else "RASTER_SOURCE_ONLY"
        return _result(status, route, blockers=["FLATTENED_FULL_FIGURE"])

    if route == "import":
        reconstruction_class = import_report.get("reconstruction_class")
        if reconstruction_class not in IMPORT_CLASSES:
            return _result(
                "UNSUPPORTED_SOURCE", route,
                blockers=["RECONSTRUCTION_CLASS_MISSING_OR_UNKNOWN"],
                reconstruction_class=reconstruction_class,
            )
        if import_report.get("unresolved_visible_events", 0):
            return _result("UNSUPPORTED_SOURCE", route,
                           blockers=["UNRESOLVED_SOURCE_IMAGES"],
                           reconstruction_class=reconstruction_class)
        if reconstruction_class == "source_picture_only":
            status = "UNSUPPORTED_SOURCE" if require_native else "SOURCE_PICTURE_ONLY"
            return _result(
                status, route, blockers=["SOURCE_PICTURE_ONLY"],
                pending=["native_editable_reconstruction"],
                reconstruction_class=reconstruction_class,
            )
        if reconstruction_class == "native_only" and picture_count:
            return _result("STRUCTURE_FAIL", route,
                           blockers=["RECONSTRUCTION_CLASS_OBJECT_COUNT_MISMATCH"],
                           reconstruction_class=reconstruction_class)
        if reconstruction_class == "mixed_native_picture" and (picture_count <= 0 or vector_count <= 0):
            return _result("STRUCTURE_FAIL", route,
                           blockers=["MIXED_RECONSTRUCTION_OBJECT_COUNT_MISMATCH"],
                           reconstruction_class=reconstruction_class)
        if reconstruction_class == "native_only" and vector_count <= 0:
            return _result("STRUCTURE_FAIL", route,
                           blockers=["NATIVE_RECONSTRUCTION_HAS_NO_NATIVE_VECTORS"],
                           reconstruction_class=reconstruction_class)

    blockers = []
    if _status(structure) != "PASS":
        blockers.append("STRUCTURE_AUDIT_NOT_PASSED")
    if text_geometry is None:
        blockers.append("TEXT_GEOMETRY_AUDIT_MISSING")
    elif _status(text_geometry) != "PASS":
        blockers.append("TEXT_GEOMETRY_AUDIT_NOT_PASSED")
    if _status(office) != "PASS":
        blockers.append("OOXML_PREFLIGHT_NOT_PASSED")
    if blockers:
        return _result("STRUCTURE_FAIL", route, blockers=blockers,
                       reconstruction_class=reconstruction_class)

    if route == "figurespec":
        if semantic_audit is None:
            return _result("NEEDS_SCIENTIFIC_REVIEW", route,
                           blockers=["SEMANTIC_RELATION_AUDIT_MISSING"])
        if _status(semantic_audit) != "PASS":
            return _result("NEEDS_SCIENTIFIC_REVIEW", route,
                           blockers=semantic_audit.get("blockers") or ["SEMANTIC_RELATION_FAILURE"])

    required_visual_evidence = "source_comparison" if route == "import" else "candidate_render"
    if (visual is None or _status(visual) != "PASS" or
        visual.get("evidence_type") != required_visual_evidence or
        not visual.get("renderer") or visual.get("requires_visual_review", True)):
        return _result("NEEDS_VISUAL_REVIEW", route,
                       blockers=["ROUTE_SPECIFIC_VISUAL_EVIDENCE_REQUIRED"],
                       reconstruction_class=reconstruction_class)

    if source_risks:
        codes = {str(item.get("code", "")) for item in source_risks if isinstance(item, dict)}
        if codes & {"SUSPICIOUS_UNICODE", "MATH_FONT"}:
            return _result("NEEDS_SCIENTIFIC_REVIEW", route,
                           blockers=["SOURCE_MATH_OR_UNICODE_RISK_REQUIRES_REVIEW"],
                           reconstruction_class=reconstruction_class)
        return _result("NEEDS_VISUAL_REVIEW", route,
                       blockers=["SOURCE_RENDER_RISK_REQUIRES_REVIEW"],
                       reconstruction_class=reconstruction_class)

    pending = []
    if approvals.get("scientific_review") != "approved":
        pending.append("scientific_review")
    if approvals.get("visual_review") != "approved":
        pending.append("visual_review")
    if approvals.get("rights_review") != "cleared":
        pending.append("rights_review")
    if require_office_host and (approvals.get("office_host") or {}).get("status") != "verified":
        pending.append("office_host")

    if not pending:
        return _result("FULL_ACCEPTED", route, approvals=approvals,
                       reconstruction_class=reconstruction_class, full_accepted=True)

    if not approvals:
        return _result("TECHNICAL_PASS", route, pending=pending,
                       reconstruction_class=reconstruction_class)

    if "office_host" in pending:
        status = "NEEDS_OFFICE_HOST_REVIEW"
    elif "rights_review" in pending:
        status = "NEEDS_RIGHTS_REVIEW"
    elif "visual_review" in pending:
        status = "NEEDS_VISUAL_REVIEW"
    else:
        status = "NEEDS_SCIENTIFIC_REVIEW"
    return _result(status, route, pending=pending, approvals=approvals,
                   reconstruction_class=reconstruction_class)


if __name__ == "__main__":
    raise SystemExit("Import classify_release() from the reproduction pipeline.")
