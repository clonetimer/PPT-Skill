"""Source-contract revision after preserved, independently scored first passes."""
from __future__ import annotations

import math
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"ml_fidelity"))
from figurelib import Figure
from ml_figure_components import (addition_junction,multihead_neighbor_bundle,
                                  multihead_self_loop,token_strip,
                                  vector_math_label)


def node_label(f: Figure, x: float, y: float, index: str, prime: bool=False) -> None:
    """Editable vector h notation without fragile combining-arrow glyphs."""
    sub={"1":"₁","2":"₂","3":"₃","4":"₄","5":"₅","6":"₆"}[index]
    vector_math_label(f,sid="h_output_label" if prime else f"h_{index}_label",
                      text="h"+("′" if prime else "")+sub,
                      x=x-(.20 if prime else .16),y=y-.08,
                      w=.40 if prime else .32,h=.25,font_pt=14,
                      arrow_fraction=.40 if prime else .45)


def gat() -> None:
    folder=HERE/"gat";ink="#171717"
    f=Figure(folder,"GAT_Figure1_revision",14,5.35,
        "Figure 1 shows shared pairwise attention and K=3 independent neighborhood heads with node 1's self contribution.",
        "https://arxiv.org/pdf/1710.10903","Figure 1, PDF page 4; Section 2.1",
        ["Source-composition redraw; colored waves are editable piecewise lines, not copied source art."])
    # Paper's two left groups feed a LeakyReLU attention score, then softmax.
    acx,acy=2.65,2.225
    f.ellipse(2.37,1.95,.55,.55,"#FFFFFF",ink,1.1,sid="attention_a")
    f.line(2.50,2.37,2.66,2.27,color=ink,sw=1.1)
    f.line(2.66,2.27,2.80,2.08,color=ink,sw=1.1)
    f.text("LeakyReLU",2.96,2.16,1.25,.26,10,align="left",sid="activation_label")
    for j in range(8):
        x=.30+j*.62;cx=x+.125
        f.ellipse(x,3.63,.25,.25,"#FFFFFF",ink,.95,sid=f"input_{j}")
        ex=acx+(cx-acx)*.10
        ey=acy+math.sqrt(.275**2-(ex-acx)**2)
        f.route(f"input_{j}","attention_a",[(cx,3.63),(ex,ey)],ink,.68,
                arrow_size=.025)
    f.ellipse(2.37,.55,.55,.55,"#FFFFFF",ink,1.1,sid="alpha_ij")
    f.text("αᵢⱼ",2.40,.69,.48,.25,13)
    f.route("attention_a","alpha_ij",[(acx,1.95),(acx,1.10)],ink,.8)
    f.text("softmaxⱼ",2.85,1.24,1.00,.28,12,align="left")
    vector_math_label(f,sid="attention_weight_label",text="a",x=3.22,y=2.48,
                      w=.30,h=.25,font_pt=13)
    f.line(.25,3.95,2.38,3.95,color=ink,sw=.7)
    f.line(2.55,3.95,5.15,3.95,color=ink,sw=.7)
    vector_math_label(f,sid="left_i_vector",text="W hᵢ",x=.90,y=4.05,
                      w=1.04,h=.30,font_pt=15,arrow_fraction=.65)
    vector_math_label(f,sid="left_j_vector",text="W hⱼ",x=3.40,y=4.05,
                      w=1.04,h=.30,font_pt=15,arrow_fraction=.65)
    # The graph is node 1 plus five neighbors. Separate head paths encode
    # independent attention even in grayscale through their wave phases.
    colors=["#2459BB","#149937","#9F20D6"]
    centers={1:(8.78,2.47),2:(7.73,1.04),3:(6.93,2.42),
             4:(7.75,3.74),5:(8.78,4.25),6:(9.82,3.63)}
    radius=.29
    for number,(x,y) in centers.items():
        f.ellipse(x-radius,y-radius,2*radius,2*radius,"#FFFFFF",ink,1.0,
                  sid=f"node_{number}")
        node_label(f,x,y,str(number))
    for number in (2,3,4,5,6):
        multihead_neighbor_bundle(f,sid=f"heads_{number}_1",source=centers[number],
            target=centers[1],source_radius=radius,target_radius=radius,
            colors=colors,source_sid=f"node_{number}",target_sid="node_1")
    multihead_self_loop(f,sid="heads_1_1",center=centers[1],
                        node_radius=radius,colors=colors,node_sid="node_1")
    vector_math_label(f,sid="self_attention_label",text="α₁₁",
                      x=9.29,y=1.71,w=.52,h=.22,font_pt=11,
                      arrow_fraction=.40)
    for text,x,y in [("α₁₂",7.29,1.48),("α₁₃",7.50,2.10),
                     ("α₁₄",7.32,3.11),("α₁₅",8.04,3.55),
                     ("α₁₆",9.68,2.91)]:
        vector_math_label(f,sid=f"attention_{text}_label",text=text,
                          x=x,y=y,w=.50,h=.22,font_pt=11,arrow_fraction=.40)
    ox,oy=12.22,2.47
    f.ellipse(ox-.30,oy-.30,.60,.60,"#FFFFFF",ink,1.0,sid="output_h1")
    node_label(f,ox,oy,"1",prime=True)
    multihead_neighbor_bundle(f,sid="heads_to_output",source=centers[1],
        target=(ox,oy),source_radius=radius,target_radius=.30,
        colors=colors,source_sid="node_1",target_sid="output_h1")
    f.text("concat/avg",10.13,2.03,1.45,.28,12,sid="aggregation_label")
    f.finish(folder/"expected_revision_topology.json",font="Times New Roman")


