"""Fail-closed release classification for source-PDF import and FigureSpec routes.

Technical checks never imply scientific, visual, rights, or target-Office approval.
"""
from __future__ import annotations

from typing import Any


VALID_ROUTES = {"import", "figurespec"}


def _status(report: dict | None) -> str | None:
    return report.get("status") if isinstance(report, dict) else None


def classify_release(*, route: str, candidate: dict | None = None,
                     import_report: dict | None = None,
                     structure: dict | None = None,
                     text_geometry: dict | None = None,
                     visual: dict | None = None,
                     office: dict | None = None,
                     semantic_audit: dict | None = None,
                     approvals: dict | None = None,
                     error: str | None = None,
                     require_native: bool = True,
                     require_office_host: bool = True) -> dict:
    """Return an explicit release status, blockers and missing approval evidence.

    Status precedence is intentionally conservative:
      RESOURCE_LIMIT > UNSUPPORTED_SOURCE > STRUCTURE_FAIL >
      NEEDS_VISUAL_REVIEW > NEEDS_SCIENTIFIC_REVIEW > TECHNICAL_PASS/FULL_ACCEPTED.
    """
    if route not in VALID_ROUTES:
        raise ValueError(f"route must be one of {sorted(VALID_ROUTES)}")

    candidate = candidate or {}
    import_report = import_report or {}
    approvals = approvals or {}
    blockers: list[str] = []
    pending: list[str] = []

    if error:
        if "RESOURCE_LIMIT" in error:
            return {"status": "RESOURCE_LIMIT", "full_accepted": False,
                    "blockers": ["RESOURCE_LIMIT"], "pending_approvals": [],
                    "route": route, "error": error}
        if any(token in error for token in ("UNRESOLVED_SOURCE_IMAGES", "UNSUPPORTED_SOURCE")):
            return {"status": "UNSUPPORTED_SOURCE", "full_accepted": False,
                    "blockers": ["UNSUPPORTED_SOURCE"], "pending_approvals": [],
                    "route": route, "error": error}
        if "NO_VISIBLE_SOURCE_CONTENT" in error:
            return {"status": "STRUCTURE_FAIL", "full_accepted": False,
                    "blockers": ["NO_VISIBLE_SOURCE_CONTENT"], "pending_approvals": [],
                    "route": route, "error": error}
        return {"status": "STRUCTURE_FAIL", "full_accepted": False,
                "blockers": ["CONVERSION_ERROR"], "pending_approvals": [],
                "route": route, "error": error}

    if int(candidate.get("shape_count", 0)) <= 0:
        blockers.append("EMPTY_CANDIDATE")
        return {"status": "STRUCTURE_FAIL", "full_accepted": False,
                "blockers": blockers, "pending_approvals": [],
                "route": route}

    if int(candidate.get("full_page_pictures", 0)) > 0:
        blockers.append("FLATTENED_FULL_FIGURE")
        return {"status": "UNSUPPORTED_SOURCE" if require_native else "NEEDS_SCIENTIFIC_REVIEW",
                "full_accepted": False, "blockers": blockers,
                "pending_approvals": ["scientific_review", "visual_review"],
                "route": route}

    reconstruction_class = import_report.get("reconstruction_class")
    if require_native and reconstruction_class == "source_picture_only":
        blockers.append("SOURCE_PICTURE_ONLY")
        return {"status": "UNSUPPORTED_SOURCE", "full_accepted": False,
                "blockers": blockers,
                "pending_approvals": ["native_editable_reconstruction"],
                "route": route}

    if import_report.get("unresolved_visible_events", 0):
        blockers.append("UNRESOLVED_SOURCE_IMAGES")
        return {"status": "UNSUPPORTED_SOURCE", "full_accepted": False,
                "blockers": blockers, "pending_approvals": [],
                "route": route}

    if _status(structure) != "PASS":
        blockers.append("STRUCTURE_AUDIT_NOT_PASSED")
    if text_geometry is not None and _status(text_geometry) != "PASS":
        blockers.append("TEXT_GEOMETRY_AUDIT_NOT_PASSED")
    if _status(office) != "PASS":
        blockers.append("OOXML_PREFLIGHT_NOT_PASSED")
    if blockers:
        return {"status": "STRUCTURE_FAIL", "full_accepted": False,
                "blockers": blockers, "pending_approvals": [],
                "route": route}

    if route == "figurespec":
        if semantic_audit is None or _status(semantic_audit) != "PASS":
            blockers.append("SEMANTIC_RELATION_FAILURE" if semantic_audit else
                            "SEMANTIC_RELATION_AUDIT_MISSING")
            return {"status": "NEEDS_SCIENTIFIC_REVIEW", "full_accepted": False,
                    "blockers": blockers,
                    "pending_approvals": ["scientific_review"],
                    "route": route}

    if visual is None or visual.get("requires_visual_review", True):
        blockers.append("VISUAL_REVIEW_REQUIRED")
        return {"status": "NEEDS_VISUAL_REVIEW", "full_accepted": False,
                "blockers": blockers,
                "pending_approvals": ["visual_review"],
                "route": route}

    # Source-visible imports preserve source geometry but do not certify its
    # scientific meaning. Both routes require explicit scientific approval.
    if approvals.get("scientific_review") != "approved":
        pending.append("scientific_review")
    if approvals.get("visual_review") != "approved":
        pending.append("visual_review")
    if approvals.get("rights_review") != "cleared":
        pending.append("rights_review")
    host = approvals.get("office_host") or {}
    if require_office_host and host.get("status") != "verified":
        pending.append("office_host")

    if not pending:
        return {"status": "FULL_ACCEPTED", "full_accepted": True,
                "blockers": [], "pending_approvals": [],
                "route": route, "approvals": approvals}

    if "office_host" in pending:
        status = "NEEDS_OFFICE_HOST_REVIEW"
    elif "rights_review" in pending:
        status = "NEEDS_RIGHTS_REVIEW"
    elif "visual_review" in pending:
        status = "NEEDS_VISUAL_REVIEW"
    elif "scientific_review" in pending:
        status = "NEEDS_SCIENTIFIC_REVIEW"
    else:
        status = "TECHNICAL_PASS"
    return {"status": status, "full_accepted": False,
            "blockers": [], "pending_approvals": pending,
            "route": route, "approvals": approvals}


if __name__ == "__main__":
    raise SystemExit("Import classify_release() from the reproduction pipeline.")
