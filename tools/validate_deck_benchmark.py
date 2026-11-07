#!/usr/bin/env python3
"""Check the benchmark deck's ordered claims and source boundaries."""
from __future__ import annotations

import json

from pptx import Presentation
from pypdf import PdfReader

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
    assert all(value in text[1] for value in ("OCF / notch filter", "Energy-assisted module", "Dense"))
    assert "schematic" in text[2].lower() and "numerical adjacency" in text[2].lower()
    pdf = PdfReader(ROOT / "dist/DECK01_c01_defense.pdf")
    assert len(pdf.pages) == 3
    assert "Dense" in (pdf.pages[1].extract_text() or "")
    print("PASS DECK01: ordered claims, source boundary, editable 3-slide output")


if __name__ == "__main__":
    main()
