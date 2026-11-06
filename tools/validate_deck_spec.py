#!/usr/bin/env python3
"""Validate the V7.5 planning contract without external dependencies."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "specs/deck_spec_v75.example.json"
ROLES = {"research_question", "problem", "prior_work", "framework", "method", "experiment", "result", "ablation", "conclusion", "evidence_boundary"}
STATUSES = {"source_visible", "paper_grounded", "verified_artifact", "unverified"}
DIMENSIONS = {"layout", "components", "connectors", "palette", "typography", "iconography", "surface", "density"}


def validate(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "specs/deck_spec_v75.schema.json").read_text(encoding="utf-8"))
    try:
        import jsonschema
    except ImportError:
        pass  # The checks below remain available in minimal local environments.
    else:
        jsonschema.validate(data, schema)
    assert data["schema_version"] == "7.5.0-dev"
    deck, slides, source_style, style = data["deck"], data["slides"], data["source_style"], data["style"]
    assert deck["topic"] and deck["audience"] and deck["duration_minutes"] > 0
    assert deck["target_slide_count"] == len(slides) and deck["narrative"]
    assert deck["style_ref"] == style["id"]
    assert style["source_style_ref"] == source_style["id"]
    assert style["font_family"] and style["background"].startswith("#")
    assert style["text_color"].startswith("#") and style["accent_colors"]
    assert style["density"] in {"sparse", "moderate", "dense"}
    assert style["shadow"] in {"none", "source_evidenced"}
    assert 5 <= len(source_style["anchors"]) <= 7
    assert len({a["dimension"] for a in source_style["anchors"]}) == len(source_style["anchors"])
    for anchor in source_style["anchors"]:
        assert anchor["dimension"] in DIMENSIONS
        assert anchor["confidence"] in {"high", "medium", "low"}
        assert (ROOT / anchor["evidence"]).is_file()
    ids = set()
    for slide in slides:
        assert slide["id"] not in ids
        ids.add(slide["id"])
        assert slide["role"] in ROLES and slide["claim"] and slide["layout"]
        assert slide["on_slide"] and slide["speaker_notes"]
        assert slide["evidence"]
        for item in slide["evidence"]:
            assert item["status"] in STATUSES
            assert (ROOT / item["source"]).is_file()
        if slide["figure_ref"]:
            assert (ROOT / slide["figure_ref"]).is_file()
    print(f"PASS {path.name}: {len(slides)} slides, {len(source_style['anchors'])} style anchors")


if __name__ == "__main__":
    validate(EXAMPLE)