def detr() -> None:
    folder=HERE/"detr";ink="#242424";gray="#777777"
    f=Figure(folder,"DETR_Figure2_revision",16,4.2,
        "Figure 2 shows CNN features and positional encoding forming encoder tokens, then parallel object-query predictions.",
        "https://www.ecva.net/papers/eccv_2020/papers_ECCV/papers/123460205.pdf",
        "Figure 2, PDF page 6; Section 3.2",
        ["The bird photograph is a source-paper excerpt for local evaluation; the detection rectangles within that excerpt are raster. Model nodes, links, token groups and prediction labels are editable.",
         "Token count is schematic and the repeated FFN objects represent one shared feed-forward network."],
        embedded_source_excerpt=True)
    regions=[(.18,2.50,"backbone"),(2.73,4.34,"encoder"),
             (7.12,3.42,"decoder"),(10.59,2.68,"prediction heads")]
    for x,w,label in regions:
        f.rect(x,.28,w,3.39,"#FFFFFF",ink,.6,dash=True)
        f.text(label,x+.08,.34,w-.16,.27,13)
    # Paper-specific CNN taper and spatial intensity stack remain source style,
    # while the junction and token rows are reusable components.
    f.polygon([(.42,1.49),(1.25,1.60),(1.25,2.18),(.42,2.29)],
              "#FFFFFF",ink,.8,sid="cnn")
    f.text("CNN",.62,1.76,.43,.25,12)
    f.rect(1.62,1.42,.24,.86,"#FFFFFF",ink,.75,sid="image_features")
    f.text("set of image\nfeatures",.92,.82,1.63,.42,11)
    f.route("cnn","image_features",[(1.25,1.89),(1.62,1.89)],ink,.9)
    for i,color in enumerate(("#F4F4F4","#D9D9D9","#A9A9A9","#707070")):
        f.rect(.45+i*.075,2.73-i*.07,.84,.50,color,gray,.55,
               sid="position_encoding" if i==3 else None)
    f.text("positional encoding",.43,3.29,1.92,.26,11)
    plus=addition_junction(f,sid="position_add",x=2.15,y=1.73,diameter=.31,
                           stroke=ink,symbol_font_pt=12)
    f.route("image_features","position_add",[(1.86,1.85),plus.port("shortcut_in_left")],ink,.8)
    f.route("position_encoding","position_add",[(1.515,2.73),(2.305,2.04)],ink,.8)
    input_row=token_strip(f,sid="enc_input",x=3.04,y=3.05,count=9,box=.22,gap=.20,
                          fill="#FFFFFF",stroke=ink,ellipsis_index=7,
                          group_outline=True)
    output_row=token_strip(f,sid="enc_output",x=3.04,y=.96,count=9,box=.22,gap=.20,
                           fill="#FFFFFF",stroke=ink,ellipsis_index=7,
                           group_outline=True)
    f.route("position_add","enc_input_group",
            [plus.port("shortcut_in_right"),(2.70,1.885),(2.70,3.16),
             input_row.port("group_left")],ink,.75)
    f.rect(3.01,1.46,3.62,1.32,"#FFFFFF",ink,.85,sid="transformer_encoder")
    f.text("transformer\nencoder",3.60,1.79,2.39,.52,15)
    for i in (0,1,2,3,4,5,6,8):
        tx=input_row.port(f"top_{i}")[0]
        f.route(f"enc_input_token_{i}","transformer_encoder",
                [(tx,3.05),(tx,2.78)],ink,.55)
        tx=output_row.port(f"bottom_{i}")[0]
        f.route("transformer_encoder",f"enc_output_token_{i}",
                [(tx,1.46),(tx,1.18)],ink,.55)
    f.rect(7.44,1.46,2.64,1.32,"#FFFFFF",ink,.85,sid="transformer_decoder")
    f.text("transformer\ndecoder",7.75,1.79,2.03,.52,15)
    last=output_row.port("group_right")
    f.route("enc_output_group","transformer_decoder",
            [(last[0],1.07),(6.92,1.07),(7.44,1.94)],ink,.75)
    colors=["#E27A85","#79BF83","#E9CE72","#77A9DE"]
    for i,color in enumerate(colors):
        qx=7.73+i*.55
        f.rect(qx,3.10,.20,.20,color,ink,.45,sid=f"query_{i}")
        f.route(f"query_{i}","transformer_decoder",
                [(qx+.10,3.10),(qx+.10,2.78)],ink,.6)
        f.rect(qx,1.10,.20,.20,color,ink,.45,sid=f"decoded_{i}")
        f.route("transformer_decoder",f"decoded_{i}",
                [(qx+.10,1.46),(qx+.10,1.30)],ink,.6)
    f.text("object queries",7.79,3.38,2.25,.26,11)
    results=["class,\nbox","no\nobject","class,\nbox","no\nobject"]
    for i,(color,label) in enumerate(zip(colors,results)):
        yy=.86+i*.64
        f.rect(10.88,yy,.67,.44,"#FFFFFF",ink,.7,sid=f"ffn_{i}")
        f.text("FFN",10.94,yy+.09,.55,.24,11)
        f.rect(11.88,yy,1.10,.44,"#FFFFFF",color,1.15,sid=f"prediction_{i}")
        f.text(label,11.94,yy+.035,.98,.37,10,sid=f"prediction_{i}_label")
        qx=7.73+i*.55
        lane_y=.72+i*.075
        f.route(f"decoded_{i}",f"ffn_{i}",
                [(qx+.10,1.10),(qx+.10,lane_y),(10.55,lane_y),(10.88,yy+.22)],ink,.62)
        f.route(f"ffn_{i}",f"prediction_{i}",
                [(11.55,yy+.22),(11.88,yy+.22)],color,.75)
    f.text("shared FFN across output positions",10.70,3.30,2.47,.22,9,
           sid="shared_head_note")
    f.asset(folder/"bird_excerpt.png",
            "https://www.ecva.net/papers/eccv_2020/papers_ECCV/papers/123460205.pdf",
            "Reuse rights not independently cleared; local evaluation only",
            "Carion et al.",status="source_artwork_excerpt",
            scope="Exact crop of PDF page 6 Figure 2 right result panel at 160 dpi, pixels (907,262)-(1070,447); includes photograph and raster detection rectangles.",
            reuse="Local comparison only; replace with a licensed original photograph and native detection boxes before public redistribution.")
    f.image(folder/"bird_excerpt.png",13.42,.32,2.40,3.30,sid="source_bird_example")
    f.finish(folder/"expected_revision_topology.json",font="Times New Roman")


if __name__=="__main__":
    gat();detr()
