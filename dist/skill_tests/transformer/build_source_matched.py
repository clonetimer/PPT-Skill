#!/usr/bin/env python3
"""Editable, source-style-matched redraw of Transformer Figures 1 and 2."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
from scientific_ir import CONTRACTS, enrich_spec, validate_drawn_routes, validate_spec  # noqa: E402
from render_figure_spec import render  # noqa: E402

TOPO = json.loads((OUT / "source_matched_topology.json").read_text(encoding="utf-8"))
STYLE = json.loads((OUT / "source_style.json").read_text(encoding="utf-8"))
assert 5 <= len(STYLE["anchors"]) <= 7
assert all(a["evidence"] and a["observation"] and a["decision"] for a in STYLE["anchors"])
SCHEMA = json.loads((ROOT / "specs/figure_spec_v76.schema.json").read_text(encoding="utf-8"))
INK="#222222"; PEACH="#F5D6AE"; CYAN="#BDE1EC"; YELLOW="#F4F1AC"
PINK="#F7D7D7"; LAVENDER="#D6CFE5"; GREEN="#CFE8D0"; GRAY="#EDEDED"


class Fig:
    def __init__(self, id, w, h, locator, claim):
        self.id=id; self.w=w; self.h=h; self.e=[]; self.edges=[]
        self.expected={tuple(v) for v in TOPO[id]}
        CONTRACTS[id]={"claim":claim,"archetype":"schematic_led_composite",
          "output_mode":"presentation",
          "unverified":["Source-matched structural redraw; no claim of pixel identity or journal acceptance."],
          "source":"dist/skill_tests/transformer/source_attention_is_all_you_need.pdf",
          "source_locator":locator,"evidence_status":"source_visible_redraw",
          "evidence_scope":"Figures 1-2 visual grammar and critical model relations; source PDF SHA-256 records the original file.",
          "reuse":"Scholarly derivative redraw with attribution to Vaswani et al.; no source image embedded."}
    def text(self,s,x,y,w,h,size=11,align="center",sid=None,bold=False,color=INK):
        z=dict(type="text",text=s,x=x,y=y,w=w,h=h,size=size,align=align,bold=bold,color=color)
        if sid:z["semantic_id"]=sid
        self.e.append(z)
    def rect(self,x,y,w,h,fill="#FFFFFF",sid=None,sw=1.15,stroke=INK,radius=.04):
        z=dict(type="rect",x=x,y=y,w=w,h=h,fill=fill,stroke=stroke,sw=sw,radius=radius)
        if sid:z["semantic_id"]=sid
        self.e.append(z)
    def box(self,sid,label,x,y,w,h,fill,size=11):
        self.rect(x,y,w,h,fill,sid)
        self.text(label,x+.035,y+.015,w-.07,h-.03,size)
    def ellipse(self,x,y,w,h,fill="#FFFFFF",sid=None,sw=1.15):
        z=dict(type="ellipse",x=x,y=y,w=w,h=h,fill=fill,stroke=INK,sw=sw)
        if sid:z["semantic_id"]=sid
        self.e.append(z)
    def line(self,x1,y1,x2,y2,arrow=False,link=None,sw=1.15,color=INK):
        z=dict(type="line",x1=x1,y1=y1,x2=x2,y2=y2,arrow=arrow,sw=sw,color=color)
        if link:z["semantic_link"]=link
        self.e.append(z)
    def route(self,a,b,*pts):
        self.edges.append((a,b))
        for i,(p,q) in enumerate(zip(pts,pts[1:])):
            self.line(*p,*q,arrow=i==len(pts)-2,link=f"{a}__{b}")
    def wave(self,x,y,w,h,sid=None):
        self.ellipse(x,y,w,h,"#FFFFFF",sid)
        nodes=[(.12,.50),(.22,.27),(.32,.25),(.43,.46),(.54,.73),(.65,.75),(.76,.53),(.88,.49)]
        self.e.append(dict(type="polyline",points=[(x+u*w,y+v*h) for u,v in nodes],color=INK,sw=.95))
    def plus(self,sid,x,y,d=.28):
        self.ellipse(x,y,d,d,"#FFFFFF",sid)
        self.text("+",x+.02,y+.003,d-.04,d-.01,13)
    def depth(self,x,y,w,h,n=3):
        for j in range(n,0,-1):
            self.rect(x+j*.08,y-j*.075,w,h,"#F4F4F4",sw=.75,stroke="#A7A7A7",radius=.16)
        self.rect(x,y,w,h,GRAY,sw=1.2,radius=.16)
    def finish(self):
        assert set(self.edges)==self.expected,(self.id,set(self.edges)^self.expected)
        spec=enrich_spec({"id":self.id,"title":self.id,
            "canvas":{"width_in":self.w,"height_in":self.h},
            "style":{"font":"Microsoft YaHei"},
            "semantic_edges":[list(p) for p in self.edges],"elements":self.e})
        jsonschema.validate(spec,SCHEMA);validate_spec(spec)
        validate_drawn_routes(spec,self.expected)
        (OUT/(self.id+".json")).write_text(json.dumps(spec,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        render(spec,OUT/(self.id+".svg"),OUT/(self.id+".pptx"))
        return spec


f=Fig("TR03_transformer_architecture_source_matched",9,9.1,
      "PDF p. 3, Figure 1; explanatory text in Section 3.1",
      "Original Transformer has upward encoder and decoder streams, positional sums, post-norm residual sublayers, encoder-to-decoder cross attention, and output projection.")
f.text("Output\nprobabilities",6.07,.13,1.52,.43,11,sid="probabilities")
f.box("softmax","Softmax",6.07,.68,1.52,.31,GREEN,11)
f.box("linear","Linear",6.07,1.11,1.52,.31,LAVENDER,11)
f.route("softmax","probabilities",(6.83,.68),(6.83,.59))
f.route("linear","softmax",(6.83,1.11),(6.83,1.02))

# Source-specific repeated layer silhouettes and residual loops.
f.depth(1.35,3.10,2.65,3.62)
f.depth(5.05,2.02,3.11,4.70)
f.text("N × 6",.76,4.70,.57,.30,11)
f.text("N × 6",8.28,4.34,.57,.30,11)
f.box("enc_norm2","Add & Norm",2.04,3.48,1.27,.31,YELLOW,10.4)
f.box("enc_ffn","Feed Forward",1.90,3.99,1.55,.53,CYAN,10.8)
f.box("enc_norm1","Add & Norm",2.04,4.74,1.27,.31,YELLOW,10.4)
f.box("enc_self","Multi-Head\nAttention",1.90,5.24,1.55,.63,PEACH,10.6)
f.route("enc_self","enc_norm1",(2.67,5.24),(2.67,5.08))
f.route("enc_norm1","enc_ffn",(2.67,4.74),(2.67,4.55))
f.route("enc_ffn","enc_norm2",(2.67,3.99),(2.67,3.82))
# Each side loop starts at the pre-sublayer stream and enters its Add & Norm.
f.line(2.67,5.96,1.65,5.96);f.line(1.65,5.96,1.65,4.90)
f.line(1.65,4.90,2.00,4.90,arrow=True)
f.line(2.67,4.64,1.51,4.64);f.line(1.51,4.64,1.51,3.63)
f.line(1.51,3.63,2.00,3.63,arrow=True)

f.box("dec_norm3","Add & Norm",6.30,2.41,1.26,.31,YELLOW,10.2)
f.box("dec_ffn","Feed Forward",6.15,2.89,1.56,.53,CYAN,10.8)
f.box("dec_norm2","Add & Norm",6.30,3.63,1.26,.31,YELLOW,10.2)
f.box("dec_cross","Multi-Head\nAttention",6.15,4.10,1.56,.55,PEACH,10.4)
f.box("dec_norm1","Add & Norm",6.30,4.88,1.26,.31,YELLOW,10.2)
f.box("dec_masked","Masked\nMulti-Head Attention",6.15,5.39,1.56,.69,PEACH,9.6)
for a,b,x,y1,y2 in [
 ("dec_masked","dec_norm1",6.93,5.39,5.22),
 ("dec_norm1","dec_cross",6.93,4.88,4.68),
 ("dec_cross","dec_norm2",6.93,4.10,3.97),
 ("dec_norm2","dec_ffn",6.93,3.63,3.45),
 ("dec_ffn","dec_norm3",6.93,2.89,2.75),
 ("dec_norm3","linear",6.93,2.41,1.45),
]:f.route(a,b,(x,y1),(x,y2))
for pre,top in [(6.17,5.04),(4.76,3.79),(3.51,2.56)]:
    f.line(6.93,pre,7.95,pre);f.line(7.95,pre,7.95,top)
    f.line(7.95,top,7.60,top,arrow=True)

f.route("enc_norm2","dec_cross",(3.31,3.64),(4.55,3.64),
        (4.55,4.37),(6.11,4.37))
f.line(5.42,4.37,5.42,4.24)
f.line(5.42,4.24,6.11,4.24,arrow=True)
f.text("encoder K,V",4.56,4.04,1.32,.20,9.1)

# Position is a distinct summand, not text inside the embedding box.
f.plus("src_add",2.55,7.11,.27)
f.wave(1.50,7.08,.48,.33,"src_pe")
f.text("Positional\nEncoding",.72,7.05,.75,.45,9.4,align="right")
f.box("src_embed","Input Embedding",2.05,7.61,1.30,.41,PINK,10.4)
f.text("Inputs",2.17,8.34,1.06,.29,11,sid="source_tokens")
f.route("source_tokens","src_embed",(2.70,8.34),(2.70,8.05))
f.route("src_embed","src_add",(2.70,7.61),(2.70,7.42))
f.route("src_pe","src_add",(1.98,7.24),(2.51,7.24))
f.route("src_add","enc_self",(2.69,7.11),(2.69,5.91))

f.plus("tgt_add",6.56,7.11,.27)
f.wave(7.65,7.08,.48,.33,"tgt_pe")
f.text("Positional\nEncoding",8.16,7.05,.75,.45,9.4,align="left")
f.box("tgt_embed","Output Embedding",6.20,7.61,1.45,.41,PINK,10.4)
f.text("Outputs\n(shifted right)",6.20,8.30,1.45,.45,10.4,sid="target_tokens")
f.route("target_tokens","tgt_embed",(6.92,8.30),(6.92,8.05))
f.route("tgt_embed","tgt_add",(6.92,7.61),(6.70,7.43))
f.route("tgt_pe","tgt_add",(7.65,7.24),(6.86,7.24))
f.route("tgt_add","dec_masked",(6.70,7.11),(6.70,6.12))
f.text("Vaswani et al. (2017), Fig. 1 · source-matched structural redraw",1.10,8.82,6.90,.18,8.9)
f.finish()


g=Fig("TR04_transformer_attention_source_matched",10.5,6.2,
      "PDF p. 4, Figure 2; attention equations in Section 3.2",
      "Q and K form scaled scores; an optional mask precedes softmax; V bypasses scoring and is multiplied by the weights; per-head projections operate in parallel before concatenation.")
g.text("Scaled Dot-Product Attention",.45,.30,4.10,.37,15)
g.text("Multi-Head Attention",5.55,.30,4.45,.37,15)
# Left: operator-specific shapes and three separate inputs.
g.box("context","MatMul",1.77,1.06,1.15,.42,LAVENDER,11)
g.box("weights","Softmax",1.77,1.70,1.15,.42,GREEN,11)
g.box("mask","Mask (opt.)",1.72,2.34,1.25,.42,PINK,10.5)
g.box("scale","Scale / √dₖ",1.77,2.98,1.15,.42,YELLOW,10.3)
g.box("score","MatMul",1.77,3.62,1.15,.42,LAVENDER,11)
for a,b,y1,y2 in [("score","scale",3.62,3.43),("scale","mask",2.98,2.79),
                   ("mask","weights",2.34,2.15),("weights","context",1.70,1.51)]:
    g.route(a,b,(2.34,y1),(2.34,y2))
g.text("Q",1.18,4.55,.30,.30,12,sid="q")
g.text("K",2.55,4.55,.30,.30,12,sid="k")
g.text("V",3.68,4.55,.30,.30,12,sid="v")
g.route("q","score",(1.33,4.55),(1.33,4.25),(1.97,4.25),(1.97,4.08))
g.route("k","score",(2.70,4.55),(2.70,4.08))
g.route("v","context",(3.83,4.55),(3.83,1.27),(2.96,1.27))
g.text("Attention(Q,K,V) = softmax(QKᵀ/√dₖ + M)V",.32,5.25,4.60,.35,11)
g.text("M 为可选掩码；被屏蔽位置在 Softmax 前加 −∞。",.32,5.64,4.60,.29,9.5)

# Right: the h replicated heads are visible behind their three projections.
g.text("Output",7.36,.81,1.19,.28,11,sid="mh_output")
g.box("mh_linear","Linear Wᴼ",7.31,1.24,1.30,.40,"#FFFFFF",10.7)
g.box("concat","Concat",7.31,1.87,1.30,.40,YELLOW,11)
for j in (3,2,1):g.rect(6.69+j*.075,2.55-j*.07,2.53,.62,"#F0F0F0",sw=.7,stroke="#A8A8A8")
g.box("heads","Scaled Dot-Product\nAttention × h",6.69,2.55,2.53,.62,LAVENDER,10.5)
g.text("h = 8",9.35,2.72,.70,.25,10)
for sid,x,label in [("proj_v",6.12,"Linear"),("proj_k",7.44,"Linear"),("proj_q",8.76,"Linear")]:
    for j in (2,1):g.rect(x+j*.05,3.85-j*.05,1.08,.40,"#F0F0F0",sw=.6,stroke="#ADADAD")
    g.box(sid,label,x,3.85,1.08,.40,"#FFFFFF",10.5)
for sid,x,label in [("mh_v",6.45,"V"),("mh_k",7.77,"K"),("mh_q",9.09,"Q")]:
    g.text(label,x,4.70,.32,.29,12,sid=sid)
for sid,x in [("mh_v",6.65),("mh_k",7.97),("mh_q",9.29)]:
    target={"mh_v":"proj_v","mh_k":"proj_k","mh_q":"proj_q"}[sid]
    g.route(sid,target,(x,4.70),(x,4.28))
for sid,x1,x2 in [("proj_v",6.66,7.21),("proj_k",7.98,7.95),("proj_q",9.30,8.69)]:
    g.route(sid,"heads",(x1,3.85),(x1,3.42),(x2,3.42),(x2,3.20))
g.route("heads","concat",(7.95,2.55),(7.95,2.30))
g.route("concat","mh_linear",(7.95,1.87),(7.95,1.67))
g.route("mh_linear","mh_output",(7.95,1.24),(7.95,1.12))
g.text("每个头使用独立 Q/K/V 投影，结果拼接后再线性映射。",5.53,5.25,4.58,.36,10.2)
g.text("Vaswani et al. (2017), Fig. 2 · source-matched structural redraw",.55,6.00,9.50,.16,9)
g.finish()
print("Built two source-matched editable Transformer figures")
