#!/usr/bin/env python3
"""Validate the frozen C01 composite source, semantics, and editable output."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from pptx import Presentation

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "figure_specs/c01/C01_composite_defense_slide.json"
SVG = ROOT / "examples/C01_composite_defense_slide_v74.svg"
PPTX = ROOT / "dist/C01_composite_defense_slide_v74.pptx"


def main():
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    assert spec["version"] == "7.4.0"
    assert spec["canvas"] == {"width_in": 13.333, "height_in": 7.5}
    labels = {e["semantic_id"]: e["text"] for e in spec["elements"]
              if e.get("semantic_id") and e["type"] == "text"}
    expected = {
        "ocf": "OCF / notch filter", "band_group": "Band subgraphs", "total_graph": "Total graph",
        "band_1": "B₁", "band_2": "B₂", "band_3": "B₃", "band_4": "Bq",
        "input": "Input", "gcn_1": "GCN", "pooling_1": "pooling",
        "gcn_2": "GCN", "pooling_2": "pooling", "sr_main": "IR layer",
        "ea": "Energy-assisted module", "sr_ea": "IR layer", "sum": "+", "dense": "Dense",
    }
    assert labels == expected, (labels, expected)
    expected_edges = {
        ("input", "gcn_1"), ("gcn_1", "pooling_1"),
        ("pooling_1", "gcn_2"), ("gcn_2", "pooling_2"),
        ("pooling_2", "sr_main"), ("sr_main", "sum"),
        ("input", "ea"), ("ea", "gcn_1"),
        ("pooling_1", "sr_ea"), ("sr_ea", "sum"), ("sum", "dense"),
    }
    expected_edges |= {("ocf", "band_group")}
    expected_edges |= {("total_graph", "input")}
    expected_edges |= {(f"band_{i}", "total_graph") for i in range(1, 5)}
    assert {tuple(edge) for edge in spec["semantic_edges"]} == expected_edges
    assert "band-pass filters" in [e.get("text") for e in spec["elements"]]
    assert "Fault cues clearer" in [e.get("text") for e in spec["elements"]]
    assert "Frequency" in [e.get("text") for e in spec["elements"]]
    assert any(e["type"]=="line" and e.get("arrow") and e.get("x1")==e.get("x2")
               and abs(e["x1"]-8.97)<1e-6 for e in spec["elements"])
    pooling=[e for e in spec["elements"] if e["type"]=="polygon" and e.get("semantic_id") in {"pooling_1","pooling_2"}]
    assert len(pooling)==2 and all(len(e["points"])==4 for e in pooling)
    for shape in pooling:
        assert abs(shape["points"][1][1]-shape["points"][0][1])>.05
        assert abs(shape["points"][2][1]-shape["points"][3][1])>.05
    labels_text=" ".join(e.get("text","") for e in spec["elements"])
    assert "public abstract uses SR" in labels_text and "unresolved" in labels_text.lower()
    total_layers = [e for e in spec["elements"] if e["type"] == "graph"
                    and e.get("semantic_id") == "total_graph"]
    interband_links = [e for e in spec["elements"] if e["type"] == "line"
                       and e.get("dash") and 7.3 <= e["x1"] <= 8.8]
    assert len(total_layers) == 4 and len(interband_links) == 9
    assert all(e["type"] != "image" for e in spec["elements"])
    assert SVG.exists() and PPTX.exists()
    deck = Presentation(PPTX)
    assert len(deck.slides) == 1
    texts = [shape.text for shape in deck.slides[0].shapes if getattr(shape, "has_text_frame", False)]
    for value in expected.values():
        assert value in texts, value
    subprocess.run([sys.executable, str(ROOT / "tools/validate_svg_examples.py"), str(SVG)], check=True)
    subprocess.run([sys.executable, str(ROOT / "tools/audit_pptx.py"), str(PPTX), "--strict"], check=True)
    print("PASS C01 V7.4 semantic topology and editable outputs")


if __name__ == "__main__":
    main()
