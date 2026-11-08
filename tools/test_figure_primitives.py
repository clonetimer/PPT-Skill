"""Regression check for source-figure polygons and rotated labels in PPTX."""
from pathlib import Path
from tempfile import TemporaryDirectory

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from render_figure_spec import render

spec={
    "canvas":{"width_in":4,"height_in":3},
    "style":{"font":"Arial"},
    "elements":[
        {"type":"polygon","points":[(.5,.5),(2.0,.8),(2.0,2.1),(.5,2.4)],
         "fill":"#DDDDFF","stroke":"#333333","sw":1},
        {"type":"text","text":"392×392","x":2.4,"y":1.0,"w":.8,"h":.2,
         "rotation":-90,"size":10,"color":"#333333"},
    ],
}

with TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/".testtmp") as d:
    svg=Path(d)/"figure.svg";pptx=Path(d)/"figure.pptx"
    render(spec,svg,pptx)
    slide=Presentation(pptx).slides[0]
    polygon=next(s for s in slide.shapes if s.shape_type==MSO_SHAPE_TYPE.FREEFORM)
    assert abs(polygon.width/914400-1.5)<.002
    assert abs(polygon.height/914400-1.9)<.002
    # The custom geometry must have four non-rectangular vertices, not the
    # accidental 1-inch square produced by premature integer rounding.
    xml=polygon._element.xml
    assert 'x="1500" y="300"' in xml or 'x="1500" y="300"' in xml.replace("\n","")
    label=next(s for s in slide.shapes if s.has_text_frame and s.text=="392×392")
    assert abs(label.rotation-270)<.01 or abs(label.rotation+90)<.01
    assert '<polygon' in svg.read_text(encoding="utf-8")
print("Editable polygon and rotated text regression passed")
