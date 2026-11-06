#!/usr/bin/env python3
"""Render a JSON FigureSpec to SVG and editable PowerPoint from the same source."""
from __future__ import annotations
import argparse, json, math, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.oxml.xmlchemy import OxmlElement
from pptx.oxml.ns import qn

DPI=120.0
A_NS="{http://schemas.openxmlformats.org/drawingml/2006/main}"
NS={"a":"http://schemas.openxmlformats.org/drawingml/2006/main"}

def color(v):
    return RGBColor.from_string(v.lstrip("#").upper())

def no_theme_effects(shape):
    for node in shape._element.iter():
        style=node.find(qn("p:style"))
        if style is not None:
            ref=style.find(qn("a:effectRef"))
            if ref is not None: ref.set("idx","0")
        effects=node.find(qn("a:effectLst"))
        if effects is not None: node.remove(effects)
    sp_pr=getattr(shape._element,"spPr",None)
    if sp_pr is not None and sp_pr.find(qn("a:effectLst")) is None:
        sp_pr.append(OxmlElement("a:effectLst"))

def render_svg(spec,path):
    w=float(spec["canvas"]["width_in"])*DPI
    h=float(spec["canvas"]["height_in"])*DPI
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}">',
         '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="#53616B"/></marker></defs>',
         f'<rect width="{w:.0f}" height="{h:.0f}" fill="#FFFFFF"/>']
    for e in spec["elements"]:
        typ=e["type"]
        if typ=="text":
            x,y,ww,hh=[float(e[k])*DPI for k in ("x","y","w","h")]
            size=float(e.get("size",14)); fs=size*DPI/72
            lines=str(e["text"]).split("\n"); align=e.get("align","center")
            anchor={"left":"start","center":"middle","right":"end"}[align]
            tx=x if align=="left" else (x+ww/2 if align=="center" else x+ww)
            lh=fs*1.18; base=y+hh/2-(len(lines)-1)*lh/2+fs*.35
            spans="".join(f'<tspan x="{tx:.2f}" dy="{0 if i==0 else lh:.2f}">{escape(line)}</tspan>' for i,line in enumerate(lines))
            font=e.get("font",spec.get("style",{}).get("font","Arial"))
            if font=="Microsoft YaHei": font="Noto Sans CJK SC, DejaVu Sans, Microsoft YaHei, sans-serif"
            out.append(f'<text x="{tx:.2f}" y="{base:.2f}" text-anchor="{anchor}" dominant-baseline="middle" font-family="{escape(font)}" font-size="{fs:.2f}px" fill="{e.get("color","#222222")}"'+(' font-weight="700"' if e.get("bold") else '')+'>'+spans+'</text>')
        elif typ=="rect":
            x,y,ww,hh=[float(e[k])*DPI for k in ("x","y","w","h")]
            out.append(f'<rect x="{x}" y="{y}" width="{ww}" height="{hh}" rx="{float(e.get("radius",0))*DPI}" fill="{e.get("fill","#FFFFFF")}" stroke="{e.get("stroke","#53616B")}" stroke-width="{float(e.get("sw",1))*DPI/72}"/>')
        elif typ=="line":
            x1,y1,x2,y2=[float(e[k])*DPI for k in ("x1","y1","x2","y2")]
            dash=' stroke-dasharray="8 6"' if e.get("dash") else ''
            arrow=' marker-end="url(#arrow)"' if e.get("arrow") else ''
            out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{e.get("color",spec.get("style",{}).get("line","#53616B"))}" stroke-width="{float(e.get("sw",1.1))*DPI/72}"{dash}{arrow}/>')
        elif typ in ("grid","stack_grid"):
            x,y,ww,hh=[float(e[k])*DPI for k in ("x","y","w","h")]
            rows,cols=int(e["rows"]),int(e["cols"])
            stroke=e.get("stroke","#D7DEE3"); border=e.get("border","#98A6AF")
            if typ=="stack_grid":
                off=float(e.get("offset",.16))*DPI
                for layer in range(int(e.get("layers",5))-1,0,-1):
                    out.append(f'<rect x="{x+off*layer}" y="{y-off*layer}" width="{ww}" height="{hh}" fill="#FFFFFF" stroke="{border}" stroke-width="1.1"/>')
            pid=f"grid{len(out)}"
            out.append(f'<defs><pattern id="{pid}" width="{ww/cols}" height="{hh/rows}" patternUnits="userSpaceOnUse"><path d="M {ww/cols} 0 H 0 V {hh/rows}" fill="none" stroke="{stroke}" stroke-width="{float(e.get("sw",.4))*DPI/72}"/></pattern></defs>')
            out.append(f'<rect x="{x}" y="{y}" width="{ww}" height="{hh}" fill="{e.get("fill","#FBFCFD")}" stroke="{border}" stroke-width=".9"/>')
            out.append(f'<rect x="{x}" y="{y}" width="{ww}" height="{hh}" fill="url(#{pid})"/>')
        else: raise ValueError(f"Unsupported primitive: {typ}")
    out.append("</svg>")
    path.write_text("\n".join(out),encoding="utf-8")

def add_text(slide,e,default_font):
    sh=slide.shapes.add_textbox(Inches(e["x"]),Inches(e["y"]),Inches(e["w"]),Inches(e["h"]))
    tf=sh.text_frame; tf.clear(); tf.word_wrap=True
    tf.margin_left=Inches(.025); tf.margin_right=Inches(.025); tf.margin_top=Inches(.012); tf.margin_bottom=Inches(.012)
    tf.vertical_anchor=MSO_ANCHOR.MIDDLE
    align={"left":PP_ALIGN.LEFT,"center":PP_ALIGN.CENTER,"right":PP_ALIGN.RIGHT}[e.get("align","center")]
    for i,line in enumerate(str(e["text"]).split("\n")):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
        p.alignment=align; p.space_before=Pt(0); p.space_after=Pt(0); p.line_spacing=1.0
        r=p.add_run(); r.text=line; r.font.name=e.get("font",default_font); r.font.size=Pt(float(e.get("size",14)))
        r.font.bold=bool(e.get("bold")); r.font.color.rgb=color(e.get("color","#222222"))
    no_theme_effects(sh)

