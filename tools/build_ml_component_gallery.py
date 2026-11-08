"""Render a synthetic gallery proving components work beyond the three papers."""
from __future__ import annotations

import json
from pathlib import Path

from ml_figure_components import (
    addition_junction, crop_concat_pair, encoder_wedge,
    feature_map_strip, similarity_matrix, vector_fanout,
)
from render_figure_spec import render

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"dist/skill_tests/ml_component_gallery"
OUT.mkdir(parents=True,exist_ok=True)


class Canvas:
    def __init__(self):self.elements=[]
    def add(self,kind,**kw):self.elements.append({"type":kind,**kw})
    def rect(self,x,y,w,h,fill="#FFFFFF",stroke="#222222",sw=.8,sid=None,dash=False):
        self.add("rect",x=x,y=y,w=w,h=h,fill=fill,stroke=stroke,sw=sw,
                 **({"semantic_id":sid} if sid else {}))
    def ellipse(self,x,y,w,h,fill="#FFFFFF",stroke="#222222",sw=.8,sid=None):
        self.add("ellipse",x=x,y=y,w=w,h=h,fill=fill,stroke=stroke,sw=sw,
                 **({"semantic_id":sid} if sid else {}))
    def polygon(self,points,fill="#FFFFFF",stroke="#222222",sw=.8,sid=None):
        self.add("polygon",points=points,fill=fill,stroke=stroke,sw=sw,
                 **({"semantic_id":sid} if sid else {}))
    def text(self,s,x,y,w,h,size=10,align="center",color="#222222",bold=False,
             rotation=0,sid=None,font=None):
        self.add("text",text=s,x=x,y=y,w=w,h=h,size=size,align=align,color=color,
                 bold=bold,**({"rotation":rotation} if rotation else {}),
                 **({"semantic_id":sid} if sid else {}),**({"font":font} if font else {}))
    def line(self,x1,y1,x2,y2,color="#333333",sw=.9,arrow=False,dash=False,link=None):
        self.add("line",x1=x1,y1=y1,x2=x2,y2=y2,color=color,sw=sw,arrow=arrow,
                 **({"dash":True} if dash else {}))


C=Canvas()
ink="#23313B";muted="#66727A";blue="#74A0CE";blue_edge="#38669A"
purple="#E4D8EB";purple_edge="#9974A8";green="#D9ECD7";green_edge="#8DBB83"
match="#D8E7FB";grid="#969696"

C.text("Editable ML Figure Components",.55,.35,14.9,.45,21,align="left",bold=True,color=ink)
C.text("Parameter variation demo · scientific relationships are illustrative, not from a paper",.55,.83,14.9,.28,10,align="left",color=muted)

C.text("01   Feature-map state and crop + concat",.65,1.40,7.0,.34,14,align="left",bold=True,color=ink)
state=feature_map_strip(C,sid="sample_state",x=1.18,y=2.15,w=.19,h=1.60,
    channels=48,spatial_size="80×80",fill=blue,stroke=blue_edge,
    label_color=muted,dimension_side="left")
pair=crop_concat_pair(C,sid="A",x=3.75,y=2.25,h=1.20,
    channels_per_half=48,spatial_size="72×72",fill=blue,
    stroke=blue_edge,label_color=muted,half_width=.13,gap=.035)
C.line(*state.port("right"),pair.port("crop_in")[0]-.06,pair.port("crop_in")[1],color="#A6A9AB",sw=2,arrow=True)
C.line(3.50,3.93,pair.port("upsample_in")[0],pair.port("upsample_in")[1],color="#15933A",sw=2,arrow=True)
C.text("copy / crop",1.78,2.30,1.35,.30,10,align="left",color=muted)
C.text("upsample",2.28,3.91,1.05,.28,10,align="left",color="#15933A")
C.text("separate ports",4.65,2.67,1.45,.30,10,align="left",color=muted)

C.text("02   Branch and additive merge",8.0,1.40,7.0,.34,14,align="left",bold=True,color=ink)
junction=addition_junction(C,sid="sample_sum",x=10.85,y=3.05,diameter=.68,stroke=ink,symbol_font_pt=25)
C.rect(9.78,2.06,2.15,.55,"#FFFFFF",ink,1)
C.text("transformation",9.92,2.18,1.86,.25,12)
C.text("x",8.90,1.78,.24,.26,15,color=ink)
C.line(9.18,2.04,9.18,2.18,color=ink,sw=1.3)
C.line(9.18,2.18,9.78,2.18,color=ink,sw=1.3,arrow=True)
C.line(11.19,2.61,*junction.port("main_in"),color=ink,sw=1.4,arrow=True)
C.line(9.18,2.18,9.18,3.39,color=ink,sw=1.3)
C.line(9.18,3.39,*junction.port("shortcut_in_left"),color=ink,sw=1.3,arrow=True)
C.text("identity",8.15,2.93,.94,.26,11,color=muted)
C.line(*junction.port("out"),11.19,4.08,color=ink,sw=1.4,arrow=True)
C.text("add, then activate",11.70,3.26,2.15,.30,10,align="left",color=muted)

C.text("03   Tapered encoders and N×N pairing",.65,4.48,10.2,.34,14,align="left",bold=True,color=ink)
text_encoder=encoder_wedge(C,sid="sample_text_encoder",x=.83,y=5.08,w=1.24,h=1.15,
    label="Text\nEncoder",fill=purple,stroke=purple_edge,taper=.20,font_pt=10)
image_encoder=encoder_wedge(C,sid="sample_image_encoder",x=.83,y=6.95,w=1.24,h=1.15,
    label="Image\nEncoder",fill=green,stroke=green_edge,taper=.20,font_pt=10)
matrix=similarity_matrix(C,sid="sample_matrix",x=4.20,y=6.05,cell_w=.43,cell_h=.43,
    indices=["1","2","…","n"],row_header_x=3.67,column_header_y=5.50,
    image_fill=green,image_stroke=green_edge,text_fill=purple,
    text_stroke=purple_edge,match_fill=match,grid_stroke=grid,grid_font_pt=8.5)
vector_fanout(C,source=text_encoder.port("output"),
    targets=[(matrix.port(f"column_{i}")[0],5.50) for i in range(4)],
    trunk=5.33,orientation="down",color=ink,omitted_index=2)
vector_fanout(C,source=image_encoder.port("output"),
    targets=[matrix.port(f"row_{i}") for i in range(4)],
    trunk=3.43,orientation="right",color=ink,omitted_index=2)
C.text("4 shown members; diagonal positives",6.25,6.52,3.25,.40,11,align="left",color=muted)
C.text("Member ports remain distinct from the group",6.25,6.96,4.1,.33,10,align="left",color=muted)

spec={"id":"ml_component_gallery","title":"Parameterized ML component gallery",
      "canvas":{"width_in":16,"height_in":9},"style":{"font":"Arial"},
      "elements":C.elements}
(OUT/"ml_component_gallery.json").write_text(json.dumps(spec,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
render(spec,OUT/"ml_component_gallery.svg",OUT/"ml_component_gallery.pptx")
print(f"Rendered {len(C.elements)} editable gallery elements")
