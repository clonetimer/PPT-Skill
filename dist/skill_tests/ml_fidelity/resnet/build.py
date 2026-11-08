#!/usr/bin/env python3
"""Editable redraw of ResNet CVPR 2016 Figure 2."""
from __future__ import annotations

import sys
from pathlib import Path

OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(OUT.parent))
from figurelib import Figure  # noqa: E402
from ml_figure_components import addition_junction  # noqa: E402

F=Figure(OUT,"MLR01_resnet_residual_block",9,5.45,
         "A residual block learns F(x) through two weight layers while passing x by an identity shortcut to the additive junction before a final ReLU.",
         "https://www.cv-foundation.org/openaccess/content_cvpr_2016/papers/He_Deep_Residual_Learning_CVPR_2016_paper.pdf",
         "PDF page 2 Figure 2; Sections 3.1–3.2")
INK="#111111"

# Scientific marks follow the original's compact black-and-white vertical grammar.
F.text("x",3.55,.45,.34,.30,24,font="Times New Roman",sid="x")
F.rect(2.73,1.42,2.04,.62,fill="#FFFFFF",stroke=INK,sw=1.35,sid="weight1")
F.text("weight layer",2.86,1.54,1.78,.34,17,font="Arial")
F.text("relu",3.94,2.22,.84,.30,17,align="left",font="Arial",sid="relu1")
F.rect(2.73,2.74,2.04,.62,fill="#FFFFFF",stroke=INK,sw=1.35,sid="weight2")
F.text("weight layer",2.86,2.86,1.78,.34,17,font="Arial")
add=addition_junction(F,sid="add",x=3.49,y=4.00,diameter=.51,stroke=INK)
F.text("relu",3.92,4.60,.74,.30,17,align="left",font="Arial",sid="relu2")
F.text("𝓕(x)",1.26,2.52,1.07,.49,22,font="Times New Roman")
F.text("𝓕(x) + x",.86,3.92,2.03,.47,22,font="Times New Roman")
F.text("x",6.43,2.60,.38,.34,24,font="Times New Roman")
F.text("identity",6.42,2.99,1.43,.36,17,align="left",font="Arial")

F.route("x","weight1",[(3.74,.77),(3.74,1.35)],INK,1.15)
F.route("weight1","weight2",[(3.74,2.04),(3.74,2.68)],INK,1.15)
F.route("weight2","add",[(3.74,3.36),(3.74,3.94)],INK,1.15)
F.route("add","relu2",[(3.74,4.51),(3.74,4.93)],INK,1.15)

# Sampled cubic bypass, still fully editable as native connectors.
def bezier(p0,p1,p2,p3,n=64):
    out=[]
    for i in range(n+1):
        t=i/n;u=1-t
        out.append((u**3*p0[0]+3*u*u*t*p1[0]+3*u*t*t*p2[0]+t**3*p3[0],
                    u**3*p0[1]+3*u*u*t*p1[1]+3*u*t*t*p2[1]+t**3*p3[1]))
    return out
arc=[(3.74,.80),(4.62,.80)]
arc+=bezier((4.62,.80),(6.06,.80),(6.10,1.70),(6.10,2.48))[1:]
arc+=bezier((6.10,2.48),(6.10,3.62),(5.47,4.25),(4.08,4.25))[1:]
F.route("x","add",arc,INK,1.15)

F.finish(OUT/"expected_topology.json",font="Arial")
