#!/usr/bin/env python3
"""Enforce explicit presentation profile and publication target prerequisites."""
from __future__ import annotations

import json

from scientific_ir import ROOT


def validate_publication_target(target, publication_profile):
    missing = [key for key in publication_profile["requires_before_build"] if not target.get(key)]
    assert not missing, f"Publication target missing: {missing}"
    assert target["final_width_mm"] > 0 and target["final_height_mm"] > 0
    assert target["minimum_text_pt"] > 0 and target["raster_resolution_dpi"] > 0


def main():
    config = json.loads((ROOT / "specs/output_profiles_v76.json").read_text(encoding="utf-8"))
    presentation = config["profiles"]["presentation"]
    publication = config["profiles"]["publication"]
    specs = sorted((ROOT / "figure_specs").rglob("*.json"))
    for path in specs:
        spec = json.loads(path.read_text(encoding="utf-8"))
        mode = spec["figure_contract"]["output_mode"]
        assert mode in {"presentation", "publication"}
        if mode == "publication":
            validate_publication_target(spec.get("publication_target", {}), publication)
        else:
            assert [round(spec["canvas"]["width_in"], 3), spec["canvas"]["height_in"]] == presentation["canvas_in"]
            texts = [e for e in spec["elements"] if e["type"] == "text"]
            assert texts
            for e in texts:
                is_note = any(token in e["text"].lower() for token in
                              ("doi", "cc by", "source-visible", "not a numerical", "lee et al."))
                minimum = presentation["source_note_min_pt"] if is_note else presentation["critical_text_min_pt"]
                assert e.get("size", 14) >= minimum, (spec["id"], e["text"], minimum)
    print(f"PASS output profiles: {len(specs)} presentation figures; publication requires target-specific contract")


if __name__ == "__main__":
    main()
