#!/usr/bin/env python3
"""Audit PowerPoint bounds, text intersections, SVG pictures, and theme effects."""
from __future__ import annotations
import argparse, json, zipfile, xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Inches

NS={"a":"http://schemas.openxmlformats.org/drawingml/2006/main"}

def walk(shapes):
    for s in shapes:
        yield s
        if s.shape_type==MSO_SHAPE_TYPE.GROUP: yield from walk(s.shapes)

def overlaps(a,b):
    iw=max(0,min(a.left+a.width,b.left+b.width)-max(a.left,b.left))
    ih=max(0,min(a.top+a.height,b.top+b.height)-max(a.top,b.top))
    return iw>Inches(.03) and ih>Inches(.03)

def audit(path):
    prs=Presentation(str(path)); slides=[]
    for i,slide in enumerate(prs.slides,1):
        counts=Counter(); pics=svgpics=oob=0; texts=[]; sizes=[]; fonts=Counter()
        for s in walk(slide.shapes):
            counts[str(s.shape_type)]+=1
            if s.shape_type==MSO_SHAPE_TYPE.PICTURE:
                pics+=1
                if "svgBlip" in s._element.xml: svgpics+=1
            if s.left<0 or s.top<0 or s.left+s.width>prs.slide_width or s.top+s.height>prs.slide_height:oob+=1
            if getattr(s,"has_text_frame",False) and s.text.strip():
                texts.append(s)
                for p in s.text_frame.paragraphs:
                    for r in p.runs:
                        if r.font.size:sizes.append(round(r.font.size.pt,1))
                        if r.font.name:fonts[r.font.name]+=1
        ov=sum(overlaps(a,b) for j,a in enumerate(texts) for b in texts[j+1:])
        slides.append({"slide":i,"recursive_shape_count":sum(counts.values()),"shape_types":dict(counts),
                       "picture_objects":pics,"svg_picture_objects":svgpics,"non_svg_picture_objects":pics-svgpics,
                       "out_of_bounds":oob,"text_box_overlaps":ov,
                       "min_font_pt":min(sizes) if sizes else None,"max_font_pt":max(sizes) if sizes else None,
                       "fonts":dict(fonts)})
    with zipfile.ZipFile(path) as z:
        theme=ET.fromstring(z.read("ppt/theme/theme1.xml")); styles=theme.find(".//a:effectStyleLst",NS)
        shadow=styles is None or not len(styles) or styles[0].find(".//a:outerShdw",NS) is not None
    return {"file":path.name,"slide_count":len(prs.slides),"theme_first_effect_has_shadow":shadow,"slides":slides}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("pptx",type=Path);ap.add_argument("--output",type=Path);ap.add_argument("--strict",action="store_true")
    args=ap.parse_args(); result=audit(args.pptx); rendered=json.dumps(result,ensure_ascii=False,indent=2)
    if args.output:args.output.write_text(rendered+"\n",encoding="utf-8")
    print(rendered)
    if args.strict:
        failures=[]
        if result["theme_first_effect_has_shadow"]:failures.append("theme shadow effect remains")
        for s in result["slides"]:
            if s["out_of_bounds"]:failures.append(f"slide {s['slide']} out-of-bounds")
            if s["text_box_overlaps"]:failures.append(f"slide {s['slide']} text overlaps")
            if s["non_svg_picture_objects"]:failures.append(f"slide {s['slide']} non-SVG pictures")
        if failures:raise SystemExit("\n".join(failures))
    return 0

if __name__=="__main__":raise SystemExit(main())
