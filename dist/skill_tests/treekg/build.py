#!/usr/bin/env python3
"""Editable source-grounded explanatory redraw of Tree-KG Figure 2."""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
from render_figure_spec import render  # noqa: E402
from scientific_ir import CONTRACTS, enrich_spec, validate_drawn_routes, validate_spec  # noqa: E402

ID = "TK01_treekg_technical_route"
TOPO = json.loads((OUT / "expected_topology.json").read_text(encoding="utf-8"))
STYLE = json.loads((OUT / "source_style.json").read_text(encoding="utf-8"))
SCHEMA = json.loads((ROOT / "specs/figure_spec_v76.schema.json").read_text(encoding="utf-8"))
assert TOPO["figure_id"] == ID and 5 <= len(STYLE["anchors"]) <= 7
REQUIRED = {tuple(v) for v in TOPO["required_edges"]}
PDF_SHA = hashlib.sha256((OUT / "source_tree_kg_acl2025.pdf").read_bytes()).hexdigest()
CONTRACTS[ID] = {
    "claim": TOPO["claim"], "archetype": "schematic_led_composite", "output_mode": "presentation",
    "unverified": ["Presentation redraw; no claim of pixel identity, exact operator scheduling, or ACL endorsement."],
    "source": "dist/skill_tests/treekg/source_tree_kg_acl2025.pdf",
    "source_locator": "PDF page 3, Figure 2; Sections 3.1–3.3; PDF SHA-256 " + PDF_SHA,
    "evidence_status": "source_visible_redraw",
    "evidence_scope": "Two phases, explicit tree, horizontal relations, six expansion operators and integration of new sources.",
    "reuse": "Scholarly derivative redraw with citation; no source image embedded."
}

INK = "#2B3031"
MUTED = "#5B6467"
GREEN = "#D3EAD2"
YELLOW = "#F3F0B0"
PEACH = "#F5D3AC"
BLUE = "#D8EAF1"
PINK = "#F2D5DD"
TAN = "#B9A47C"
E = []
EDGES = []
NODE_GEOMETRY = {}

def text(s, x, y, w, h, size=11, bold=False, align="center", color=INK, sid=None):
    z = dict(type="text", text=s, x=x, y=y, w=w, h=h, size=size, bold=bold, align=align, color=color)
    if sid: z["semantic_id"] = sid
    E.append(z)

def rect(x,y,w,h,fill="#FFFFFF",stroke=INK,sw=.9,dash=False,radius=.05,sid=None):
    z=dict(type="rect",x=x,y=y,w=w,h=h,fill=fill,stroke=stroke,sw=sw,radius=radius)
    if dash:z["dash"]=True
    if sid:z["semantic_id"]=sid
    E.append(z)

def line(x1,y1,x2,y2,color=INK,sw=1,arrow=False,dash=False,link=None):
    z=dict(type="line",x1=x1,y1=y1,x2=x2,y2=y2,color=color,sw=sw,arrow=arrow)
    if dash:z["dash"]=True
    if link:z["semantic_link"]=link
    E.append(z)

def route(a,b,points,color=INK,dash=False):
    EDGES.append((a,b))
    for i,(p,q) in enumerate(zip(points,points[1:])):
        line(*p,*q,color=color,sw=1.25,arrow=i==len(points)-2,dash=dash,link=f"{a}__{b}")

def node(sid,label,cx,cy,r=.27,fill=YELLOW,size=8.6):
    NODE_GEOMETRY[(cx,cy)] = r
    E.append(dict(type="ellipse",x=cx-r,y=cy-r,w=2*r,h=2*r,fill=fill,stroke=INK,sw=.85,semantic_id=sid))
    if label:text(label,cx-r+.02,cy-r+.025,2*r-.04,2*r-.05,max(9.5,size))

def op(n,label,x,y,w=3.1):
    sid={"1":"convolution","2":"aggregation","3":"embedding","4":"deduplication","5":"prediction","6":"integration"}[n]
    text(f"{n}  {label}",x,y,w,.27,12,bold=True,align="left",sid=sid)
    line(x,y+.32,x+w,y+.32,color="#A6AFB1",sw=.6)

def graph_line(a,b,color=INK,dash=False):
    # Paper-like graph edges terminate at circular node boundaries, never through labels.
    dx,dy=b[0]-a[0],b[1]-a[1]
    length=math.hypot(dx,dy)
    if not length:return
    ra=NODE_GEOMETRY.get(a,0);rb=NODE_GEOMETRY.get(b,0)
    ux,uy=dx/length,dy/length
    line(a[0]+ux*ra,a[1]+uy*ra,b[0]-ux*rb,b[1]-uy*rb,color=color,sw=.95,dash=dash)

text("Tree-KG｜从教材树形骨架到可扩展知识图谱",.45,.20,14.9,.45,21,bold=True,align="left")
text("依据 Niu et al., ACL 2025, Figure 2 与 §3.2–3.3 的可编辑讲解版",.47,.69,14.9,.27,10.4,align="left",color=MUTED)
line(.45,1.05,15.55,1.05,color="#A7B0B0",sw=.8)

