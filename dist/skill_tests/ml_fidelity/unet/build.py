#!/usr/bin/env python3
"""Editable, source-grammar redraw of U-Net MICCAI 2015 Figure 1."""
from __future__ import annotations

import sys
from pathlib import Path

OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(OUT.parent))
from figurelib import Figure  # noqa: E402
from ml_figure_components import crop_concat_pair, feature_map_strip  # noqa: E402

F=Figure(OUT,"MLU01_unet_architecture",16,9.2,
         "The original U-Net has four copy-and-crop skip paths and valid-convolution spatial contraction from 572×572 input to 388×388 segmentation output.",
         "https://arxiv.org/pdf/1505.04597","PDF page 2 Figure 1; Section 2",
         ["Source-composition redraw; small spatial labels require zoom at projection distance."])
BLUE="#74A0CE";BORDER="#38669A";DARK_BLUE="#081681";POOL="#930600";UP="#068C15";SKIP="#B6B8BA";TEAL="#008F91";GRAY="#767676"

def bar(sid,x,y,w,h,channels,size,white=False,show_channel=True,show_dim=True):
    return feature_map_strip(F,sid=sid,x=x,y=y,w=w,h=h,channels=channels,
        spatial_size=size,fill=BLUE,stroke=BORDER,label_color=GRAY,white=white,
        show_channel=show_channel,show_dimension=show_dim,
        dimension_side="right" if sid.startswith("dec") or sid=="output" else "left",
        dimension_band="inside" if white else "below")

def conv(x1,x2,y):F.line(x1,y,x2,y,color=DARK_BLUE,sw=2.5,arrow=True)

# Contracting path. A thin input tile precedes two valid 3×3 convolutions per level.
bar("input",.87,.95,.065,2.40,1,"572×572")
enc=[
    (1.31,.95,2.40,64,("570×570","568×568")),
    (2.60,3.64,1.52,128,("282×282","280×280")),
    (3.91,5.37,.94,256,("138×138","136×136")),
    (5.18,6.55,.57,512,("66×66","64×64")),
]
for i,(x,y,h,c,sz) in enumerate(enc):
    w=.105+.025*i
    # Semantic anchor spans the stage; arrow checks target the stage, not a single slab.
    F.text("",x-.05,y-.02,.62,h+.04,1,sid=f"enc{i}")
    bar(f"enc{i}_first",x,y,w,h,c,sz[0])
    bar(f"enc{i}",x+.31,y,w,h,c,sz[1])
    conv(x+w+.035,x+.31-.04,y+h*.28)
    # crop boundary is a distinct mark on the feature map used for the skip.
    F.line(x+.31+w-.012,y+.18,x+.31+w-.012,y+h-.18,color=BORDER,sw=.7,dash=True)

F.text("",6.02,7.33,1.15,.50,1,sid="bottleneck")
bar("bottleneck_input",6.06,7.36,.20,.37,512,"32×32")
bar("bottleneck_first",6.42,7.36,.25,.37,1024,"30×30")
bar("bottleneck",6.88,7.36,.25,.37,1024,"28×28")
conv(6.06+.20+.02,6.42-.04,7.46)
conv(6.42+.25+.02,6.88-.04,7.46)

# Pooling transitions: 568²→284²→140²→68²→32².
pool_info=[(2.26,3.64,1.52,64,"284×284"),(3.57,5.37,.94,128,"140×140"),
           (4.84,6.55,.57,256,"68×68"),(6.06,7.36,.37,512,"32×32")]
for i,(px,py,ph,pc,pdim) in enumerate(pool_info):
    if i<3:bar(f"pool{i}",px,py,.08,ph,pc,pdim)
    srcx=enc[i][0]+.31+(.105+.025*i)
    srcy=enc[i][1]+enc[i][2]
    # Downward pool mark connects to the new, channel-preserving half-size state.
    F.route(f"enc{i}",f"pool{i}" if i<3 else "bottleneck",[(srcx,srcy),(srcx,srcy+.17),(px+.04,srcy+.17),(px+.04,py)],POOL,1.55)
    if i<3:conv(px+.10,enc[i+1][0]-.035,py+ph*.28)

