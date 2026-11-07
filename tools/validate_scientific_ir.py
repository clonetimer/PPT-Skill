#!/usr/bin/env python3
"""Validate evidence, typed elements, and independently specified C01 topology."""
from __future__ import annotations

import json
from pathlib import Path

from scientific_ir import ROOT, validate_expected_topology, validate_spec

SCHEMA = ROOT / "specs/figure_spec_v76.schema.json"
TOPOLOGY = ROOT / "specs/c01_expected_topology_v76.json"


def check_all():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    topology = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
    try:
        import jsonschema
    except ImportError:
        jsonschema = None
    paths = sorted((ROOT / "figure_specs").rglob("*.json"))
    assert len(paths) >= 5
    for path in paths:
        spec = json.loads(path.read_text(encoding="utf-8"))
        if jsonschema:
            jsonschema.validate(spec, schema)
        validate_spec(spec)
        if spec["id"] == topology["figure_id"]:
            validate_expected_topology(spec, topology)
        print(f"PASS {path.relative_to(ROOT)}: {len(spec['elements'])} evidence-linked elements")


if __name__ == "__main__":
    check_all()
