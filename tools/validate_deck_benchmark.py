#!/usr/bin/env python3
"""Check the benchmark deck's ordered claims and source boundaries."""
from __future__ import annotations

import json

from pptx import Presentation

from build_deck_benchmark import OUTPUT, ROOT, SPEC


def main():
    contract = json.loads(SPEC.read_text(encoding="utf-8"))
    deck = Presentation(OUTPUT)
    assert len(deck.slides) == 3
    text = ["\n".join(shape.text for shape in slide.shapes if getattr(shape, "has_text_frame", False))
            for slide in deck.slides]
    for slide_spec, slide, slide_text in zip(contract["slides"], deck.slides, text):
        if slide_spec["role"] != "method":
            assert slide_spec["claim"] in slide_text
        assert all(value in slide_text for value in slide_spec["on_slide"])
        assert slide_spec["speaker_notes"] in slide.notes_slide.notes_text_frame.text
    assert "OCF / notch filter" in text[1] and "Energy-assisted module" in text[1]
    assert "schematic" in text[2].lower() and "numerical adjacency" in text[2].lower()
    assert (ROOT / "dist/DECK01_c01_defense.pdf").is_file()
    print("PASS DECK01: ordered claims, source boundary, editable 3-slide output")


if __name__ == "__main__":
    main()
