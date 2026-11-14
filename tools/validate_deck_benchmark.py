#!/usr/bin/env python3
"""Validate DECK01 v7.6 claims, evidence cards, notes and rendered PDF."""
from __future__ import annotations

from pptx import Presentation
from pptx.util import Inches
from pypdf import PdfReader

from build_deck_benchmark import OUTPUT, ROOT, SPEC
import json


def main():
    contract = json.loads(SPEC.read_text(encoding="utf-8"))
    deck = Presentation(OUTPUT)
    assert len(deck.slides) == 3
    slide_text = [
        "\n".join(shape.text for shape in slide.shapes if getattr(shape, "has_text_frame", False))
        for slide in deck.slides
    ]
    for slide_spec, slide, visible in zip(contract["slides"], deck.slides, slide_text):
        if slide_spec["role"] != "method":
            assert slide_spec["claim"] in visible
        assert all(value in visible for value in slide_spec["on_slide"])
        assert slide_spec["speaker_notes"] in slide.notes_slide.notes_text_frame.text

    assert all(value in slide_text[1] for value in ("OCF / notch filter", "Energy-assisted module", "Dense", "fault class"))
    squares = [shape for shape in deck.slides[1].shapes
               if abs(shape.left / 914400 - 8.90) < .01
               and abs(shape.width / 914400 - .13) < .01
               and abs(shape.height / 914400 - .13) < .01]
    assert len(squares) == 5
    assert all(str(square.fill.fore_color.rgb) == ("DCA16C" if index == 1 else "FFFFFF")
               for index, square in enumerate(squares))

    boundary = contract["slides"][2]
    assert len(boundary["evidence_blocks"]) == 3
    s03 = deck.slides[2]
    names = {shape.name for shape in s03.shapes}
    assert all(f"s03_card_{index}" in names for index in range(1, 4))
    assert all(value in slide_text[2] for value in (
        "SOURCE-VISIBLE ROUTES", "SCHEMATIC SUBSTITUTIONS", "HUMAN REVIEW STILL REQUIRED",
        "18", "5  frequency-band panel", "1  Total graph → Input", "12  SEANet diagnosis panel",
        "Independent domain review", "Projection / final-size readability", "PowerPoint 2016 host round trip"
    ))

    # Evidence-card text must remain inside the slide and must not overlap other text boxes.
    text_shapes = [shape for shape in s03.shapes if shape.has_text_frame and shape.text.strip()]
    for shape in text_shapes:
        assert shape.left >= 0 and shape.top >= 0
        assert shape.left + shape.width <= deck.slide_width
        assert shape.top + shape.height <= deck.slide_height
    overlaps = []
    for index, a in enumerate(text_shapes):
        for b in text_shapes[index + 1:]:
            iw = max(0, min(a.left + a.width, b.left + b.width) - max(a.left, b.left))
            ih = max(0, min(a.top + a.height, b.top + b.height) - max(a.top, b.top))
            if iw > Inches(.03) and ih > Inches(.03):
                overlaps.append((a.name, b.name))
    assert not overlaps, f"DECK01_EVIDENCE_CARD_TEXT_OVERLAPS:{overlaps}"

    pdf_path = ROOT / "dist/DECK01_c01_defense_v76.pdf"
    pdf = PdfReader(pdf_path)
    assert len(pdf.pages) == 3
    pdf_text = pdf.pages[2].extract_text() or ""
    assert "SOURCE-VISIBLE ROUTES" in pdf_text and "18" in pdf_text
    assert "PowerPoint 2016 host round trip" in pdf_text
    for page in range(1, 4):
        assert (ROOT / f"dist/DECK01_c01_defense_v76_slide_{page}.png").is_file()
    print("PASS DECK01 v7.6: 3-slide narrative, 18 source-visible routes, 3 evidence cards, PDF and PNGs")


if __name__ == "__main__":
    main()
