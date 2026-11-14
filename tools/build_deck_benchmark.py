#!/usr/bin/env python3
"""Build DECK01 v7.6 with an evidence boundary that distinguishes checked, schematic and pending claims."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from scientific_ir import ROOT
from render_figure_spec import clean_theme

SPEC = ROOT / "specs/deck_spec_v76.example.json"
OUTPUT = ROOT / "dist/DECK01_c01_defense_v76.pptx"
METHOD = ROOT / "dist/C01_composite_defense_slide_v75.pptx"
ACCENTS = ("668A9C", "6D9A8E", "B88E58")


def add_text(slide, value, x, y, w, h, size, bold=False, color="28343C",
             align=PP_ALIGN.LEFT, name=""):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        shape.name = name
    frame = shape.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = Inches(.02)
    frame.margin_right = Inches(.02)
    frame.margin_top = Inches(.02)
    frame.margin_bottom = Inches(.02)
    paragraph = frame.paragraphs[0]
    paragraph.alignment = align
    run = paragraph.add_run()
    run.text = value
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)
    return shape


def add_rect(slide, x, y, w, h, fill, line="D6DEE2", name=""):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h)
    )
    if name:
        shape.name = name
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor.from_string(fill)
    shape.line.color.rgb = RGBColor.from_string(line)
    shape.line.width = Pt(1)
    return shape


def make_problem_page(slide, slide_spec):
    add_text(slide, "01  PROBLEM", .68, .46, 6.4, .35, 12, True, "687780", name="s01_role")
    add_text(slide, "Why frequency-aware sensor fusion?", .68, 1.10, 12.0, .68, 28, True, name="s01_title")
    add_text(slide, slide_spec["claim"], .68, 2.04, 11.8, .68, 20, name="s01_claim")
    for index, point in enumerate(slide_spec["on_slide"]):
        add_text(slide, f"{index+1:02d}  {point}", 1.00, 3.16+index*.73, 10.8, .48, 16,
                 name=f"s01_point_{index+1}")
    add_text(slide, "Lee et al., EAAI 179 (2026), 115273 · DOI 10.1016/j.engappai.2026.115273",
             .68, 6.82, 12.0, .32, 10, color="687780", name="s01_source")


def make_evidence_page(slide, slide_spec):
    add_text(slide, "03  EVIDENCE BOUNDARY", .68, .46, 7.0, .35, 12, True, "687780",
             name="s03_role")
    add_text(slide, "What the redraw establishes", .68, 1.05, 12.0, .62, 28, True,
             name="s03_title")
    add_text(slide, slide_spec["claim"], .68, 1.86, 11.9, .55, 19,
             name="s03_claim")

    blocks = slide_spec["evidence_blocks"]
    x0, gap, width, y, height = .68, .28, 3.80, 2.72, 3.62
    for index, block in enumerate(blocks):
        x = x0 + index * (width + gap)
        accent = ACCENTS[index]
        add_rect(slide, x, y, width, height, "F6F8F9", "D7E0E4", f"s03_card_{index+1}")
        add_rect(slide, x, y, width, .075, accent, accent, f"s03_card_{index+1}_accent")
        add_text(slide, block["title"], x+.20, y+.24, width-.40, .34, 12, True,
                 accent, name=f"s03_card_{index+1}_title")
        add_text(slide, block["metric"], x+.20, y+.68, .75, .70, 30, True,
                 "28343C", name=f"s03_card_{index+1}_metric")
        add_text(slide, block["descriptor"], x+1.05, y+.72, width-1.25, .76, 12,
                 color="43525B", name=f"s03_card_{index+1}_descriptor")
        divider = slide.shapes.add_shape(
            MSO_SHAPE.LINE, Inches(x+.20), Inches(y+1.62),
            Inches(width-.40), Inches(0)
        )
        divider.name = f"s03_card_{index+1}_divider"
        divider.line.color.rgb = RGBColor.from_string("D7E0E4")
        divider.line.width = Pt(1)
        for item_index, item in enumerate(block["items"]):
            add_text(slide, f"•  {item}", x+.22, y+1.83+item_index*.48,
                     width-.44, .40, 12, color="28343C",
                     name=f"s03_card_{index+1}_item_{item_index+1}")

    add_text(
        slide,
        "CI checks editable structure and rendered consistency; it does not certify scientific approval or final-size legibility.",
        .68, 6.66, 12.0, .34, 10, color="687780", name="s03_footnote"
    )


def build(output_path: Path = OUTPUT) -> Path:
    contract = json.loads(SPEC.read_text(encoding="utf-8"))
    assert contract["schema_version"] == "7.6.0-dev"
    assert contract["deck"]["target_slide_count"] == len(contract["slides"]) == 3
    assert [slide["role"] for slide in contract["slides"]] == [
        "problem", "method", "evidence_boundary"
    ]
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]
    s01, s02, s03 = (prs.slides.add_slide(blank) for _ in range(3))
    make_problem_page(s01, contract["slides"][0])

    method = Presentation(METHOD)
    assert len(method.slides) == 1
    for shape in method.slides[0].shapes:
        s02.shapes._spTree.insert_element_before(deepcopy(shape.element), "p:extLst")
    s02.notes_slide.notes_text_frame.text = contract["slides"][1]["speaker_notes"]
    make_evidence_page(s03, contract["slides"][2])

    for slide, slide_spec in ((s01, contract["slides"][0]), (s03, contract["slides"][2])):
        slide.notes_slide.notes_text_frame.text = slide_spec["speaker_notes"]

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(output_path)
    clean_theme(output_path)
    print(f"Built {output_path}: {len(prs.slides)} editable slides")
    return output_path


def main():
    build()


if __name__ == "__main__":
    main()
