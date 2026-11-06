#!/usr/bin/env python3
from __future__ import annotations
import json,subprocess,sys,tempfile,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Inches
ROOT=Path(__file__).resolve().parents[1];S="{http://www.w3.org/2000/svg}";A={"a":"http://schemas.openxmlformats.org/drawingml/2006/main"}
def ov(a,b):
 x=max(0,min(a.left+a.width,b.left+b.width)-max(a.left,b.left));y=max(0,min(a.top+a.height,b.top+b.height)-max(a.top,b.top))
 return x>Inches(.03) and y>Inches(.03)
def check(p,tmp):
 s=json.loads(p.read_text(encoding="utf-8"));w=s["canvas"]["width_in"];h=s["canvas"]["height_in"];allowed={"text","rect","trapezoid","line","polyline","ellipse","sensor","graph"}
 for i,e in enumerate(s["elements"]):
  assert e["type"] in allowed,(p,i,e["type"])
  if e["type"]=="line":assert 0<=e["x1"]<=w and 0<=e["x2"]<=w and 0<=e["y1"]<=h and 0<=e["y2"]<=h
  elif e["type"]=="polyline":assert all(0<=x<=w and 0<=y<=h for x,y in e["points"])
  elif e["type"]=="graph":assert e["x"]>=0 and e["y"]>=0 and e["x"]+e["w"]<=w and e["y"]+e["h"]<=h and all(0<=x<=1 and 0<=y<=1 for x,y in e["nodes"])
  elif e["type"]=="sensor":assert e["x"]>=0 and e["y"]>=0 and e["x"]+e.get("scale",1)*.21<=w and e["y"]+e.get("scale",1)*.36<=h
  else:assert e["x"]>=0 and e["y"]>=0 and e["w"]>0 and e["h"]>0 and e["x"]+e["w"]<=w and e["y"]+e["h"]<=h
 svg=tmp/(p.stem+".svg");ppt=tmp/(p.stem+".pptx")
 subprocess.run([sys.executable,str(ROOT/"tools"/"render_figure_spec.py"),str(p),"--svg",str(svg),"--pptx",str(ppt)],check=True)
 r=ET.parse(svg).getroot();assert r.tag==S+"svg" and r.attrib.get("viewBox") and r.find(".//"+S+"image") is None
 d=Presentation(ppt);sl=d.slides[0];tx=[];pics=0;oob=0
 for sh in sl.shapes:
  pics+=sh.shape_type==MSO_SHAPE_TYPE.PICTURE;oob+=sh.left<0 or sh.top<0 or sh.left+sh.width>d.slide_width or sh.top+sh.height>d.slide_height
  if getattr(sh,"has_text_frame",False) and sh.text.strip():tx.append(sh)
 overlaps=sum(ov(a,b) for i,a in enumerate(tx) for b in tx[i+1:])
 with zipfile.ZipFile(ppt) as z:
  t=ET.fromstring(z.read("ppt/theme/theme1.xml"));q=t.find(".//a:effectStyleLst",A);shadow=q[0].find(".//a:outerShdw",A) is not None or b"outerShdw" in z.read("ppt/slides/slide1.xml")
 assert not pics and not oob and not overlaps and not shadow,(p,pics,oob,overlaps,shadow)
 return {"spec":p.name,"shapes":len(sl.shapes),"pictures":pics,"out_of_bounds":oob,"text_overlaps":overlaps,"shadow":shadow}
def main():
 files=[ROOT/"figure_specs"/"c01"/f"{stem}.json" for stem in ("C01_FBG_construction","C01_SEANet_graph_level")]
 assert all(p.is_file() for p in files)
 with tempfile.TemporaryDirectory() as t:print(json.dumps([check(p,Path(t)) for p in files],indent=2))
if __name__=="__main__":main()
