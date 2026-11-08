"""Held-out paper test of the reusable residual-variant component."""
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"ml_fidelity"))
from figurelib import Figure
from ml_figure_components import ResidualLayer,residual_variant

F=Figure(HERE,"MLH01_wide_resnet_variants",16,5.2,
    "Wide Residual Networks Figure 1 compares basic, bottleneck, basic-wide and wide-dropout residual blocks with identity shortcuts.",
    "https://arxiv.org/pdf/1605.07146","Figure 1, PDF page 2; Section 2",
    ["Source-composition redraw; gray identity arrows and layer widths are schematic, not data-scaled.",
     "The source circle-cross is shown as a plus sign to make the addition in its Equation (1) explicit; a short explanatory footnote was added."])

orange="#F0BD96";blue="#8DCFE4";red="#E59DA5";stroke="#65727B"
variants=[
    ("a","(a) basic",[("conv3×3",1.28,orange),("conv3×3",1.28,orange)]),
    ("b","(b) bottleneck",[("conv1×1",2.12,blue),("conv3×3",1.28,orange),("conv1×1",2.12,blue)]),
    ("c","(c) basic-wide",[("conv3×3",2.28,orange),("conv3×3",2.28,orange)]),
    ("d","(d) wide-dropout",[("conv3×3",2.28,orange),("dropout",2.28,red),("conv3×3",2.28,orange)]),
]

for j,(sid,caption,layers) in enumerate(variants):
    x=.45+j*3.85
    residual_variant(F,sid=sid,x=x,y=.26,
        layers=[ResidualLayer(*row) for row in layers],
        layer_stroke=stroke,line_color="#202020",shortcut_fill="#D1D1D1",
        panel_width=3.25,layer_height=.28,layer_gap=.20 if len(layers)==3 else .32)
    F.text(caption,x+.08,4.42,3.0,.34,15,font="Times New Roman")

F.text("BN and ReLU precede each convolution (omitted in the source figure).",
       .55,4.91,14.9,.26,10,align="left",color="#555555")
F.finish(HERE/"expected_topology.json",font="Times New Roman")
