#!/usr/bin/env python3
"""Validate B01 timing disclosure and the bounded engineering-state semantics."""
from __future__ import annotations
import json
from pathlib import Path
from scientific_ir import ROOT, validate_spec

SPEC = ROOT / "figure_specs/B01_engineering_fdir.json"


def validate():
    spec=json.loads(SPEC.read_text(encoding="utf-8"))
    validate_spec(spec)
    labels=[e.get("text","") for e in spec["elements"] if e["type"]=="text"]
    assert not any("0.1 s" in text for text in labels), "UNSUPPORTED_MISSION_TIMING_LABEL_REMAINS"
    assert any("no mission-specific timing is asserted" in text.lower() for text in labels), "TIMING_BOUNDARY_DISCLOSURE_MISSING"
    required=("NORMAL","RECONFIG","DEGRADED","SAFE","Fault confirmed","Reconfig. authorized","safety / resource guard")
    joined="\n".join(labels)
    assert all(label in joined for label in required)
    assert len([e for e in spec["elements"] if e["type"]=="line" and e.get("arrow")]) >= 3
    return {"status":"PASS","unsupported_timing_claims":0,"timing_boundary_disclosed":True,
            "mode_states":["NORMAL","RECONFIG","DEGRADED","SAFE"],
            "state_transition_semantics":"Only visible labels and arrows are asserted; exact guard predicates and authority roles remain unspecified."}


if __name__=="__main__":
    print(json.dumps(validate(),ensure_ascii=False,indent=2))
