#!/usr/bin/env python3
"""Audit PowerPoint shape counts, raster objects, explicit fonts, and bounds."""
import argparse, json
from collections import Counter
from pathlib import Path
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Inches

def walk(shapes):
    for shape in shapes:
        yield shape
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from walk(shape.shapes)

def audit(path):
    prs=Presentation(str(path)); slides=[]
    for i,slide in enumerate(prs.slides,1):
        counts,fonts,sizes=Counter(),Counter(),[]
        pictures,oob=0,[]
        for sh in walk(slide.shapes):
            counts[str(sh.shape_type)]+=1
            pictures += sh.shape_type == MSO_SHAPE_TYPE.PICTURE
            if sh.left<0 or sh.top<0 or sh.left+sh.width>prs.slide_width or sh.top+sh.height>prs.slide_height:
                oob.append({"name":sh.name,"type":str(sh.shape_type),"connector_transform_extent":sh.shape_type==MSO_SHAPE_TYPE.LINE})
            if getattr(sh,"has_text_frame",False) and sh.text.strip():
                for p in sh.text_frame.paragraphs:
                    for r in p.runs:
                        if r.font.name: fonts[r.font.name]+=1
                        if r.font.size: sizes.append(round(r.font.size.pt,1))
        slides.append({"slide":i,"recursive_shape_count":sum(counts.values()),"picture_objects":pictures,"out_of_bounds":oob,"min_font_pt":min(sizes) if sizes else None,"max_font_pt":max(sizes) if sizes else None,"fonts":dict(fonts),"shape_types":dict(counts)})
    return {"file":Path(path).name,"slide_count":len(prs.slides),"slide_size_in":[round(prs.slide_width/Inches(1),3),round(prs.slide_height/Inches(1),3)],"slides":slides}

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("pptx",type=Path);ap.add_argument("--output",type=Path);args=ap.parse_args()
    result=json.dumps(audit(args.pptx),ensure_ascii=False,indent=2)
    if args.output: args.output.write_text(result+"\n",encoding="utf-8")
    print(result)
