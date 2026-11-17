#!/usr/bin/env python3
"""Load and hash-lock a DeckSpec slide's source FigureSpec and topology contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _resolve(root: Path, relative: str) -> Path:
    base = Path(root).resolve()
    candidate = (base / relative).resolve()
    if not candidate.is_relative_to(base):
        raise ValueError(f"SOURCE_FIGURE_PATH_ESCAPES_ROOT:{relative}")
    return candidate


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_source_figure_contract(root: Path, slide: dict) -> dict | None:
    """Return a reproducible source-figure lock; speaker notes are never copied here."""
    figure_ref = slide.get("figure_ref")
    if not figure_ref:
        if slide.get("topology_ref"):
            raise ValueError("TOPOLOGY_REF_REQUIRES_FIGURE_REF")
        return None

    figure_path = _resolve(root, figure_ref)
    if not figure_path.is_file():
        raise FileNotFoundError(f"SOURCE_FIGURE_SPEC_MISSING:{figure_ref}")
    figure_spec = json.loads(figure_path.read_text(encoding="utf-8"))

    topology_ref = slide.get("topology_ref")
    topology_path = _resolve(root, topology_ref) if topology_ref else None
    topology = {}
    if topology_path:
        if not topology_path.is_file():
            raise FileNotFoundError(f"SOURCE_TOPOLOGY_MISSING:{topology_ref}")
        topology = json.loads(topology_path.read_text(encoding="utf-8"))

    critical_labels = topology.get("critical_labels") or {
        element.get("semantic_id"): element.get("text", "")
        for element in figure_spec.get("elements", [])
        if element.get("type") == "text" and element.get("semantic_id")
    }
    critical_edges = topology.get("critical_edges") or figure_spec.get("semantic_edges", [])
    required_nodes = topology.get("required_nodes", [])
    geometry_contract = topology.get("geometry_contract", {})
    readout_discrepancy = topology.get("readout_label_discrepancy", "")

    overridden_ids = set(critical_labels)
    source_text = []
    seen = set()
    for element in figure_spec.get("elements", []):
        if element.get("type") != "text":
            continue
        if element.get("semantic_id") in overridden_ids:
            continue
        value = str(element.get("text", "")).strip()
        if not value:
            continue
        # V7.4 prose says "SR paths"; V7.5 preserves the source-visible
        # author-lab label "IR layer" and records the public-abstract discrepancy separately.
        if readout_discrepancy and "SR" in value:
            continue
        if value not in seen:
            source_text.append(value)
            seen.add(value)
    for value in critical_labels.values():
        value = str(value).strip()
        if value and value not in seen:
            source_text.append(value)
            seen.add(value)

    return {
        "figure_spec_ref": figure_ref,
        "figure_spec_sha256": _sha256(figure_path),
        "figure_id": str(figure_spec.get("id", "")),
        "figure_version": str(figure_spec.get("version", "")),
        "topology_ref": topology_ref,
        "topology_sha256": _sha256(topology_path) if topology_path else None,
        "source_text": source_text,
        "critical_labels": critical_labels,
        "critical_edges": critical_edges,
        "required_nodes": required_nodes,
        "geometry_contract": geometry_contract,
        "readout_label_discrepancy": readout_discrepancy,
    }
