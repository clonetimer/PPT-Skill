#!/usr/bin/env python3
"""Build a source-grounded, one-page GAT explanation using invisible regions.

This authored example does not infer a model from a paper or run model weights.
All scientific marks are native FigureSpec primitives. Illustrative cell counts
and node/head counts are not experimental settings or measured attention values.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path

from single_page_composer import render_page, revise_region

INK = "#202D3A"
MUTED = "#5D6975"
BLUE = "#245C9F"
TEAL = "#187B72"
OCHRE = "#AE6B2D"
GRAY = "#A0AAB4"
WHITE = "#FFFFFF"
FONT = "Noto Sans CJK SC"
MATH = "DejaVu Sans"


class Marks:
    """A tiny authoring convenience for this example, not a model/API wrapper."""

    def __init__(self):
        self.elements = []

    def add(self, kind, sid, **kwargs):
        self.elements.append({"type": kind, "id": sid, **kwargs})

    def text(self, sid, text, x, y, w, h, size=15, color=INK,
             bold=False, align="left", font=FONT):
        self.add("text", sid, text=text, x=x, y=y, w=w, h=h,
                 size=size, color=color, bold=bold, align=align, font=font)

    def line(self, sid, x1, y1, x2, y2, color=INK, sw=1.1, arrow=False):
        self.add("line", sid, x1=x1, y1=y1, x2=x2, y2=y2,
                 color=color, sw=sw, arrow=arrow, arrow_size=.075)

    def circle(self, sid, cx, cy, r, fill=WHITE, stroke=INK, sw=1.3):
        self.add("ellipse", sid, x=cx-r, y=cy-r, w=2*r, h=2*r,
                 fill=fill, stroke=stroke, sw=sw)

    def vector(self, sid, x, y, width, height, color, count=4):
        # Equal cells indicate vector components, not a heatmap.
        for index in range(count):
            self.add("rect", f"{sid}_{index}", x=x+index*width/count,
                     y=y, w=width/count, h=height,
                     fill=WHITE, stroke=color, sw=1.2)

    def region(self, sid, x, y, w, h, role):
        return {"id": sid, "role": role,
                "bounds": {"x": x, "y": y, "w": w, "h": h},
                "spec": {"canvas": {"width_in": w, "height_in": h},
                         "elements": self.elements}}


def initial_page():
    regions = []
    m = Marks()
    m.text("series", "GRAPH ATTENTION NETWORKS  /  ICLR 2018", .55, .24, 11.9, .23,
           10.5, MUTED, font=MATH)
    m.text("title", "GAT：在邻域内学习“谁的信息更重要”", .55, .57, 12.2, .50,
           28, bold=True)
    m.text("claim", "共享特征变换，按邻域归一化，再加权聚合与多头融合。",
           .57, 1.12, 12.0, .30, 16, MUTED)
    m.line("rule", .55, 1.58, 12.78, 1.58, GRAY, .7)
    regions.append(m.region("header", 0, 0, 13.333, 1.65, "claim"))

    m = Marks()
    m.text("heading", "a  一个注意力头：邻居向目标节点传递消息", 0, 0, 5.55, .34,
           14, bold=True)
    center = (2.91, 1.90)
    nodes = {"j": (.63, 1.90), "k": (1.65, .78), "l": (1.52, 2.90),
             "m": (2.80, 3.10), "n": (4.10, 2.90)}
    labels = {"j": "hⱼ", "k": "hₖ", "l": "hₗ", "m": "hₘ", "n": "hₙ"}
    for index, (cx, cy) in nodes.items():
        dx, dy = center[0]-cx, center[1]-cy
        d = math.hypot(dx, dy)
        ux, uy = dx/d, dy/d
        color = BLUE if index == "j" else GRAY
        m.line(f"message_{index}_i", cx+ux*.245, cy+uy*.245,
               center[0]-ux*.31, center[1]-uy*.31, color, 1.6, True)
        m.circle(f"node_{index}", cx, cy, .245, stroke=color)
        m.text(f"label_{index}", labels[index], cx-.24, cy-.20, .48, .4,
               20, color=INK, align="center", font=MATH)
    m.circle("target_i", *center, .31, BLUE, BLUE)
    m.text("target_label", "hᵢ", center[0]-.27, center[1]-.22, .54, .44,
           23, WHITE, align="center", font=MATH)
    m.text("message_label", "αᵢⱼWhⱼ", 1.13, 1.48, 1.45, .32,
           19, BLUE, align="center", font=MATH)
    m.vector("feature_j", .25, 2.26, .76, .16, BLUE)
    # A cubic loop explicitly returns the node's own contribution to its update.
    p0, p1, p2, p3 = (2.79, 1.62), (2.50, .65), (4.17, .87), (3.16, 1.71)
    points = []
    for step in range(25):
        t = step/24
        points.append([(1-t)**3*p0[q] + 3*(1-t)**2*t*p1[q]
                       + 3*(1-t)*t*t*p2[q] + t**3*p3[q] for q in (0, 1)])
    m.add("polyline", "self_loop", points=points, color=GRAY, sw=1.6)
    m.line("self_loop_tip", *points[-2], *points[-1], GRAY, 1.6, True)
    m.text("self_weight", "αᵢᵢ", 3.46, 1.10, .66, .30, 17,
           MUTED, align="center", font=MATH)
    m.line("update", 3.27, 1.9, 4.64, 1.9, INK, 1.5, True)
    m.text("sum_activation", "Σ, σ", 3.64, 1.55, .72, .29,
           18, align="center", font=MATH)
    m.circle("updated_i", 4.97, 1.90, .29, WHITE, BLUE, 1.6)
    m.text("updated_label", "uᵢ", 4.71, 1.68, .52, .44, 22,
           BLUE, align="center", font=MATH)
    m.text("neighbor_note", "Nᵢ 包含自身；箭头表示消息流向。", .02, 3.43, 5.35, .30,
           12.5, MUTED)
    regions.append(m.region("neighborhood", .55, 1.82, 5.55, 3.80, "scientific_figure"))

    m = Marks()
    m.text("heading", "b  同一目标节点的邻居共同决定边权", 0, 0, 6.28, .34,
           14, bold=True)
    m.vector("target_feature", .12, .68, 1.02, .26, INK)
    m.text("concat", "∥", 1.17, .66, .22, .30, 20, align="center", font=MATH)
    m.vector("neighbor_feature", 1.42, .68, 1.02, .26, BLUE)
    m.text("target_feature_label", "Whᵢ", .12, 1.03, 1.02, .30,
           17, align="center", font=MATH)
    m.text("neighbor_feature_label", "Whⱼ", 1.42, 1.03, 1.02, .30,
           17, BLUE, align="center", font=MATH)
    m.line("pair_to_score", 2.52, .81, 2.98, .81, INK, 1.2, True)
    m.circle("attention", 3.34, .81, .27)
    m.text("attention_label", "aᵀ", 3.08, .61, .52, .40,
           18, align="center", font=MATH)
    m.line("score_nonlinearity", 3.66, .81, 5.14, .81, INK, 1.2, True)
    m.text("leaky_relu", "LeakyReLU", 3.75, .39, 1.43, .28,
           12.5, MUTED, align="center", font=MATH)
    m.text("raw_score", "eᵢⱼ", 5.30, .56, .75, .47,
           23, align="center", font=MATH)
    m.text("alpha", "αᵢⱼ =", .12, 1.74, 1.10, .46,
           24, BLUE, align="left", font=MATH)
    m.text("numerator", "exp(eᵢⱼ)", 1.30, 1.54, 2.55, .39,
           21, align="center", font=MATH)
    m.line("fraction", 1.24, 1.98, 3.98, 1.98, INK, 1.1)
    m.text("denominator", "Σₗ∈Nᵢ exp(eᵢₗ)", 1.20, 2.00, 2.87, .43,
           19, align="center", font=MATH)
    m.text("normalization_scope", "固定目标 i\n仅在 Nᵢ 内归一化", 4.30, 1.71, 1.95, .63,
           13.5, MUTED)
    regions.append(m.region("attention", 6.45, 1.82, 6.33, 2.67, "edge_calculation"))

    m = Marks()
    m.text("equation", "uᵢ = σ(Σⱼ∈Nᵢ αᵢⱼWhⱼ)", .02, .0, 5.53, .54,
           22, align="left", font=MATH)
    m.text("shared", "同一头内，W 与 a 在所有节点、边之间共享。", .02, .70, 5.5, .55,
           13, MUTED)
    regions.append(m.region("aggregation", .55, 5.72, 5.55, 1.18, "equation"))

    m = Marks()
    m.text("heading", "c  隐藏层：独立计算各头，再沿特征维拼接", 0, 0, 6.3, .34,
           14, bold=True)
    for index, (color, y, label) in enumerate([(BLUE, .60, "uᵢ⁽¹⁾"),
                                               (TEAL, .95, "uᵢ⁽²⁾"),
                                               (OCHRE, 1.30, "uᵢ⁽³⁾")]):
        m.vector(f"head_{index+1}", .12, y, .85, .18, color)
        m.text(f"head_label_{index+1}", label, 1.08, y-.10, .77, .38,
               16, color, align="left", font=MATH)
        # Each head is parallel, never a head-to-head sequential connection.
        m.line(f"head_to_concat_{index+1}", 1.91, y+.09,
               2.64, .90, color, 1.05, True)
        m.vector(f"concat_segment_{index+1}", 2.88+index*.78, .79, .78, .23, color)
    m.text("concat_label", "h′ᵢ = uᵢ⁽¹⁾ ∥ uᵢ⁽²⁾ ∥ uᵢ⁽³⁾", 2.75, 1.15, 3.55, .32,
           16, align="center", font=MATH)
    m.text("head_scope", "独立的 W⁽ᵏ⁾、a⁽ᵏ⁾", 2.80, .45, 3.05, .27,
           12, MUTED, align="center", font=MATH)
    m.text("final_layer", "预测层：先平均各头未激活的聚合值，再激活（式 6）。",
           .02, 1.67, 6.28, .43, 11.5, MUTED)
    regions.append(m.region("heads", 6.45, 4.77, 6.33, 2.12, "parallel_heads"))

    m = Marks()
    m.line("rule", .55, .02, 12.78, .02, GRAY, .7)
    m.text("citation", "Veličković et al.  Graph Attention Networks.  ICLR 2018 · Fig. 1 / Eqs. 1–6 · arXiv:1710.10903",
           .55, .10, 12.20, .23, 9.7, MUTED, font=MATH)
    m.text("schematic", "根据论文与作者代码改绘；六节点、三头及向量格数均为示意，不表示实验配置或实测权重。",
           .55, .35, 12.20, .23, 10.2, MUTED)
    regions.append(m.region("footer", 0, 6.91, 13.333, .59, "source"))
    return {
        "id": "GAT_single_page", "canvas": {"width_in": 13.333, "height_in": 7.5},
        "style": {"font": FONT}, "title": "GAT：在邻域内学习加权聚合",
        "claim": "Neighborhood-normalized attention weights aggregate projected neighbor features; independent heads concatenate in a hidden layer.",
        "input_completeness": "paper_figure_equations_and_author_code",
        "sources": [
            {"url": "https://arxiv.org/pdf/1710.10903v3", "locator": "Section 2.1, Figure 1, Equations (1)-(6)"},
            {"url": "https://github.com/PetarV-/GAT/blob/5af87e7fce2b90ae1cbd621cd58059036a3c7436/utils/layers.py", "locator": "Lines 6-34: shared transform, additive score, masked softmax, aggregation"},
            {"url": "https://github.com/PetarV-/GAT/blob/5af87e7fce2b90ae1cbd621cd58059036a3c7436/utils/process.py", "locator": "Lines 8-25: adjacency mask and self loops"},
            {"url": "https://github.com/PetarV-/GAT/blob/5af87e7fce2b90ae1cbd621cd58059036a3c7436/models/gat.py", "locator": "Lines 8-31: independent heads, concatenation, final averaging"}],
        "notes": "Authored mechanism explanation, not a pixel-matched reproduction or a measured attention map. The a/b panels expand one head and suppress the head superscript. u_i denotes the activated output of that one head; the c panel repeats the computation independently with separate W and a. Three heads and six nodes are illustrative. Vector cell counts do not imply a dimension. Per-edge colors highlight one example message; head colors in c identify independent outputs. For the final layer, average the unactivated head aggregates before the final activation (paper Eq. 6). The author Cora implementation averages identity-activation output heads into logits; this slide follows the paper's general formulation. Dropout, bias, training losses and all experiment-specific settings are omitted. Unicode mathematical labels are editable text, not Office Math equation objects.",
        "regions": regions,
    }


def apply_review(page, review):
    """Apply an observed review's local element updates through region replacement."""
    for region_id, replacement in review.get("region_replacements", {}).items():
        page = revise_region(page, region_id, replacement)
    for region_id, updates in review.get("region_updates", {}).items():
        source_region = next(r for r in page["regions"] if r["id"] == region_id)
        spec = copy.deepcopy(source_region["spec"])
        by_id = {element["id"]: element for element in spec["elements"]}
        for element_id, fields in updates.items():
            if element_id not in by_id:
                raise ValueError(f"Unknown element {region_id}/{element_id}")
            if "id" in fields or "type" in fields:
                raise ValueError("A layout review cannot change element identity/type")
            by_id[element_id].update(fields)
        page = revise_region(page, region_id, {"spec": spec})
    return page


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--review", type=Path, help="Apply a saved, observed local revision")
    parser.add_argument("--stem", default="GAT_single_page")
    args = parser.parse_args()
    page = initial_page()
    if args.review:
        page = apply_review(page, json.loads(args.review.read_text(encoding="utf-8")))
    outputs = render_page(page, args.output_dir, args.stem)
    for kind, path in outputs.items():
        print(f"{kind}: {path}")


if __name__ == "__main__":
    main()