# The source's asymmetric two-phase framing, with graph marks in place of repeated process boxes.
rect(.45,1.42,4.12,6.65,stroke="#5E6768",sw=1.2,radius=.08,sid="explicit_kg")
rect(4.87,1.42,10.68,6.65,stroke="#5E6768",sw=1.2,radius=.08,sid="expansion")
text("I  初始构建 · Explicit KG",.68,1.52,3.63,.33,14.4,bold=True,align="left")
text("II  迭代扩展 · Hidden KG",5.13,1.52,9.95,.33,14.4,bold=True,align="left")

# Input is visibly a structured document, rather than a generic data box.
for dx,dy in [(.12,.10),(.06,.05),(0,0)]:
    rect(.85+dx,2.06+dy,1.02,.76,fill="#FFFFFF",stroke="#7B7770",sw=.75,radius=0,sid="textbook" if dx==0 else None)
for yy,ww in [(2.24,.68),(2.41,.61),(2.58,.73)]:line(.98,yy,.98+ww,yy,color="#7B7770",sw=.7)
text("结构化教材",2.02,2.14,1.87,.33,12,bold=True,align="left")
text("章 / 节 / 小节",2.02,2.50,1.91,.26,10.5,align="left",color=MUTED)
text("正则分段",.78,3.11,1.06,.27,11.1,bold=True,sid="segmentation")
text("自底向上摘要",1.95,3.11,1.63,.27,11.1,bold=True,sid="summary")
text("实体、关系抽取",2.55,3.59,1.78,.27,10.6,bold=True,sid="extraction")
route("textbook","segmentation",[(1.36,2.87),(1.36,3.05)],TAN)
route("segmentation","summary",[(1.85,3.29),(1.93,3.29)],TAN)
route("summary","extraction",[(3.10,3.41),(3.10,3.54)],TAN)
route("extraction","explicit_kg",[(3.48,3.92),(3.48,4.06),(2.46,4.06),(2.46,4.18)],TAN)
text("① 目录与实体树（纵向边）",.73,4.20,3.22,.24,10.3,bold=True,align="left",color=MUTED)
node("pre_root","电磁学",2.40,4.66,.23,GREEN,8.0)
node("pre_section_a","电荷",1.50,5.13,.22,GREEN,8.0)
node("pre_section_b","库仑定律",3.31,5.13,.24,GREEN,7.2)
node("pre_entity_a","负电荷",1.03,5.62,.22,YELLOW,7.3)
node("pre_entity_b","电子",1.91,5.62,.22,YELLOW,8.0)
node("pre_entity_c","电子",3.07,5.62,.22,YELLOW,8.0)
node("pre_entity_d","电场",3.94,5.62,.22,YELLOW,8.0)
for a,b in [((2.40,4.66),(1.50,5.13)),((2.40,4.66),(3.31,5.13)),((1.50,5.13),(1.03,5.62)),((1.50,5.13),(1.91,5.62)),((3.31,5.13),(3.07,5.62)),((3.31,5.13),(3.94,5.62))]:graph_line(a,b)
line(4.29,5.83,4.29,6.09,color=TAN,sw=1.5,arrow=True)
text("② 关系抽取后（横向边）",.73,6.02,3.34,.24,10.3,bold=True,align="left",color=MUTED)
node("post_root","电磁学",2.40,6.48,.23,GREEN,8.0)
node("post_section_a","电荷",1.50,6.96,.22,GREEN,8.0)
node("post_section_b","库仑定律",3.31,6.96,.24,GREEN,7.2)
node("post_entity_a","负电荷",1.03,7.49,.22,YELLOW,7.3)
node("post_entity_b","电子",1.91,7.49,.22,YELLOW,8.0)
node("post_entity_c","正电荷",3.07,7.49,.22,YELLOW,7.3)
node("post_entity_d","电场",3.94,7.49,.22,YELLOW,8.0)
for a,b in [((2.40,6.48),(1.50,6.96)),((2.40,6.48),(3.31,6.96)),((1.50,6.96),(1.03,7.49)),((1.50,6.96),(1.91,7.49)),((3.31,6.96),(3.07,7.49)),((3.31,6.96),(3.94,7.49))]:graph_line(a,b)
graph_line((1.50,6.96),(3.31,6.96),"#8B6D68",True)
graph_line((1.91,7.49),(3.07,7.49),"#8B6D68",True)
text("显式 KG：目录骨架 + 领域实体",.75,7.78,3.45,.22,9.6,bold=True,align="left")

# Expansion operator vignettes. Graph transformations carry the visual content.
line(8.36,1.95,8.36,7.54,color="#B8C0C0",sw=.7,dash=True)
line(11.87,1.95,11.87,7.54,color="#B8C0C0",sw=.7,dash=True)
line(5.06,4.72,15.35,4.72,color="#B8C0C0",sw=.7,dash=True)

