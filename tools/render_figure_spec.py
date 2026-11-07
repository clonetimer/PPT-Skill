#!/usr/bin/env python3
from __future__ import annotations
import argparse,base64,json,math,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE,MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN,MSO_ANCHOR
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.oxml.xmlchemy import OxmlElement
from pptx.oxml.ns import qn
DPI=120.;A_NS="{http://schemas.openxmlformats.org/drawingml/2006/main}";NS={"a":"http://schemas.openxmlformats.org/drawingml/2006/main"}
def rgb(v):return RGBColor.from_string(v.lstrip("#").upper())
def nofx(s):
 for n in s._element.iter():
  st=n.find(qn("p:style"))
  if st is not None:
   r=st.find(qn("a:effectRef"))
   if r is not None:r.set("idx","0")
  e=n.find(qn("a:effectLst"))
  if e is not None:n.remove(e)
 sp=getattr(s._element,"spPr",None)
 if sp is not None and sp.find(qn("a:effectLst")) is None:sp.append(OxmlElement("a:effectLst"))
def clean_theme(p):
 t=p.with_suffix(".tmp.pptx")
 with zipfile.ZipFile(p) as a,zipfile.ZipFile(t,"w",zipfile.ZIP_DEFLATED) as b:
  for i in a.infolist():
   d=a.read(i.filename)
   if i.filename=="ppt/theme/theme1.xml":
    r=ET.fromstring(d);q=r.find(".//a:effectStyleLst",NS)
    if q is not None and len(q):
     for c in list(q[0]):q[0].remove(c)
     q[0].append(ET.Element(A_NS+"effectLst"))
    d=ET.tostring(r,encoding="utf-8",xml_declaration=True)
   b.writestr(i,d)
 t.replace(p)
def pts(e):return [(e["x"]+x*e["w"],e["y"]+y*e["h"]) for x,y in e["nodes"]]
def addtext(sl,e,df):
 s=sl.shapes.add_textbox(Inches(e["x"]),Inches(e["y"]),Inches(e["w"]),Inches(e["h"]))
 f=s.text_frame;f.clear();f.word_wrap=True;f.margin_left=Inches(.02);f.margin_right=Inches(.02);f.margin_top=Inches(.008);f.margin_bottom=Inches(.008);f.vertical_anchor=MSO_ANCHOR.MIDDLE
 al={"left":PP_ALIGN.LEFT,"center":PP_ALIGN.CENTER,"right":PP_ALIGN.RIGHT}[e.get("align","center")]
 for j,t in enumerate(e["text"].split("\n")):
  p=f.paragraphs[0] if j==0 else f.add_paragraph();p.alignment=al;p.space_before=Pt(0);p.space_after=Pt(0);p.line_spacing=1
  r=p.add_run();r.text=t;r.font.name=e.get("font",df);r.font.size=Pt(e.get("size",14));r.font.bold=e.get("bold",False);r.font.italic=e.get("italic",False);r.font.color.rgb=rgb(e.get("color","#28343C"))
 nofx(s)
def addline(sl,e):
 s=sl.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,Inches(e["x1"]),Inches(e["y1"]),Inches(e["x2"]),Inches(e["y2"]));c=rgb(e.get("color","#43525B"));s.line.color.rgb=c;s.line.width=Pt(e.get("sw",1))
 if e.get("dash"):s.line.dash_style=MSO_LINE_DASH_STYLE.DASH
 nofx(s)
 if e.get("arrow"):
  ang=math.degrees(math.atan2(e["y2"]-e["y1"],e["x2"]-e["x1"]));z=.105
  q=sl.shapes.add_shape(MSO_SHAPE.ISOSCELES_TRIANGLE,Inches(e["x2"]-z/2),Inches(e["y2"]-z/2),Inches(z),Inches(z));q.rotation=ang+90;q.fill.solid();q.fill.fore_color.rgb=c;q.line.color.rgb=c;nofx(q)