# Expanding path. The first thin white slab is the copy/crop feature map.
dec=[
    (7.61,6.585,.50,512,"56×56","54×54","52×52",512),
    (8.94,5.48,.72,256,"104×104","102×102","100×100",256),
    (10.27,3.86,1.08,128,"200×200","198×198","196×196",128),
    (11.60,1.325,1.65,64,"392×392","390×390","388×388",64),
]
for level,(x,y,h,c,sz0,sz1,sz2,cc) in zip((3,2,1,0),dec):
    white_w=.08; blue_w=.08
    F.text("",x-.05,y-.02,.92,h+.04,1,sid=f"dec{level}")
    pair=crop_concat_pair(F,sid=str(level),x=x,y=y,h=h,channels_per_half=cc,
        spatial_size=sz0,fill=BLUE,stroke=BORDER,label_color=GRAY,
        half_width=white_w,gap=.02)
    bar(f"dec{level}_first",x+.36,y,.13,h,c,sz1)
    bar(f"dec{level}",x+.67,y,.13,h,c,sz2)
    conv(x+.19,x+.32,y+h*.28)
    conv(x+.50,x+.63,y+h*.28)

# Four copy-and-crop transfers, each to the white concatenated feature slab.
skip_pairs=[(3,5.18+.31+.18,6.55+.16,7.61,6.55+.16),
            (2,3.91+.31+.155,5.37+.26,8.94,5.37+.26),
            (1,2.60+.31+.13,3.64+.43,10.27,3.64+.43),
            (0,1.31+.31+.105,.95+.67,11.60,.95+.67)]
for i,sx,sy,dx,dy in skip_pairs:
    F.route(f"enc{i}",f"copy{i}",[(sx+.025,sy),(dx-.13,dy),(dx-.015,dy)],SKIP,3.0)

# Green up-convolutions feed the next higher-resolution decoder level.
up_pairs=[("bottleneck","up3",7.13,7.46,7.75,7.085),
          ("dec3","up2",8.41,6.71,9.08,6.20),
          ("dec2","up1",9.74,5.63,10.41,4.94),
          ("dec1","up0",11.07,4.07,11.74,2.975)]
for a,b,sx,sy,dx,dy in up_pairs:
    F.route(a,b,[(sx,sy),(dx,sy),(dx,dy)],UP,2.2)

bar("output",12.66,1.325,.068,1.65,2,"388×388")
F.route("input","enc0",[(.95,1.62),(1.26,1.62)],DARK_BLUE,1.4)
F.route("dec0","output",[(12.40,1.62),(12.63,1.62)],TEAL,1.8)
F.text("input\nimage\ntile",.10,1.18,.61,.86,15,align="right")
F.text("output\nsegmentation\nmap",12.85,1.18,1.66,.86,14,align="left")

# The source uses a five-color arrow legend, not box-shaped operation cards.
legend=[("conv 3×3, ReLU",DARK_BLUE), ("copy and crop",SKIP),("max pool 2×2",POOL),("up-conv 2×2",UP),("conv 1×1",TEAL)]
for j,(label,color) in enumerate(legend):
    y=5.55+j*.50
    if j==2:F.line(12.84,y-.17,12.84,y+.17,color=color,sw=2.3,arrow=True)
    elif j==3:F.line(12.84,y+.17,12.84,y-.17,color=color,sw=2.3,arrow=True)
    else:F.line(12.64,y,13.04,y,color=color,sw=2.3,arrow=True)
    F.text(label,13.13,y-.16,2.55,.31,13,align="left",color=color)

F.finish(OUT/"expected_topology.json",font="Arial")
