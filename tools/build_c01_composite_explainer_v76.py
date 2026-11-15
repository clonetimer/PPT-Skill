#!/usr/bin/env python3
"""Create a two-slide enlarged presentation companion to the one-slide C01 overview."""
from __future__ import annotations

import json
import shutil
from copy import deepcopy
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from repair_case_artifacts import render_pptx, sha256_file
from render_figure_spec import clean_theme
from scientific_ir import ROOT

FBG = ROOT / "dist/C01_FBG_construction_v74.pptx"
SEANET = ROOT / "dist/C01_SEANet_graph_level_v74.pptx"
OUTPUT = ROOT / "dist/C01_composite_explainer_v76.pptx"
ACCEPTED = ROOT / "dist/accepted_repairs/C01_composite_explainer_v76.pptx"

DESCRIPTIONS = (
    "Slide 1 of 2: Graph Construction (Time-Frequency Graph), corresponding to frequency-band graph (FBG) construction in the paper. Sensor signals pass through OCF/notch filtering with qualitative fault-sensitivity cues; band-pass filters form ordinal frequency-band subgraphs that connect to a total graph. Waveforms and graph coordinates are schematic.",
    "Slide 2 of 2: SEANet graph-level diagnosis. The total graph constructed on slide 1 is the Input. The main GCN/pooling route and energy-assisted branch feed two sensitivity-aware readout (SR) paths, which are summed before Dense classification into five class outputs. Graph coordinates are schematic.",
)


def set_alt(shape, description: str):
    for node in shape._element.iter():
        if node.tag.endswith("}cNvPr"):
            node.set("descr", description)
            return


def add_footer(slide, value: str, description: str):
    shape = slide.shapes.add_textbox(Inches(.68), Inches(7.12), Inches(12.0), Inches(.20))
    shape.name = "C01_explainer_transition"
    frame = shape.text_frame
    frame.clear()
    frame.word_wrap = False
    frame.margin_left = Inches(.01)
    frame.margin_right = Inches(.01)
    frame.margin_top = Inches(0)
    frame.margin_bottom = Inches(0)
    paragraph = frame.paragraphs[0]
    paragraph.alignment = PP_ALIGN.LEFT
    run = paragraph.add_run()
    run.text = value
    run.font.name = "Times New Roman"
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(88, 103, 114)
    set_alt(shape, description)


def build(output: Path = OUTPUT) -> dict:
    if not FBG.is_file() or not SEANET.is_file():
        raise FileNotFoundError("C01_FBG_V74_OR_SEANET_V74_MISSING")
    fbg = Presentation(FBG)
    seanet = Presentation(SEANET)
    if len(fbg.slides) != 1 or len(seanet.slides) != 1:
        raise ValueError("C01_EXPLAINER_REQUIRES_TWO_SINGLE_SLIDE_SOURCE_FIGURES")
    if (fbg.slide_width, fbg.slide_height) != (seanet.slide_width, seanet.slide_height):
        raise ValueError("C01_EXPLAINER_SOURCE_CANVAS_MISMATCH")

    deck = Presentation()
    deck.slide_width = fbg.slide_width
    deck.slide_height = fbg.slide_height
    blank = deck.slide_layouts[6]
    slides = [deck.slides.add_slide(blank), deck.slides.add_slide(blank)]
    for target, source in zip(slides, (fbg.slides[0], seanet.slides[0])):
        for shape in source.shapes:
            target.shapes._spTree.insert_element_before(deepcopy(shape.element), "p:extLst")

    add_footer(
        slides[0],
        "Next: Total graph → Input on slide 2",
        "Transition cue: the total graph constructed on this slide becomes the Input on slide 2.",
    )
    add_footer(
        slides[1],
        "Input on this slide = Total graph constructed on slide 1",
        "Cross-slide semantic link: the SEANet Input is the total graph produced by the FBG construction on slide 1.",
    )

    # Give each slide's first visible title the complete slide-level description.
    for slide, description in zip(slides, DESCRIPTIONS):
        title_shape = next((s for s in slide.shapes if s.has_text_frame and s.text.strip()), None)
        if title_shape is not None:
            set_alt(title_shape, description)
        existing = slide.notes_slide.notes_text_frame.text
        slide.notes_slide.notes_text_frame.text = (
            existing + "\n\nAccessibility description and reading order: " + description
        ).strip()

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    deck.save(output)
    clean_theme(output)
    pdf, pages = render_pptx(output, ROOT / "dist" / "C01_explainer_render", "C01_composite_explainer_v76")
    if len(pages) != 2:
        raise AssertionError("C01_EXPLAINER_EXPECTS_TWO_RENDERED_PAGES")
    shutil.copy2(pdf, ROOT / "dist/C01_composite_explainer_v76.pdf")
    for index, page in enumerate(pages, 1):
        shutil.copy2(page, ROOT / f"dist/C01_composite_explainer_v76_slide_{index}.png")
    ACCEPTED.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(output, ACCEPTED)

    report = {
        "status": "PASS",
        "slide_count": len(deck.slides),
        "slides": [
            {"slide": 1, "source": str(FBG.relative_to(ROOT)), "description": DESCRIPTIONS[0]},
            {"slide": 2, "source": str(SEANET.relative_to(ROOT)), "description": DESCRIPTIONS[1]},
        ],
        "transition": "Total graph on slide 1 -> Input on slide 2",
        "pptx_sha256": sha256_file(output),
        "pdf_sha256": sha256_file(ROOT / "dist/C01_composite_explainer_v76.pdf"),
        "preview_pages": [f"dist/C01_composite_explainer_v76_slide_{i}.png" for i in (1,2)],
    }
    (ROOT / "dist/C01_composite_explainer_v76_build.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    build()
