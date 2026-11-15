#!/usr/bin/env python3
"""Validate source-visible C01-FBG v7.4 labels, frequency direction and editability."""
from __future__ import annotations
import json
from pathlib import Path
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from scientific_ir import ROOT, validate_spec

SPEC=ROOT/"figure_specs/c01/C01_FBG_construction_v74.json"
SVG=ROOT/"examples/C01_FBG_construction_v74.svg"
PPTX=ROOT/"dist/C01_FBG_construction_v74.pptx"


def _descr(shape):
    for node in shape._element.iter():
        if node.tag.endswith("}cNvPr"):
            return node.get("descr")
    return None


def validate():
    spec=json.loads(SPEC.read_text(encoding="utf-8"))
    validate_spec(spec)
    labels=[e.get("text","") for e in spec["elements"] if e["type"]=="text"]
    required=[
        "Graph Construction (Time-Frequency Graph)",
        "Band-pass filters","Total graph","OCF","Notch filter",
        "operational component\nremoved","Sub graph 1:\\n1st band",
        "Sub graph 2:\\n2nd band","Sub graph 3:\\n3rd band","Sub graph N:\\nNth band",
        "Frequency","Fault sensitivity cues clearer (qualitative)"
    ]
    normalized={label.casefold().replace("\\r\\n","\\n") for label in labels}
    missing=[label for label in required if label.casefold().replace("\\r\\n","\\n") not in normalized]
    assert not missing, missing
    assert sum(label=="Fault sensitivity" for label in labels)==2
    graphs=[e for e in spec["elements"] if e["type"]=="graph"]
    assert len(graphs)==5, "four frequency-band subgraphs plus total graph required"
    assert sum(e["type"]=="line" and e.get("arrow") and e.get("id")=="el_0045" for e in spec["elements"])==1
    assert "Frequency-band graph (FBG) construction" in labels
    assert "Exact numerical frequency cutoffs" in spec["figure_contract"]["unverified"]
    assert all(e["type"]!="image" for e in spec["elements"])
    assert SVG.is_file() and PPTX.is_file()
    deck=Presentation(PPTX)
    assert len(deck.slides)==1
    shapes=list(deck.slides[0].shapes)
    assert not any(s.shape_type==MSO_SHAPE_TYPE.PICTURE for s in shapes)
    missing=[s.name for s in shapes if not (_descr(s) or "").strip()]
    assert not missing, "MISSING_ALT_TEXT:"+",".join(missing)
    oob=[s.name for s in shapes if s.left<0 or s.top<0 or s.left+s.width>deck.slide_width or s.top+s.height>deck.slide_height]
    assert not oob, "OBJECTS_OUT_OF_BOUNDS:"+",".join(oob)
    return {"status":"PASS","spec_elements":len(spec["elements"]),"pptx_shapes":len(shapes),
            "picture_count":0,"alt_text_coverage":1.0,"band_subgraphs":4,
            "total_graph_layers":1,"frequency_axis":True,"fault_sensitivity_cues":2,
            "source_title_preserved":True,"numerical_cutoffs_asserted":False}


if __name__=="__main__":
    print(json.dumps(validate(),ensure_ascii=False,indent=2))