op("1","上下文卷积",5.14,2.03,2.94)
node("conv_center","电荷",6.60,3.47,.36,PEACH,9.6)
for name,cx,cy in [("电势",5.61,3.05),("电场",5.64,3.92),("电子",7.59,3.04),("正电荷",7.59,3.92)]:
    node("conv_"+name,name,cx,cy,.28,YELLOW,8)
    graph_line((6.60,3.47),(cx,cy))
text("邻域语义 → 节点描述",5.20,4.30,2.95,.23,10.1,align="left",color=MUTED)

op("2","实体聚合",8.59,2.03,2.98)
node("core","核心",10.01,3.13,.39,PEACH,10.1)
for name,cx,cy in [("现象",9.04,3.91),("属性",10.08,4.02),("效应",11.08,3.88)]:
    node("sub_"+name,name,cx,cy,.29,BLUE,8.6)
    graph_line((10.01,3.47),(cx,cy))
text("横向关联 → 核心/非核心纵向边",8.59,4.30,3.01,.23,9.6,align="left",color=MUTED)

op("6","结构整合",12.13,2.03,2.92)
node("old_a","",12.73,3.03,.20,GREEN)
node("old_b","",13.21,3.43,.20,GREEN)
node("old_c","",12.71,3.89,.20,YELLOW)
graph_line((12.73,3.03),(13.21,3.43));graph_line((13.21,3.43),(12.71,3.89))
text("+",13.55,3.30,.28,.28,20)
node("new_a","",14.20,3.08,.20,GREEN)
node("new_b","",14.67,3.45,.20,YELLOW)
node("new_c","",14.21,3.91,.20,YELLOW)
graph_line((14.20,3.08),(14.67,3.45));graph_line((14.67,3.45),(14.21,3.91))
graph_line((13.21,3.43),(14.20,3.08),"#8B6D68",True)
text("新文本子图 → 对齐并合并",12.12,4.30,3.12,.23,10,align="left",color=MUTED)

op("3","节点嵌入",5.14,4.91,2.94)
node("embed_a","A",5.78,6.13,.30,PEACH,11)
node("embed_b","B",7.05,5.86,.30,PEACH,11)
node("embed_c","C",7.36,6.73,.30,YELLOW,11)
graph_line((5.78,6.13),(7.05,5.86),"#809096",True)
graph_line((7.05,5.86),(7.36,6.73),"#809096",True)
text("描述 → 向量；近邻检索",5.20,7.32,2.92,.23,10.1,align="left",color=MUTED)

op("4","实体去重",8.59,4.91,2.98)
node("dup_a","电荷",9.27,5.96,.34,PINK,9)
node("dup_b","Electric\ncharge",10.78,6.01,.37,PINK,8.1)
line(9.63,5.96,10.38,6.00,color="#8B6D68",sw=1.05,dash=True)
text("同角色 + 近邻 + LLM 判同",8.61,6.70,2.97,.23,9.8,align="left",color=MUTED)
text("并查集合并",8.61,7.32,2.92,.23,10.1,align="left",color=MUTED)

op("5","边预测",12.13,4.91,2.92)
node("pred_a","",12.67,6.03,.23,YELLOW)
node("pred_b","",13.60,5.83,.23,YELLOW)
node("pred_c","",14.63,6.43,.23,YELLOW)
graph_line((12.67,6.03),(13.60,5.83))
graph_line((13.60,5.83),(14.63,6.43),"#8B6D68",True)
text("cos(zᵤ,zᵥ) + AA + CA",12.13,6.82,3.06,.23,10.2,align="left")
text("排序 → LLM 强度阈值 → 加边",12.13,7.32,3.04,.23,9.8,align="left",color=MUTED)

route("explicit_kg","expansion",[(4.61,4.58),(4.81,4.58)],TAN)
text("新增文本子图",13.64,2.49,1.38,.23,9.7,color=MUTED,sid="new_sources")
text("扩展后的 Tree-KG",12.47,7.72,2.67,.25,11.2,bold=True,sid="expanded_kg")

text("图注：六类算子可灵活组合；图中不规定固定执行顺序。颜色区分类别；虚线表示横向、候选或推断关系。",.49,8.26,15.02,.33,10.3,align="left",color=MUTED)

assert set(EDGES)==REQUIRED, (set(EDGES)^REQUIRED)
assert set(TOPO["required_nodes"]) <= {e.get("semantic_id") for e in E}
spec=enrich_spec({"id":ID,"title":"Tree-KG technical route", "canvas":{"width_in":16,"height_in":9},
                  "style":{"font":"Microsoft YaHei"},"semantic_edges":[list(x) for x in EDGES],"elements":E})
jsonschema.validate(spec,SCHEMA)
validate_spec(spec)
validate_drawn_routes(spec,REQUIRED)
(OUT/(ID+".json")).write_text(json.dumps(spec,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
render(spec,OUT/(ID+".svg"),OUT/(ID+".pptx"))
print(f"Rendered {ID}; {len(E)} native elements; {len(EDGES)} audited semantic routes")
