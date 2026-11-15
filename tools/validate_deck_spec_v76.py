#!/usr/bin/env python3
"""Validate the v7.6 DeckSpec and its source-backed evidence cards."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "specs/deck_spec_v76.example.json"
SCHEMA = ROOT / "specs/deck_spec_v76.schema.json"
ROLES = {"research_question", "problem", "prior_work", "framework", "method", "experiment", "result", "ablation", "conclusion", "evidence_boundary"}
STATUSES = {"source_visible", "paper_grounded", "verified_artifact", "unverified"}
DIMENSIONS = {"layout", "components", "connectors", "palette", "typography", "iconography", "surface", "density"}


def validate(path: Path = EXAMPLE):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    try:
        import jsonschema
    except ImportError:
        pass
    else:
        jsonschema.validate(data, schema)
    assert data["schema_version"] == "7.6.0-dev"
    deck, slides, source_style, style = data["deck"], data["slides"], data["source_style"], data["style"]
    assert deck["topic"] and deck["audience"] and deck["duration_minutes"] > 0
    assert deck["target_slide_count"] == len(slides) and deck["narrative"]
    assert deck["style_ref"] == style["id"] and style["source_style_ref"] == source_style["id"]
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
        assert slide["on_slide"] and slide["speaker_notes"] and slide["evidence"]
        for item in slide["evidence"]:
            assert item["status"] in STATUSES
            assert (ROOT / item["source"]).is_file()
        if slide["figure_ref"]:
            assert (ROOT / slide["figure_ref"]).is_file()
        if slide.get("topology_ref"):
            assert slide.get("figure_ref"), "topology_ref requires a figure_ref"
            assert (ROOT / slide["topology_ref"]).is_file()
    boundary = next(slide for slide in slides if slide["role"] == "evidence_boundary")
    assert len(boundary["evidence_blocks"]) == 3
    assert [block["metric"] for block in boundary["evidence_blocks"]] == ["18", "3", "3"]
    assert sum("5  frequency-band panel" in x for x in boundary["evidence_blocks"][0]["items"]) == 1
    assert any("PowerPoint 2016 host round trip" in x for x in boundary["evidence_blocks"][2]["items"])
    print(f"PASS {Path(path).name}: {len(slides)} slides, 3 evidence-boundary cards")


if __name__ == "__main__":
    validate()
