"""Frozen-component first-pass redraws of two different ML figure families."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"ml_fidelity"))
from figurelib import Figure
from ml_figure_components import addition_junction


def finish(figure: Figure) -> None:
    fixture=figure.folder/"expected_topology.json"
    fixture.write_text(json.dumps({"figure_id":figure.id,"required_nodes":[],
                                   "required_edges":[]},indent=2)+"\n",encoding="utf-8")
    # Historical negative control: preserve the original empty-topology output.
    figure.finish(fixture,font="Times New Roman",allow_unchecked_first_pass=True)


def gat() -> None:
    folder=HERE/"gat"
    f=Figure(folder,"GAT_Figure1_first_pass",14,5.35,
        "Figure 1 explains pairwise graph attention and three-head neighborhood aggregation.",
        "https://arxiv.org/pdf/1710.10903","Figure 1, PDF page 4; Section 2.1",
        ["First-pass reconstruction with frozen components; colored attention lines are straight rather than the source's wavy strokes."])
    black="#1B1B1B";blue="#2665C2";green="#23A823";violet="#AF29E0"
    # Pairwise attention mechanism: two transformed feature groups, shared a,
    # neighborhood-normalized alpha_ij. No false sequential box pipeline.
    for j in range(8):
        x=.30+j*.62
        f.ellipse(x,3.63,.25,.25,"#FFFFFF",black,.95,sid=f"input_{j}")
        f.line(x+.125,3.63,2.65,2.35,color=black,sw=.7,arrow=True)
    f.ellipse(2.37,1.95,.55,.55,"#FFFFFF",black,1.1,sid="attention_a")
    f.text("a",2.50,2.08,.30,.25,16,font="Times New Roman")
    f.line(2.65,1.95,2.65,1.12,color=black,sw=.8,arrow=True)
    f.ellipse(2.37,.55,.55,.55,"#FFFFFF",black,1.1,sid="alpha_ij")
    f.text("αᵢⱼ",2.40,.69,.48,.25,13)
    f.text("softmaxⱼ",2.82,1.26,1.05,.28,12,align="left",color=black)
    f.text("a⃗",3.29,2.49,.42,.3,14)
    f.line(.25,3.95,2.38,3.95,color=black,sw=.7)
    f.line(2.55,3.95,5.15,3.95,color=black,sw=.7)
    f.text("W h⃗ᵢ",.83,4.05,1.1,.32,15)
    f.text("W h⃗ⱼ",3.31,4.05,1.1,.32,15)
    # Three independent head calculations over the same neighborhood.
    cx,cy=8.78,2.48
    nodes={
        1:(cx,cy),2:(7.74,1.06),3:(6.92,2.42),4:(7.76,3.76),
        5:(8.78,4.29),6:(9.83,3.66),
    }
    for number,(x,y) in nodes.items():
        f.ellipse(x-.29,y-.29,.58,.58,"#FFFFFF",black,1.0,sid=f"node_{number}")
        f.text(f"h⃗{number}",x-.20,y-.10,.40,.25,14)
    # Slightly separated straight strands preserve three heads but expose a
    # source-style gap for the first-pass critic.
    for number in (2,3,4,5,6):
        x,y=nodes[number]
        vx,vy=cx-x,cy-y
        length=math.hypot(vx,vy)
        px,py=-vy/length,vx/length
        for k,(color,shift) in enumerate(((blue,-.065),(green,0),(violet,.065))):
            start=(x+vx/length*.29+px*shift,y+vy/length*.29+py*shift)
            end=(cx-vx/length*.32+px*shift,cy-vy/length*.32+py*shift)
            f.line(*start,*end,color=color,sw=1.0,arrow=True)
    for k,color in enumerate((blue,green,violet)):
        f.ellipse(8.94+k*.035,1.88-k*.035,.43+k*.04,.40+k*.04,
                  "#FFFFFF",color,.7,sid=f"self_head_{k}")
    f.text("α₁₂",7.82,1.72,.60,.25,11)
    f.text("α₁₃",7.32,2.20,.60,.25,11)
    f.text("α₁₄",8.05,3.16,.60,.25,11)
    f.text("α₁₅",8.85,3.63,.60,.25,11)
    f.text("α₁₆",9.41,3.10,.60,.25,11)
    for k,color in enumerate((blue,green,violet)):
        f.line(9.08,2.48+k*.045,11.91,2.48+k*.045,
               color=color,sw=1.3,arrow=True)
    f.text("concat/avg",10.09,2.04,1.48,.30,12)
    f.ellipse(12.01,2.21,.62,.62,"#FFFFFF",black,1.0,sid="output_h1")
    f.text("h⃗′₁",12.13,2.37,.37,.24,14)
    finish(f)


def detr() -> None:
    folder=HERE/"detr"
    f=Figure(folder,"DETR_Figure2_first_pass",16,4.2,
        "Figure 2 shows DETR's image-feature encoder, parallel object queries and shared prediction head.",
        "https://www.ecva.net/papers/eccv_2020/papers_ECCV/papers/123460205.pdf",
        "Figure 2, PDF page 6; Section 3.2",
        ["First-pass reconstruction with frozen components; the right bird photograph is a source-paper excerpt for local evaluation, including its original boxes."])
    ink="#242424";gray="#777777";red="#E27A85";green="#79BF83";yellow="#E9CE72";blue="#77A9DE"
    regions=[(.18,2.50,"backbone"),(2.73,4.34,"encoder"),(7.12,3.42,"decoder"),(10.59,2.68,"prediction heads")]
    for x,w,label in regions:
        f.rect(x,.28,w,3.39,"#FFFFFF",ink,.6,dash=True)
        f.text(label,x+.08,.34,w-.16,.27,13,align="center")
    f.rect(.47,1.60,.75,.57,"#FFFFFF",ink,.8,sid="cnn")
    f.text("CNN",.53,1.76,.63,.25,12)
    f.rect(1.58,1.45,.28,.90,"#FFFFFF",ink,.75,sid="image_features")
    f.text("set of image\nfeatures",.92,.85,1.75,.46,11)
    f.line(1.22,1.88,1.58,1.88,color=ink,sw=.9,arrow=True)
    for i in range(4):
        f.rect(.42+i*.075,2.68-i*.07,.90,.57,"#FFFFFF",gray,.55)
    f.text("positional encoding",.45,3.28,1.90,.26,11)
    f.line(1.86,1.89,2.20,1.89,color=ink,sw=.9,arrow=True)
    f.line(1.66,2.68,2.20,2.05,color=ink,sw=.9,arrow=True)
    plus=addition_junction(f,sid="position_add",x=2.15,y=1.73,diameter=.31,
                           stroke=ink,symbol_font_pt=12)
    f.line(2.46,1.89,2.92,1.89,color=ink,sw=.9,arrow=True)
    # Flattened visual tokens run above and below the encoder, following the
    # source's many-to-many token rather than a single large arrow.
    for i in range(9):
        xx=2.92+i*.40
        f.rect(xx,.94,.27,.27,"#FFFFFF",ink,.6,sid=f"enc_in_{i}")
        f.rect(xx,3.05,.27,.27,"#FFFFFF",ink,.6,sid=f"enc_out_{i}")
        f.line(xx+.135,1.21,xx+.135,1.43,color=ink,sw=.55,arrow=True)
        f.line(xx+.135,2.79,xx+.135,3.05,color=ink,sw=.55,arrow=True)
    f.rect(3.01,1.45,3.50,1.34,"#FFFFFF",ink,.85,sid="transformer_encoder")
    f.text("transformer\nencoder",3.57,1.80,2.35,.52,15)
    f.line(2.46,1.89,3.04,1.89,color=ink,sw=.8,arrow=True)
    f.line(6.60,1.89,7.43,1.89,color=ink,sw=.9,arrow=True)
    f.rect(7.43,1.44,2.63,1.35,"#FFFFFF",ink,.85,sid="transformer_decoder")
    f.text("transformer\ndecoder",7.75,1.79,2.00,.52,15)
    query_colors=[red,green,yellow,blue]
    for i,color in enumerate(query_colors):
        qx=7.71+i*.55
        f.rect(qx,3.13,.20,.20,color,ink,.45,sid=f"query_{i}")
        f.line(qx+.10,3.13,qx+.10,2.79,color=ink,sw=.6,arrow=True)
        f.rect(qx,1.13,.20,.20,color,ink,.45,sid=f"decoded_{i}")
        f.line(qx+.10,1.44,qx+.10,1.33,color=ink,sw=.6,arrow=True)
    f.text("object queries",7.79,3.38,2.24,.26,11)
    targets=["class,\nbox","no\nobject","class,\nbox","no\nobject"]
    for i,(color,label) in enumerate(zip(query_colors,targets)):
        yy=.86+i*.64
        f.rect(10.88,yy,.67,.44,"#FFFFFF",ink,.7,sid=f"ffn_{i}")
        f.text("FFN",10.94,yy+.09,.55,.24,11)
        f.rect(11.88,yy,1.10,.44,"#FFFFFF",color,1.15,sid=f"prediction_{i}")
        f.text(label,11.94,yy+.035,.98,.37,10)
        f.line(9.98,1.22+i*.04,10.88,yy+.22,color=ink,sw=.65,arrow=True)
        f.line(11.55,yy+.22,11.88,yy+.22,color=color,sw=.75,arrow=True)
    f.image(folder/"bird_excerpt.png",13.41,.31,2.42,3.33,sid="source_bird_example")
    finish(f)


if __name__=="__main__":
    gat();detr()
