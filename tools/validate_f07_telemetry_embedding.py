#!/usr/bin/env python3
"""Validate F07's stated 221/1600 tensor counts and explicit schematic boundary."""
from __future__ import annotations
import json
from pathlib import Path
from scientific_ir import ROOT, validate_spec

SPEC=ROOT/"figure_specs/F07_telemetry_embedding.json"

def validate():
    spec=json.loads(SPEC.read_text(encoding="utf-8"))
    validate_spec(spec)
    labels=[e.get("text","") for e in spec["elements"] if e["type"]=="text"]
    assert "xₜ ∈ ℝ²²¹" in labels
    assert "N = 221 selected parameters" in labels
    assert "221 valid channels\n1,379 zero-padding cells" in labels
    assert "40 × 40 feature grid" in labels
    assert "L = 5 · stride = 1" in labels
    assert any("no channel-to-cell mapping is asserted" in x.lower() for x in labels)
    assert any("illustrative ordering" in x.lower() for x in labels)
    grids=[e for e in spec["elements"] if e["type"] in {"grid","stack_grid"}]
    assert len(grids)==2 and all(e["rows"]==40 and e["cols"]==40 for e in grids)
    assert grids[1]["layers"]==5
    return {"status":"PASS","selected_parameters":221,"grid_cells":1600,
            "padding_cells":1379,"temporal_layers":5,
            "channel_mapping":"explicitly schematic; no per-channel coordinate claim"}

if __name__=="__main__":
    print(json.dumps(validate(),ensure_ascii=False,indent=2))
