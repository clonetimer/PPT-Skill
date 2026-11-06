#!/usr/bin/env python3
"""Validate FigureSpec JSON and its SVG/native-PowerPoint outputs."""
from __future__ import annotations
import json, subprocess, sys, tempfile, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Inches

ROOT=Path(__file__).resolve().parents[1]
NS={"svg":"http://www.w3.org/2000/svg","a":"http://schemas.openxmlformats.org/drawingml/2006/main"}
A_NS="{http://schemas.openxmlformats.org/drawingml/2006/main}"

def validate_spec(path):
    spec=json.loads(path.read_text(encoding="utf-8"))
    w=float(spec["canvas"]["width_in"]); h=float(spec["canvas"]["height_in"])
    assert w>0 and h>0
    for i,e in enumerate(spec["elements"]):
        assert e["type"] in {"text","rect","line","grid","stack_grid"}, f"{path}: unsupported primitive {i}"
        if e["type"]=="line":
            for k in ("x1","x2"): assert 0<=float(e[k])<=w, f"{path}: x out of bounds at {i}"
            for k in ("y1","y2"): assert 0<=float(e[k])<=h, f"{path}: y out of bounds at {i}"
        else:
            x,y,ww,hh=[float(e[k]) for k in ("x","y","w","h")]
            assert x>=0 and y>=0 and ww>0 and hh>0 and x+ww<=w+1e-6 and y+hh<=h+1e-6, f"{path}: geometry out of bounds at {i}"
        if e["type"] in {"grid","stack_grid"}: assert int(e["rows"])>0 and int(e["cols"])>0
    return spec

def validate_outputs(path,spec,tmp):
    name=path.stem; svg=tmp/f"{name}.svg"; pptx=tmp/f"{name}.pptx"
    subprocess.run([sys.executable,str(ROOT/"tools"/"render_figure_spec.py"),str(path),"--svg",str(svg),"--pptx",str(pptx)],check=True)
    root=ET.parse(svg).getroot()
    assert root.tag.endswith("svg") and root.attrib.get("viewBox")
    assert root.find(".//svg:image",NS) is None and root.find(".//svg:foreignObject",NS) is None
    deck=Presentation(str(pptx)); assert len(deck.slides)==1
    slide=deck.slides[0]; pictures=0; oob=0; texts=[]
    for sh in slide.shapes:
        pictures += sh.shape_type==MSO_SHAPE_TYPE.PICTURE
        if sh.left<0 or sh.top<0 or sh.left+sh.width>deck.slide_width or sh.top+sh.height>deck.slide_height:oob+=1
        if getattr(sh,"has_text_frame",False) and sh.text.strip():texts.append(sh)
    overlaps=0
    for i,a in enumerate(texts):
        for b in texts[i+1:]:
            iw=max(0,min(a.left+a.width,b.left+b.width)-max(a.left,b.left))
            ih=max(0,min(a.top+a.height,b.top+b.height)-max(a.top,b.top))
            overlaps += iw>Inches(.03) and ih>Inches(.03)
    assert pictures==0 and oob==0 and overlaps==0, f"{name}: picture={pictures}, oob={oob}, overlaps={overlaps}"
    with zipfile.ZipFile(pptx) as z:
        theme=ET.fromstring(z.read("ppt/theme/theme1.xml")); styles=theme.find(".//a:effectStyleLst",NS)
        assert styles is not None and len(styles)>0
        first=styles[0]
        assert len(first)==1 and first[0].tag==A_NS+"effectLst" and len(first[0])==0, f"{name}: theme shadow not cleared"
        assert b"outerShdw" not in z.read("ppt/slides/slide1.xml")
    if any(e["type"] in {"grid","stack_grid"} and int(e["rows"])==40 and int(e["cols"])==40 for e in spec["elements"]):
        assert len(slide.shapes)<250, f"{name}: 40x40 grid expanded into too many shapes"
    return {"spec":path.name,"shapes":len(slide.shapes),"pictures":pictures,"out_of_bounds":oob,"text_overlaps":overlaps,"theme_shadow":False}

def main():
    specs=sorted((ROOT/"figure_specs").glob("*.json"))
    assert specs,"No FigureSpec JSON files"
    with tempfile.TemporaryDirectory() as d:
        results=[validate_outputs(p,validate_spec(p),Path(d)) for p in specs]
    print(json.dumps(results,ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__": raise SystemExit(main())
