#!/usr/bin/env python3
"""Shared evidence and geometry contract for scientific FigureSpecs."""
from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path

from chart_contract import canonical_chart_spec_digest

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = json.loads((ROOT / "specs/figure_contracts_v76.json").read_text(encoding="utf-8"))
PRIMITIVES = {"text", "rect", "line", "polyline", "ellipse", "trapezoid", "sensor", "graph", "grid", "stack_grid", "image"}


def semantic_role(element: dict) -> str:
    if element.get("semantic_id"):
        return "scientific_label" if element["type"] == "text" else "scientific_object"
    return {"line": "connector", "polyline": "trace", "graph": "schematic_graph",
            "sensor": "schematic_sensor", "grid": "schematic_grid", "stack_grid": "schematic_grid",
            "text": "annotation", "image": "source_image"}.get(element["type"], "layout_shape")


def enrich_spec(source: dict) -> dict:
    """Freeze provenance fields without changing existing drawing geometry."""
    spec = copy.deepcopy(source)
    contract = CONTRACTS[spec["id"]]
    spec["schema_version"] = "7.6.0-dev"
    spec["figure_contract"] = {k: contract[k] for k in ("claim", "archetype", "output_mode", "unverified")}
    spec["evidence_records"] = [{
        "id": "source_1", "source": contract["source"],
        "source_file_sha256": hashlib.sha256((ROOT / contract["source"]).read_bytes()).hexdigest(),
        "source_locator": contract["source_locator"],
        "status": contract["evidence_status"], "scope": contract["evidence_scope"],
        "reuse": contract.get("reuse", "derivative_redraw_only")
    }]
    for index, element in enumerate(spec["elements"], 1):
        element["id"] = f"el_{index:04d}"
        element["semantic_role"] = semantic_role(element)
        element["evidence_ref"] = "source_1"
    return spec


def validate_spec(spec: dict) -> None:
    assert spec["schema_version"] == "7.6.0-dev"
    assert spec["id"] in CONTRACTS
    contract = spec["figure_contract"]
    assert contract["claim"] and contract["output_mode"] in {"presentation", "publication"}
    evidence = {record["id"]: record for record in spec["evidence_records"]}
    assert evidence and len(evidence) == len(spec["evidence_records"])
    for record in evidence.values():
        source = ROOT / record["source"]
        assert source.is_file()
        assert record["source_file_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
        assert record["source_locator"]
        assert record["status"] in {"source_visible_redraw", "paper_grounded", "domain_adaptation", "data_driven"}
        assert record["scope"] and record["reuse"]
    if contract["archetype"] == "quantitative_grid":
        lineage = spec["data_lineage"]
        chart_spec = ROOT / lineage["chart_spec"]
        assert chart_spec.is_file() and lineage["chart_spec_sha256"] == canonical_chart_spec_digest(chart_spec)
        assert any(record["source"] == lineage["data_ref"] and
                   record["source_file_sha256"] == lineage["sha256"]
                   for record in evidence.values())
    ids = set()
    semantic_ids = set()
    for element in spec["elements"]:
        assert element["type"] in PRIMITIVES
        assert element["id"] and element["id"] not in ids
        ids.add(element["id"])
        assert element["semantic_role"] and element["evidence_ref"] in evidence
        if element.get("semantic_id"):
            assert element["semantic_id"] not in semantic_ids or element["type"] in {"graph", "rect"}
            semantic_ids.add(element["semantic_id"])
    for edge in spec.get("semantic_edges", []):
        assert len(edge) == 2 and edge[0] in semantic_ids and edge[1] in semantic_ids


def distance_to_box(x: float, y: float, box: tuple[float, float, float, float]) -> float:
    left, top, right, bottom = box
    return math.hypot(max(left - x, 0, x - right), max(top - y, 0, y - bottom))


def semantic_boxes(spec: dict) -> dict[str, tuple[float, float, float, float]]:
    boxes = {}
    for e in spec["elements"]:
        sid = e.get("semantic_id")
        if sid and all(k in e for k in ("x", "y", "w", "h")):
            box = (e["x"], e["y"], e["x"] + e["w"], e["y"] + e["h"])
            if sid in boxes:
                a = boxes[sid]
                box = (min(a[0], box[0]), min(a[1], box[1]), max(a[2], box[2]), max(a[3], box[3]))
            boxes[sid] = box
    return boxes


def validate_drawn_routes(spec: dict, expected_edges: set[tuple[str, str]], tolerance: float = .23) -> None:
    """Check visible line segments, direction, route continuity, and end nodes."""
    lines = {}
    for e in spec["elements"]:
        if e.get("semantic_link"):
            assert e["type"] == "line" and e.get("arrow"), e["id"]
            lines.setdefault(e["semantic_link"], []).append(e)
    assert set(lines) == {f"{a}__{b}" for a, b in expected_edges}
    boxes = semantic_boxes(spec)
    for source, target in expected_edges:
        route = lines[f"{source}__{target}"]
        assert source in boxes and target in boxes
        assert distance_to_box(route[0]["x1"], route[0]["y1"], boxes[source]) <= tolerance, (source, "start")
        assert distance_to_box(route[-1]["x2"], route[-1]["y2"], boxes[target]) <= tolerance, (target, "end")
        for first, second in zip(route, route[1:]):
            assert math.hypot(first["x2"] - second["x1"], first["y2"] - second["y1"]) <= tolerance, (source, target, "break")


def validate_expected_topology(spec: dict, topology: dict) -> None:
    assert spec["id"] == topology["figure_id"]
    labels = {e["semantic_id"]: e["text"] for e in spec["elements"]
              if e.get("semantic_id") and e["type"] == "text"}
    assert all(labels.get(key) == value for key, value in topology["critical_labels"].items())
    critical = {tuple(edge) for edge in topology["critical_edges"]}
    assert critical <= {tuple(edge) for edge in spec["semantic_edges"]}
    validate_drawn_routes(spec, critical)
