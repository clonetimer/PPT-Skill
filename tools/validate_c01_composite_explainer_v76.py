#!/usr/bin/env python3
"""Validate the two-slide C01 explainer companion and cross-slide Total graph -> Input cue."""
from __future__ import annotations
import json
from pathlib import Path
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from scientific_ir import ROOT

PPTX=ROOT/"dist/C01_composite_explainer_v76.pptx"
PDF=ROOT/"dist/C01_composite_explainer_v76.pdf"
PAGES=[ROOT/f"dist/C01_composite_explainer_v76_slide_{i}.png" for i in (1,2)]


def descr(shape):
    for node in shape._element.iter():
        if node.tag.endswith("}cNvPr"): return node.get("descr")
    return None


def validate():
    deck=Presentation(PPTX)
    assert len(deck.slides)==2
    assert abs(deck.slide_width/deck.slide_height-16/9)<.002
    expected=[
        ("Graph Construction (Time-Frequency Graph)","Frequency-band graph (FBG) construction","Next: Total graph → Input on slide 2"),
        ("Graph-level fault diagnosis framework","fault class","Input on this slide = Total graph constructed on slide 1"),
    ]
    counts=[]
    for index,(slide,terms) in enumerate(zip(deck.slides,expected),1):
        text="\n".join(s.text for s in slide.shapes if s.has_text_frame)
        assert all(term in text for term in terms), (index,terms)
        assert not any(s.shape_type==MSO_SHAPE_TYPE.PICTURE for s in slide.shapes)
        missing=[s.name for s in slide.shapes if not (descr(s) or "").strip()]
        assert not missing, f"SLIDE_{index}_ALT_TEXT_MISSING:{missing}"
        oob=[s.name for s in slide.shapes if s.left<0 or s.top<0 or s.left+s.width>deck.slide_width or s.top+s.height>deck.slide_height]
        assert not oob, f"SLIDE_{index}_OUT_OF_BOUNDS:{oob}"
        notes=slide.notes_slide.notes_text_frame.text
        assert "Accessibility description and reading order" in notes
        counts.append(len(slide.shapes))
    assert PDF.is_file() and all(path.is_file() for path in PAGES)
    from pypdf import PdfReader
    assert len(PdfReader(PDF).pages)==2
    return {"status":"PASS","slide_count":2,"shapes_per_slide":counts,
            "picture_count":0,"alt_text_coverage":1.0,
            "cross_slide_route":"Total graph on slide 1 -> Input on slide 2",
            "pdf_pages":2,"preview_pages":2}


if __name__=="__main__":
    print(json.dumps(validate(),ensure_ascii=False,indent=2))
