#!/usr/bin/env python3
"""Build the three-slide C01 defense benchmark from DeckSpec and FigureSpec output."""
from __future__ import annotations

import json
from copy import deepcopy

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from scientific_ir import ROOT
from render_figure_spec import clean_theme

SPEC = ROOT / "specs/deck_spec_v75.example.json"
OUTPUT = ROOT / "dist/DECK01_c01_defense.pptx"
METHOD = ROOT / "dist/C01_composite_defense_slide_v74.pptx"


def text(slide, value, x, y, w, h, size, bold=False, color="28343C"):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = shape.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = Inches(.02)
    frame.margin_top = Inches(.02)
    paragraph = frame.paragraphs[0]
    paragraph.alignment = PP_ALIGN.LEFT
    run = paragraph.add_run()
    run.text = value
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)


def make_page(slide, number, role, title, claim, points, note):
    text(slide, f"{number:02d}  {role.upper()}", .68, .46, 6.4, .35, 12, True, "687780")
    text(slide, title, .68, 1.10, 12.0, .68, 28, True)
    text(slide, claim, .68, 2.04, 11.8, .68, 20)
    for index, point in enumerate(points):
        text(slide, f"{index+1:02d}  {point}", 1.00, 3.16+index*.73, 10.8, .48, 16)
    text(slide, note, .68, 6.82, 12.0, .32, 10, color="687780")


def main():
    contract = json.loads(SPEC.read_text(encoding="utf-8"))
    assert contract["deck"]["target_slide_count"] == len(contract["slides"]) == 3
    assert [slide["role"] for slide in contract["slides"]] == ["problem", "method", "evidence_boundary"]
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]
    s01, s02, s03 = (prs.slides.add_slide(blank) for _ in range(3))
    make_page(s01, 1, "problem", "Why frequency-aware sensor fusion?",
              contract["slides"][0]["claim"], contract["slides"][0]["on_slide"],
              "Lee et al., EAAI 179 (2026), 115273 · DOI 10.1016/j.engappai.2026.115273")
    method = Presentation(METHOD)
    assert len(method.slides) == 1
    for shape in method.slides[0].shapes:
        s02.shapes._spTree.insert_element_before(deepcopy(shape.element), 'p:extLst')
    make_page(s03, 3, "evidence boundary", "What the redraw establishes",
              contract["slides"][2]["claim"], contract["slides"][2]["on_slide"],
              "Sensor glyphs and exact graph adjacency are schematic · source topology checked")
    for slide, slide_spec in zip(prs.slides, contract["slides"]):
        slide.notes_slide.notes_text_frame.text = slide_spec["speaker_notes"]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(OUTPUT)
    clean_theme(OUTPUT)
    print(f"Built {OUTPUT.relative_to(ROOT)}: {len(prs.slides)} editable slides")


if __name__ == "__main__":
    main()