def add_line(slide,e,default_color):
    sh=slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,Inches(e["x1"]),Inches(e["y1"]),Inches(e["x2"]),Inches(e["y2"]))
    c=e.get("color",default_color); sh.line.color.rgb=color(c); sh.line.width=Pt(float(e.get("sw",1.1)))
    if e.get("dash"): sh.line.dash_style=MSO_LINE_DASH_STYLE.DASH
    if e.get("arrow"):
        angle=math.degrees(math.atan2(float(e["y2"])-float(e["y1"]),float(e["x2"])-float(e["x1"])))
        size=.105
        tri=slide.shapes.add_shape(MSO_SHAPE.ISOSCELES_TRIANGLE,Inches(float(e["x2"])-size/2),Inches(float(e["y2"])-size/2),Inches(size),Inches(size))
        tri.rotation=angle+90; tri.fill.solid(); tri.fill.fore_color.rgb=color(c); tri.line.color.rgb=color(c); no_theme_effects(tri)
    no_theme_effects(sh)

def render_pptx(slide,spec):
    default_font=spec.get("style",{}).get("font","Arial")
    default_line=spec.get("style",{}).get("line","#53616B")
    for e in spec["elements"]:
        typ=e["type"]
        if typ=="text": add_text(slide,e,default_font)
        elif typ=="rect":
            shape_type=MSO_SHAPE.ROUNDED_RECTANGLE if float(e.get("radius",0))>0 else MSO_SHAPE.RECTANGLE
            sh=slide.shapes.add_shape(shape_type,Inches(e["x"]),Inches(e["y"]),Inches(e["w"]),Inches(e["h"]))
            sh.fill.solid(); sh.fill.fore_color.rgb=color(e.get("fill","#FFFFFF"))
            sh.line.color.rgb=color(e.get("stroke",default_line)); sh.line.width=Pt(float(e.get("sw",1))); no_theme_effects(sh)
        elif typ=="line": add_line(slide,e,default_line)
        elif typ=="grid":
            x,y,ww,hh=[float(e[k]) for k in ("x","y","w","h")]
            bg=slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(x),Inches(y),Inches(ww),Inches(hh))
            bg.fill.solid(); bg.fill.fore_color.rgb=color(e.get("fill","#FBFCFD"))
            bg.line.color.rgb=color(e.get("border","#98A6AF")); bg.line.width=Pt(.8); no_theme_effects(bg)
            rows,cols=int(e["rows"]),int(e["cols"])
            for c in range(1,cols):
                add_line(slide,{"x1":x+ww*c/cols,"y1":y,"x2":x+ww*c/cols,"y2":y+hh,"color":e.get("stroke","#D7DEE3"),"sw":e.get("sw",.4)},default_line)
            for r in range(1,rows):
                add_line(slide,{"x1":x,"y1":y+hh*r/rows,"x2":x+ww,"y2":y+hh*r/rows,"color":e.get("stroke","#D7DEE3"),"sw":e.get("sw",.4)},default_line)
        elif typ=="stack_grid":
            x,y,ww,hh=[float(e[k]) for k in ("x","y","w","h")]; off=float(e.get("offset",.16))
            for layer in range(int(e.get("layers",5))-1,0,-1):
                back=slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(x+off*layer),Inches(y-off*layer),Inches(ww),Inches(hh))
                back.fill.solid(); back.fill.fore_color.rgb=color("#FFFFFF"); back.line.color.rgb=color(e.get("border","#98A6AF")); back.line.width=Pt(.8); no_theme_effects(back)
            render_pptx(slide,{"style":spec.get("style",{}),"elements":[{"type":"grid","x":x,"y":y,"w":ww,"h":hh,"rows":e["rows"],"cols":e["cols"],"fill":e.get("fill","#FBFCFD"),"stroke":e.get("stroke","#D7DEE3"),"border":e.get("border","#98A6AF"),"sw":e.get("sw",.35)}]})
        else: raise ValueError(f"Unsupported primitive: {typ}")

def remove_theme_shadow_style(path):
    tmp=path.with_suffix(".tmp.pptx")
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp,"w",zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data=zin.read(item.filename)
            if item.filename=="ppt/theme/theme1.xml":
                root=ET.fromstring(data); styles=root.find(".//a:effectStyleLst",NS)
                if styles is not None and len(styles):
                    first=styles[0]
                    for child in list(first): first.remove(child)
                    first.append(ET.Element(A_NS+"effectLst"))
                data=ET.tostring(root,encoding="utf-8",xml_declaration=True)
            zout.writestr(item,data)
    tmp.replace(path)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("spec",type=Path); ap.add_argument("--svg",type=Path,required=True); ap.add_argument("--pptx",type=Path,required=True)
    args=ap.parse_args(); spec=json.loads(args.spec.read_text(encoding="utf-8"))
    render_svg(spec,args.svg)
    deck=Presentation(); deck.slide_width=Inches(float(spec["canvas"]["width_in"])); deck.slide_height=Inches(float(spec["canvas"]["height_in"]))
    slide=deck.slides.add_slide(deck.slide_layouts[6]); slide.background.fill.solid(); slide.background.fill.fore_color.rgb=color("#FFFFFF")
    render_pptx(slide,spec); deck.save(args.pptx); remove_theme_shadow_style(args.pptx)

if __name__=="__main__": main()
