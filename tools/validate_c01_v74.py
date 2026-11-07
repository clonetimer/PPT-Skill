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
        "gcn_2": "GCN", "pooling_2": "pooling", "sr_main": "SR",
        "ea": "Energy-assisted module", "sr_ea": "SR", "sum": "+",
    }
    assert labels == expected, (labels, expected)
    expected_edges = {
        ("input", "gcn_1"), ("gcn_1", "pooling_1"),
        ("pooling_1", "gcn_2"), ("gcn_2", "pooling_2"),
        ("pooling_2", "sr_main"), ("sr_main", "sum"),
        ("input", "ea"), ("ea", "sr_ea"), ("sr_ea", "sum"),
    }
    expected_edges |= {("ocf", "band_group")}
    expected_edges |= {(f"band_{i}", "total_graph") for i in range(1, 5)}
    assert {tuple(edge) for edge in spec["semantic_edges"]} == expected_edges
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