def render(spec,svg,pptx):
 w=spec["canvas"]["width_in"]*DPI;h=spec["canvas"]["height_in"]*DPI;df=spec.get("style",{}).get("font","Times New Roman")
 out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}">','<defs><marker id="ar" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0 0 L9 4.5 L0 9 Z" fill="#43525B"/></marker></defs>',f'<rect width="{w:.0f}" height="{h:.0f}" fill="#FFFFFF"/>']
 prs=Presentation();prs.slide_width=Inches(spec["canvas"]["width_in"]);prs.slide_height=Inches(spec["canvas"]["height_in"]);sl=prs.slides.add_slide(prs.slide_layouts[6]);sl.background.fill.solid();sl.background.fill.fore_color.rgb=rgb("#FFFFFF")
 for e in spec["elements"]:
  t=e["type"]
  if t=="image":
   image_path=Path(e["path"])
   if not image_path.is_absolute():image_path=Path(__file__).resolve().parents[1]/image_path
   data=image_path.read_bytes();mime="image/png" if image_path.suffix.lower()==".png" else "image/jpeg"
   out.append(f'<image x="{e["x"]*DPI}" y="{e["y"]*DPI}" width="{e["w"]*DPI}" height="{e["h"]*DPI}" href="data:{mime};base64,{base64.b64encode(data).decode()}"/>')
   sl.shapes.add_picture(str(image_path),Inches(e["x"]),Inches(e["y"]),width=Inches(e["w"]),height=Inches(e["h"]))
  elif t=="text":
   x,y,ww,hh=[e[k]*DPI for k in ("x","y","w","h")];fs=e.get("size",14)*DPI/72;ls=e["text"].split("\n");a=e.get("align","center");anc={"left":"start","center":"middle","right":"end"}[a];tx=x if a=="left" else x+ww/2 if a=="center" else x+ww;lh=fs*1.18;by=y+hh/2-(len(ls)-1)*lh/2+fs*.35
   sp="".join(f'<tspan x="{tx}" dy="{0 if j==0 else lh}">{escape(v)}</tspan>' for j,v in enumerate(ls))
   out.append(f'<text x="{tx}" y="{by}" text-anchor="{anc}" dominant-baseline="middle" font-family="{escape("Noto Sans CJK SC, DejaVu Sans, Microsoft YaHei, sans-serif" if e.get("font",df)=="Microsoft YaHei" else e.get("font",df))}" font-size="{fs}" fill="{e.get("color","#28343C")}"'+(' font-weight="700"' if e.get("bold") else '')+(' font-style="italic"' if e.get("italic") else '')+f'>{sp}</text>');addtext(sl,e,df)
  elif t=="rect":
   x,y,ww,hh=[e[k]*DPI for k in ("x","y","w","h")];dash=' stroke-dasharray="8 6"' if e.get("dash") else ''
   out.append(f'<rect x="{x}" y="{y}" width="{ww}" height="{hh}" rx="{e.get("radius",0)*DPI}" fill="{e.get("fill","#FFFFFF")}" stroke="{e.get("stroke","#43525B")}" stroke-width="{e.get("sw",1)*DPI/72}"{dash}/>')
   s=sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if e.get("radius",0)>0 else MSO_SHAPE.RECTANGLE,Inches(e["x"]),Inches(e["y"]),Inches(e["w"]),Inches(e["h"]));s.fill.solid();s.fill.fore_color.rgb=rgb(e.get("fill","#FFFFFF"));s.line.color.rgb=rgb(e.get("stroke","#43525B"));s.line.width=Pt(e.get("sw",1))
   if e.get("dash"):s.line.dash_style=MSO_LINE_DASH_STYLE.DASH
   nofx(s)
  elif t=="trapezoid":
   x,y,ww,hh=[e[k]*DPI for k in ("x","y","w","h")];out.append(f'<polygon points="{x+ww*.13},{y} {x+ww*.87},{y} {x+ww},{y+hh} {x},{y+hh}" fill="{e["fill"]}" stroke="{e["stroke"]}" stroke-width="{e.get("sw",1)*DPI/72}"/>')
   s=sl.shapes.add_shape(MSO_SHAPE.TRAPEZOID,Inches(e["x"]),Inches(e["y"]),Inches(e["w"]),Inches(e["h"]));s.fill.solid();s.fill.fore_color.rgb=rgb(e["fill"]);s.line.color.rgb=rgb(e["stroke"]);s.line.width=Pt(e.get("sw",1));nofx(s)
  elif t=="line":
   x1,y1,x2,y2=[e[k]*DPI for k in ("x1","y1","x2","y2")];dash=' stroke-dasharray="8 6"' if e.get("dash") else '';ar=' marker-end="url(#ar)"' if e.get("arrow") else ''
   out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{e.get("color","#43525B")}" stroke-width="{e.get("sw",1)*DPI/72}"{dash}{ar}/>');addline(sl,e)
  elif t=="polyline":
   out.append('<polyline points="'+" ".join(f'{x*DPI},{y*DPI}' for x,y in e["points"])+f'" fill="none" stroke="{e["color"]}" stroke-width="{e.get("sw",1.2)*DPI/72}" stroke-linecap="round" stroke-linejoin="round"/>')
   for a,b in zip(e["points"][:-1],e["points"][1:]):addline(sl,{"x1":a[0],"y1":a[1],"x2":b[0],"y2":b[1],"color":e["color"],"sw":e.get("sw",1.2)})
  elif t=="ellipse":
   x,y,ww,hh=[e[k]*DPI for k in ("x","y","w","h")];out.append(f'<ellipse cx="{x+ww/2}" cy="{y+hh/2}" rx="{ww/2}" ry="{hh/2}" fill="{e["fill"]}" stroke="{e["stroke"]}" stroke-width="{e.get("sw",1)*DPI/72}"/>')
   s=sl.shapes.add_shape(MSO_SHAPE.OVAL,Inches(e["x"]),Inches(e["y"]),Inches(e["w"]),Inches(e["h"]));s.fill.solid();s.fill.fore_color.rgb=rgb(e["fill"]);s.line.color.rgb=rgb(e["stroke"]);s.line.width=Pt(e.get("sw",1));nofx(s)
  elif t=="grid" or t=="stack_grid":
   x,y,ww,hh=[e[k]*DPI for k in ("x","y","w","h")];rows,cols=int(e["rows"]),int(e["cols"]);stroke=e.get("stroke","#D7DEE3");border=e.get("border","#98A6AF")
   if t=="stack_grid":
    off=e.get("offset",.16)*DPI
    for layer in range(int(e.get("layers",5))-1,0,-1):out.append(f'<rect x="{x+off*layer}" y="{y-off*layer}" width="{ww}" height="{hh}" fill="#FFFFFF" stroke="{border}" stroke-width="1"/>')
   pid="grid"+str(len(out));out.append(f'<defs><pattern id="{pid}" width="{ww/cols}" height="{hh/rows}" patternUnits="userSpaceOnUse"><path d="M {ww/cols} 0 H 0 V {hh/rows}" fill="none" stroke="{stroke}" stroke-width="{e.get("sw",.4)*DPI/72}"/></pattern></defs>')
   out.append(f'<rect x="{x}" y="{y}" width="{ww}" height="{hh}" fill="{e.get("fill","#FBFCFD")}" stroke="{border}" stroke-width="1"/>')
   out.append(f'<rect x="{x}" y="{y}" width="{ww}" height="{hh}" fill="url(#{pid})"/>')
   x,y,ww,hh=[e[k] for k in ("x","y","w","h")];rows,cols=int(e["rows"]),int(e["cols"])
   if t=="stack_grid":
    off=e.get("offset",.16)
    for layer in range(int(e.get("layers",5))-1,0,-1):
     b=sl.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(x+off*layer),Inches(y-off*layer),Inches(ww),Inches(hh));b.fill.solid();b.fill.fore_color.rgb=rgb("#FFFFFF");b.line.color.rgb=rgb(e.get("border","#98A6AF"));b.line.width=Pt(.8);nofx(b)
   bg=sl.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(x),Inches(y),Inches(ww),Inches(hh));bg.fill.solid();bg.fill.fore_color.rgb=rgb(e.get("fill","#FBFCFD"));bg.line.color.rgb=rgb(e.get("border","#98A6AF"));bg.line.width=Pt(.8);nofx(bg)
   for c in range(1,cols):addline(sl,{"x1":x+ww*c/cols,"y1":y,"x2":x+ww*c/cols,"y2":y+hh,"color":e.get("stroke","#D7DEE3"),"sw":e.get("sw",.4)})
   for r in range(1,rows):addline(sl,{"x1":x,"y1":y+hh*r/rows,"x2":x+ww,"y2":y+hh*r/rows,"color":e.get("stroke","#D7DEE3"),"sw":e.get("sw",.4)})
  elif t=="sensor":
   x,y,z=e["x"],e["y"],e.get("scale",1);v=e.get("variant",0);c=e.get("color","#43525B")
   if v==0:
    out.extend([f'<circle cx="{(x+z*.10)*DPI}" cy="{(y+z*.10)*DPI}" r="{z*.075*DPI}" fill="#E8F0F3" stroke="{c}" stroke-width="2"/>',f'<circle cx="{(x+z*.10)*DPI}" cy="{(y+z*.10)*DPI}" r="{z*.025*DPI}" fill="{c}"/>'])
   elif v==1:out.append(f'<rect x="{(x+z*.02)*DPI}" y="{(y+z*.06)*DPI}" width="{z*.17*DPI}" height="{z*.14*DPI}" rx="2" fill="#E8F0F3" stroke="{c}" stroke-width="2"/>')
   elif v==2:out.append(f'<polygon points="{(x+z*.02)*DPI},{(y+z*.12)*DPI} {(x+z*.12)*DPI},{(y+z*.04)*DPI} {(x+z*.20)*DPI},{(y+z*.15)*DPI} {(x+z*.10)*DPI},{(y+z*.23)*DPI}" fill="#E8F0F3" stroke="{c}" stroke-width="2"/>')
   else:out.append(f'<rect x="{(x+z*.06)*DPI}" y="{(y+z*.025)*DPI}" width="{z*.09*DPI}" height="{z*.24*DPI}" rx="3" fill="#E8F0F3" stroke="{c}" stroke-width="2"/>')
   out.extend([f'<line x1="{(x+z*.10)*DPI}" y1="{(y+z*.20)*DPI}" x2="{(x+z*.10)*DPI}" y2="{(y+z*.30)*DPI}" stroke="{c}" stroke-width="2"/>',f'<rect x="{(x+z*.015)*DPI}" y="{(y+z*.30)*DPI}" width="{z*.18*DPI}" height="{z*.045*DPI}" fill="#FFFFFF" stroke="{c}" stroke-width="1.5"/>'])
   if v==0:
    s=sl.shapes.add_shape(MSO_SHAPE.OVAL,Inches(x+z*.025),Inches(y+z*.025),Inches(z*.15),Inches(z*.15))
   elif v==1:
    s=sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,Inches(x+z*.02),Inches(y+z*.06),Inches(z*.17),Inches(z*.14))
   elif v==2:
    s=sl.shapes.add_shape(MSO_SHAPE.PARALLELOGRAM,Inches(x+z*.015),Inches(y+z*.04),Inches(z*.19),Inches(z*.19))
   else:
    s=sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,Inches(x+z*.06),Inches(y+z*.025),Inches(z*.09),Inches(z*.24))
   s.fill.solid();s.fill.fore_color.rgb=rgb("#E8F0F3");s.line.color.rgb=rgb(c);nofx(s)
   addline(sl,{"x1":x+z*.10,"y1":y+z*.20,"x2":x+z*.10,"y2":y+z*.30,"color":c,"sw":1})
   b=sl.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(x+z*.015),Inches(y+z*.30),Inches(z*.18),Inches(z*.045));b.fill.solid();b.fill.fore_color.rgb=rgb("#FFFFFF");b.line.color.rgb=rgb(c);nofx(b)
  elif t=="graph":
   ps=pts(e)
   for a,b in e["edges"]:
    x1,y1=ps[a];x2,y2=ps[b];out.append(f'<line x1="{x1*DPI}" y1="{y1*DPI}" x2="{x2*DPI}" y2="{y2*DPI}" stroke="{e["edge"]}" stroke-width="{e.get("sw",.75)*DPI/72}"/>');addline(sl,{"x1":x1,"y1":y1,"x2":x2,"y2":y2,"color":e["edge"],"sw":e.get("sw",.75)})
   for x,y in ps:
    rr=e.get("r",.045);out.append(f'<circle cx="{x*DPI}" cy="{y*DPI}" r="{rr*DPI}" fill="{e["fill"]}" stroke="#43525B" stroke-width="1.1"/>')
    s=sl.shapes.add_shape(MSO_SHAPE.OVAL,Inches(x-rr),Inches(y-rr),Inches(2*rr),Inches(2*rr));s.fill.solid();s.fill.fore_color.rgb=rgb(e["fill"]);s.line.color.rgb=rgb("#43525B");s.line.width=Pt(.55);nofx(s)
 out.append("</svg>");Path(svg).parent.mkdir(parents=True,exist_ok=True);Path(svg).write_text("\n".join(out),encoding="utf-8")
 Path(pptx).parent.mkdir(parents=True,exist_ok=True);prs.save(pptx);clean_theme(Path(pptx))
def main():
 a=argparse.ArgumentParser();a.add_argument("spec",type=Path);a.add_argument("--svg",type=Path,required=True);a.add_argument("--pptx",type=Path,required=True);x=a.parse_args();render(json.loads(x.spec.read_text(encoding="utf-8")),x.svg,x.pptx)
if __name__=="__main__":main()
