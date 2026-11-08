#!/usr/bin/env python3
"""Source-composition redraw of Niu et al. ACL 2025 Figure 2.

The paper figure is inspected at high resolution. All graph marks and labels are
editable PowerPoint primitives; licensed Tabler SVG icons are embedded as PNGs.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import jsonschema

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"tools"))
from render_figure_spec import render  # noqa: E402
from scientific_ir import CONTRACTS,enrich_spec,validate_spec  # noqa: E402

ID="TK02_treekg_source_composition"
PAPER=OUT/"source_tree_kg_acl2025.pdf"
ASSET=Path("dist/skill_tests/treekg/assets")
BLACK="#211F1D";GRAY="#77746F";TAN="#C0B18C"
GREEN="#D0E9CD";YELLOW="#F7F4AF";ORANGE="#F9D5A7";PINK="#F7D3D5";BLUE="#DDEFF5"
E=[];NODES={}

def txt(s,x,y,w,h,size=11,align="center",bold=False,italic=False,color=BLACK,sid=None):
    z=dict(type="text",text=s,x=x,y=y,w=w,h=h,size=size,align=align,bold=bold,italic=italic,color=color)
    if sid:z["semantic_id"]=sid
    E.append(z)
def rect(x,y,w,h,fill="#FFFFFF",stroke=BLACK,sw=.85,dash=False,sid=None):
    z=dict(type="rect",x=x,y=y,w=w,h=h,fill=fill,stroke=stroke,sw=sw,radius=0)
    if dash:z["dash"]=True
    if sid:z["semantic_id"]=sid
    E.append(z)
def line(x1,y1,x2,y2,color=BLACK,sw=.9,arrow=False,dash=False,link=None):
    z=dict(type="line",x1=x1,y1=y1,x2=x2,y2=y2,color=color,sw=sw,arrow=arrow)
    if dash:z["dash"]=True
    if link:z["semantic_link"]=link
    E.append(z)
def route(a,b,points,color=BLACK,sw=1,arrow=True,dash=False):
    for i,(p,q) in enumerate(zip(points,points[1:])):
        line(*p,*q,color=color,sw=sw,arrow=arrow and i==len(points)-2,dash=dash,link=f"{a}__{b}")
def circle(sid,label,cx,cy,r,fill,size=9.5):
    NODES[sid]=(cx,cy,r)
    E.append(dict(type="ellipse",x=cx-r,y=cy-r,w=2*r,h=2*r,fill=fill,stroke=BLACK,sw=.82,semantic_id=sid))
    if label:txt(label,cx-r+.015,cy-r+.015,2*r-.03,2*r-.03,size)
def edge(a,b,arrow=False,dash=False,color=BLACK,sw=.8):
    x1,y1,r1=NODES[a];x2,y2,r2=NODES[b]
    dx,dy=x2-x1,y2-y1;d=math.hypot(dx,dy);ux,uy=dx/d,dy/d
    line(x1+ux*r1,y1+uy*r1,x2-ux*r2,y2-uy*r2,color=color,sw=sw,arrow=arrow,dash=dash)
def dashed_oval(x,y,w,h,segments=42,color=BLACK):
    for i in range(0,segments,2):
        a=2*math.pi*i/segments;b=2*math.pi*(i+1)/segments
        line(x+w/2+w/2*math.cos(a),y+h/2+h/2*math.sin(a),
             x+w/2+w/2*math.cos(b),y+h/2+h/2*math.sin(b),color=color,sw=.8)
def icon(name,x,y,w,h=None):
    if h is None:h=w
    E.append(dict(type="image",path=str(ASSET/(name+".png")),x=x,y=y,w=w,h=h,
                  semantic_role="source_licensed_icon"))
def step(label,x,y,w,h=.40,size=10.5,sid=None):
    rect(x,y,w,h,sid=sid)
    txt(label,x+.045,y+.025,w-.09,h-.05,size,align="left")

# Same aspect ratio and phase boundaries as the published Figure 2.
txt("Initial Construction",.76,.12,4.12,.46,21)
txt("Iterative Expansion",8.10,.12,5.15,.46,21)
rect(.45,.73,4.74,9.26,sw=1.22,sid="initial_phase")
rect(5.76,.73,9.78,9.26,sw=1.22,sid="expansion_phase")
line(5.22,5.45,5.67,5.45,color="#747474",sw=2.4,arrow=True,link="initial_phase__expansion_phase")
line(15.56,5.45,15.94,5.45,color="#747474",sw=2.4,arrow=True)

# Left: textbook and two explicitly different KG states, as in the source.
txt("Structured Raw Text",.85,1.21,2.80,.28,12.4,align="left",sid="textbook")
icon("book-open-text",3.61,1.02,.82)
step("1. Segmentation\n2. Summarization\n3.1 Entity Extraction",.70,1.84,2.68,1.10,11.0,"initial_ops")
txt("Regular Expression\n& LLM",3.60,1.94,1.20,.57,10.4)
line(3.89,2.55,3.89,3.05,color=TAN,sw=2.3,arrow=True)
icon("robot",4.28,2.56,.48)

circle("l_top","Electro-\nmagnetism",3.73,3.61,.34,GREEN,9.0)
circle("l_cat_a","Section 1.1\nCharge",3.15,4.52,.35,GREEN,8.4)
circle("l_cat_b","Section 2.2\nCoulomb's\nLaw",4.42,4.52,.35,GREEN,7.7)
circle("l_ent_a","Negative\nCharge",2.73,5.43,.34,YELLOW,8.7)
circle("l_ent_b","Electron",3.85,5.43,.32,YELLOW,9.3)
circle("l_sum_a","Summary",4.36,3.77,.24,PINK,6.5)
circle("l_sum_b","Summary",3.73,4.86,.24,PINK,6.5)
circle("l_sum_c","Summary",4.92,5.17,.24,PINK,6.5)
for a,b in [("l_top","l_cat_a"),("l_top","l_cat_b"),("l_cat_a","l_ent_a"),("l_cat_a","l_ent_b")]:edge(a,b,arrow=True)
for a,b in [("l_sum_a","l_top"),("l_sum_b","l_cat_a"),("l_sum_c","l_cat_b")]:edge(a,b,arrow=True,dash=True)
txt("Vertical Edge",1.14,3.52,1.66,.27,10.8,align="left")
line(2.22,3.79,3.25,4.15,sw=.8)
txt("Catalog Node",.89,4.36,1.87,.27,10.8,align="left")
line(2.77,4.55,2.80,4.56,sw=.8)
txt("Entity Node",.83,5.15,1.48,.27,10.8,align="left")
line(2.33,5.32,2.42,5.39,sw=.8)

step("3.2 Relation\nExtraction",.72,6.16,1.94,.76,11.4,"relation_extraction")
line(3.90,6.06,3.90,6.82,color=TAN,sw=2.3,arrow=True)
icon("robot",4.27,6.24,.48)
circle("l2_top","Electro-\nmagnetism",3.73,7.26,.34,GREEN,9.0)
circle("l2_cat_a","Section 1.1\nCharge",3.12,8.15,.35,GREEN,8.4)
circle("l2_cat_b","Section 2.2\nCoulomb's\nLaw",4.43,8.15,.35,GREEN,7.7)
circle("l2_ent_a","Negative\nCharge",2.72,9.20,.34,YELLOW,8.7)
circle("l2_ent_b","Electron",3.83,9.20,.33,YELLOW,9.3)
for a,b in [("l2_top","l2_cat_a"),("l2_top","l2_cat_b"),("l2_cat_a","l2_ent_a"),("l2_cat_a","l2_ent_b")]:edge(a,b,arrow=True)
edge("l2_cat_a","l2_cat_b",arrow=True)
edge("l2_ent_b","l2_ent_a",arrow=True)
txt("obey",3.63,8.22,.36,.19,8.2)
txt("has",3.16,8.91,.25,.18,8.2)
txt("Horizontal Edge",.79,8.08,1.90,.31,10.8,align="left")

# Upper right 1: before and after contextual convolution, with robot glyph.
step("1. Contextual-based\n    Convolution",5.89,.85,2.37,.58,10.8,"convolution")
circle("c1_q","Charge",7.08,2.01,.27,YELLOW,8.5)
circle("c1_p","Electric\nPotential",7.80,1.66,.27,YELLOW,8.2)
circle("c1_f","Electric\nField",6.49,2.61,.27,YELLOW,8.2)
circle("c1_pos","Positive\nCharge",7.75,2.62,.27,YELLOW,8.2)
for a,b in [("c1_q","c1_p"),("c1_q","c1_f"),("c1_q","c1_pos")]:edge(a,b)
icon("robot",6.30,3.22,.46)
line(7.12,3.16,7.12,3.65,color=TAN,sw=2.15,arrow=True)
circle("c1_new","Charge",7.10,4.12,.35,ORANGE,9.4)
circle("c1_newp","Electric\nPotential",7.87,3.74,.28,YELLOW,8.2)
circle("c1_newf","Electric\nField",6.50,4.55,.28,YELLOW,8.2)
circle("c1_newpos","Positive\nCharge",7.77,4.57,.28,YELLOW,8.2)
for a,b in [("c1_new","c1_newp"),("c1_new","c1_newf"),("c1_new","c1_newpos")]:edge(a,b)
for a,b in [("c1_newp","c1_new"),("c1_newf","c1_new"),("c1_newpos","c1_new")]:edge(a,b,arrow=True,dash=True)

# Upper right 2: horizontal graph becomes core/non-core vertical relations.
line(8.48,.77,8.48,5.30,color=GRAY,sw=.75,dash=True)
step("2. Entity\n    Aggregation",8.61,.85,1.72,.58,10.8,"aggregation")
circle("a_charge","Charge",11.02,1.35,.27,YELLOW,8.6)
circle("a_negative","Negative\nCharge",11.43,1.95,.27,YELLOW,8.1)
circle("a_coulomb","Coulomb",12.28,1.74,.27,YELLOW,8.3)
circle("a_magnetic","Magnetic\nMoment",10.96,2.64,.27,YELLOW,8.0)
circle("a_electron","Electron",11.95,2.68,.27,YELLOW,8.4)
for a,b in [("a_charge","a_negative"),("a_charge","a_coulomb"),("a_negative","a_coulomb"),("a_electron","a_negative"),("a_electron","a_magnetic")]:edge(a,b,arrow=True)
txt("Horizontal Edges",8.67,2.54,1.84,.25,10.5,align="left")
icon("robot",10.27,3.16,.46)
line(11.33,3.00,11.33,3.55,color=TAN,sw=2.2,arrow=True)
circle("a_core_e","Electron",10.90,4.02,.31,PINK,8.7)
circle("a_core_c","Charge",11.88,4.02,.31,PINK,8.7)
circle("a_non_m","Magnetic\nMoment",10.54,4.75,.27,BLUE,7.9)
circle("a_non_n","Negative\nCharge",11.36,4.75,.27,BLUE,8.0)
circle("a_non_col","Coulomb",12.29,4.75,.27,BLUE,8.0)
for a,b in [("a_core_e","a_non_m"),("a_core_e","a_non_n"),("a_core_c","a_non_n"),("a_core_c","a_non_col")]:edge(a,b,arrow=True)
txt("Core",9.06,3.90,1.10,.21,10.1,align="left")
txt("Non-core",8.75,4.61,1.42,.21,10.1,align="left")

# Upper right 6: two overlapping structures merge through a robot operation.
line(12.77,.77,12.77,5.30,color=GRAY,sw=.75,dash=True)
step("6. Structure Integration",12.87,.85,2.32,.37,10.4,"integration")
for sid,cx,cy,fill in [("m1",13.30,1.70,GREEN),("m2",12.99,2.24,GREEN),("m3",13.72,2.23,GREEN),("m4",13.33,2.73,YELLOW),
                       ("n1",14.80,1.70,GREEN),("n2",14.48,2.24,GREEN),("n3",15.15,2.24,GREEN),("n4",14.78,2.73,YELLOW)]:circle(sid,"",cx,cy,.20,fill)
for a,b in [("m1","m2"),("m1","m3"),("m3","m4"),("n1","n2"),("n1","n3"),("n2","n4")]:edge(a,b,arrow=True)
edge("m3","n2",dash=True)
txt("Identical",13.72,1.97,.74,.21,9.4)
txt("+",13.95,2.44,.34,.33,18)
line(14.03,3.03,14.03,3.49,color=TAN,sw=2.1,arrow=True)
icon("robot",14.72,3.20,.44)
for sid,cx,cy,fill in [("r1",14.05,3.80,GREEN),("r2",13.53,4.39,GREEN),("r3",14.17,4.45,GREEN),("r4",14.82,4.30,GREEN),
                       ("r5",13.86,4.90,YELLOW),("r6",14.55,4.94,YELLOW)]:circle(sid,"",cx,cy,.18,fill)
for a,b in [("r1","r2"),("r1","r3"),("r1","r4"),("r3","r5"),("r3","r6"),("r5","r6")]:edge(a,b,arrow=True)

# Lower field: shared embedding/dedup decision, central LLM, scored candidate graphs.
line(5.79,5.39,15.50,5.39,color=BLACK,sw=.85,dash=True)
step("3. Node Embedding",5.89,5.48,2.38,.33,10.5,"embedding")
step("4. Entity Deduplication",5.89,5.90,2.38,.33,10.5,"deduplication")
step("5. Edge\n    Prediction",10.29,5.57,1.37,.52,10.5,"prediction")
line(10.16,5.43,10.16,9.92,color=GRAY,sw=.75,dash=True)
dashed_oval(5.98,6.66,2.83,2.89,36)
txt("Threshold",8.94,6.70,1.17,.22,9.7,align="left")
for sid,label,cx,cy,fill in [("d1","",6.59,7.64,ORANGE),("d2","Charge",7.30,8.12,ORANGE),("d3","",8.06,7.38,ORANGE),
                              ("d4","",8.05,8.50,ORANGE),("d5","",6.76,8.95,YELLOW),("d6","",7.45,9.16,YELLOW),
                              ("d7","",8.47,9.62,YELLOW)]:circle(sid,label,cx,cy,.30,fill,9.2)
icon("robot",9.24,7.67,.70)
txt("Identical?",8.89,7.34,.88,.22,9.5)
txt("Yes!",8.84,7.89,.34,.20,9.5)
txt("No!",8.84,8.54,.34,.20,9.5)
route("deduplication","integration",[(8.44,7.43),(9.15,7.87)],dash=True,arrow=True)
route("deduplication","integration",[(9.15,8.41),(8.38,8.62)],dash=True,arrow=True)
route("deduplication","integration",[(8.10,9.04),(9.16,8.24)],dash=True,arrow=True)

dashed_oval(11.72,6.56,1.08,1.16,28)
dashed_oval(12.90,6.53,2.18,1.25,32)
for sid,cx,cy in [("p1",12.08,7.02),("p2",12.40,7.43),("p3",13.28,7.01),("p4",14.08,6.80),("p5",13.83,7.46)]:circle(sid,"",cx,cy,.21,YELLOW)
for a,b in [("p1","p2"),("p3","p4"),("p3","p5"),("p4","p5")]:edge(a,b)
txt("Computed Score 1",11.78,7.87,1.70,.22,9.7)
txt("Strength",12.75,8.36,1.12,.22,9.7)
route("prediction","integration",[(12.67,8.08),(10.14,8.08)],dash=True,arrow=True)
route("prediction","integration",[(10.88,8.22),(13.72,8.22)],dash=True,arrow=True)
line(14.01,8.23,14.19,8.67,color=TAN,sw=2.2,arrow=True)
for sid,cx,cy in [("p6",13.10,8.78),("p7",12.82,9.25),("p8",13.70,9.18),("p9",14.28,9.06),("p10",14.19,9.65),("p11",13.39,9.63)]:circle(sid,"",cx,cy,.21,YELLOW)
for a,b in [("p6","p7"),("p6","p8"),("p8","p9"),("p8","p10"),("p7","p11"),("p11","p10")]:edge(a,b)
txt("Computed Score 2",10.95,8.37,1.61,.22,9.7)
route("prediction","integration",[(12.73,8.85),(10.18,8.45)],dash=True,arrow=True)

CONTRACTS[ID]={"claim":"Tree-KG constructs a textbook-derived explicit hierarchical KG, then expands and merges it with six flexible operator families.",
 "archetype":"schematic_led_composite","output_mode":"presentation",
 "unverified":["Source-composition redraw, not pixel identity or exact execution scheduling; small details remain compressed."],
 "source":"dist/skill_tests/treekg/source_tree_kg_acl2025.pdf",
 "source_locator":"PDF page 3 Figure 2; Sections 3.1–3.3; SHA-256 "+hashlib.sha256(PAPER.read_bytes()).hexdigest(),
 "evidence_status":"source_visible_redraw","evidence_scope":"Phase composition and operator before/after visual grammar.",
 "reuse":"New editable redraw with citation. Robot: Tabler Icons MIT; open book: Lucide ISC. Original Figure 2 image is not embedded."}
spec=enrich_spec({"id":ID,"title":"Tree-KG Figure 2 source-composition redraw",
 "canvas":{"width_in":16,"height_in":10.25},"style":{"font":"Times New Roman"},"elements":E,
 "semantic_edges":[["initial_phase","expansion_phase"]]})
schema=json.loads((ROOT/"specs/figure_spec_v76.schema.json").read_text(encoding="utf-8"))
jsonschema.validate(spec,schema)
validate_spec(spec)
(OUT/(ID+".json")).write_text(json.dumps(spec,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
render(spec,OUT/(ID+".svg"),OUT/(ID+".pptx"))
print(f"Rendered {ID}: {len(E)} elements")
