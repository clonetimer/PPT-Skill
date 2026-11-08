#!/usr/bin/env python3
"""Two linked, editable figures for the original 2017 Transformer."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import jsonschema
from pptx import Presentation
from pptx.util import Inches

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
from scientific_ir import CONTRACTS, enrich_spec, validate_drawn_routes, validate_spec  # noqa: E402
from render_figure_spec import clean_theme, render  # noqa: E402

TOPO = json.loads((OUT / "expected_topology.json").read_text(encoding="utf-8"))
SCHEMA = json.loads((ROOT / "specs/figure_spec_v76.schema.json").read_text(encoding="utf-8"))
NAVY = "#203343"; MUTED = "#526A7A"; BLUE = "#DDECF4"; TEAL = "#DDF0E9"
GOLD = "#F8ECD0"; PURPLE = "#EAE4F4"; STROKE = "#527084"


class Figure:
    def __init__(self, figure_id: str, claim: str, expected_key: str):
        self.id = figure_id
        self.elements: list[dict] = []
        self.edges: list[tuple[str, str]] = []
        self.expected = {tuple(edge) for edge in TOPO[expected_key]}
        CONTRACTS[figure_id] = {
            "claim": claim, "archetype": "schematic_led_composite",
            "output_mode": "presentation",
            "unverified": ["This is a paper-grounded reconstruction, not an exact Figure 1/2 redraw or a depiction of newer Transformer variants."],
            "source": "dist/skill_tests/transformer/SOURCE.md",
            "source_locator": "Vaswani et al. Figure 1, Figure 2, and Sections 3.1–3.5, identified in SOURCE.md",
            "evidence_status": "paper_grounded",
            "evidence_scope": claim,
            "reuse": "new editable schematic based on cited paper",
        }

    def text(self, s, x, y, w, h, size=12, *, bold=False, color=NAVY, align="center"):
        self.elements.append(dict(type="text", text=s, x=x, y=y, w=w, h=h,
                                  size=size, bold=bold, color=color, align=align))

    def rect(self, x, y, w, h, fill="#FFFFFF", *, sid=None, stroke=STROKE, sw=1,
             radius=.05):
        e = dict(type="rect", x=x, y=y, w=w, h=h, fill=fill, stroke=stroke,
                 sw=sw, radius=radius)
        if sid:
            e["semantic_id"] = sid
        self.elements.append(e)

    def box(self, sid, s, x, y, w, h, fill=BLUE, size=12):
        self.rect(x, y, w, h, fill, sid=sid)
        self.text(s, x+.06, y+.04, w-.12, h-.08, size, bold=True)

    def line(self, x1, y1, x2, y2, *, color=STROKE, sw=1.4, arrow=False,
             link=None, dash=False):
        e = dict(type="line", x1=x1, y1=y1, x2=x2, y2=y2, color=color,
                 sw=sw, arrow=arrow)
        if link:
            e["semantic_link"] = link
        if dash:
            e["dash"] = True
        self.elements.append(e)

    def route(self, source, target, *points):
        self.edges.append((source, target))
        for i, (p, q) in enumerate(zip(points, points[1:])):
            self.line(*p, *q, link=f"{source}__{target}",
                      arrow=i == len(points)-2, sw=1.65)

    def header(self, title, subtitle, page):
        self.text(title, .5, .20, 12.25, .43, 21, bold=True, align="left")
        self.text(subtitle, .5, .68, 12.25, .27, 11.2, color=MUTED, align="left")
        self.line(.5, 1.08, 12.82, 1.08, color="#9EB3BE", sw=.85)
        self.text(page, 12.08, 7.08, .72, .20, 9.3, color=MUTED, align="right")

    def finish(self):
        assert set(self.edges) == self.expected, (self.id, set(self.edges) ^ self.expected)
        spec = enrich_spec({"id": self.id, "title": self.id,
                            "canvas": {"width_in": 13.333, "height_in": 7.5},
                            "style": {"font": "Microsoft YaHei"},
                            "semantic_edges": [list(e) for e in self.edges],
                            "elements": self.elements})
        jsonschema.validate(spec, SCHEMA)
        validate_spec(spec)
        validate_drawn_routes(spec, self.expected)
        (OUT / f"{self.id}.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        render(spec, OUT / f"{self.id}.svg", OUT / f"{self.id}.pptx")
        return spec


a = Figure("TR01_transformer_architecture",
           "The original Transformer is a six-layer post-norm encoder–decoder with masked decoder self-attention and encoder-output cross-attention.",
           "architecture")
a.header("Transformer 原始架构｜编码器、解码器与信息流",
         "Vaswani et al. (2017) base model · 箭头表示张量依赖；旁路表示残差连接", "1 / 2")
a.text("编码器 × 6", .78, 1.18, 4.5, .30, 15, bold=True, align="left")
a.text("解码器 × 6", 7.20, 1.18, 4.8, .30, 15, bold=True, align="left")
a.box("source_tokens", "输入词元 x₁ … xₙ", .78, 1.56, 4.45, .44, BLUE, 12.5)
a.box("src_embed", "词嵌入 × √d_model  +  位置编码", .78, 2.10, 4.45, .48, BLUE, 12)
a.route("source_tokens", "src_embed", (3.00, 2.00), (3.00, 2.07))
a.rect(.70, 2.76, 4.70, 2.43, "#F5FAFC", stroke="#9FBAC7", sw=1)
a.text("重复层 N = 6", .88, 2.79, 4.30, .22, 10.5, color=MUTED)
a.box("encoder_self", "多头自注意力 · Q/K/V 均来自编码器", 1.08, 3.10, 3.94, .42, BLUE, 11.7)
a.box("encoder_norm1", "残差相加 + LayerNorm", 1.08, 3.59, 3.94, .35, "#EEF5F8", 11)
a.box("encoder_ffn", "逐位置 FFN · 512 → 2048 → 512", 1.08, 4.03, 3.94, .42, BLUE, 11.7)
a.box("encoder_norm2", "残差相加 + LayerNorm", 1.08, 4.54, 3.94, .35, "#EEF5F8", 11)
a.route("src_embed", "encoder_self", (3.00, 2.58), (3.00, 3.07))
a.route("encoder_self", "encoder_norm1", (3.00, 3.52), (3.00, 3.56))
a.route("encoder_norm1", "encoder_ffn", (3.00, 3.94), (3.00, 4.00))
a.route("encoder_ffn", "encoder_norm2", (3.00, 4.45), (3.00, 4.51))
# Residual shortcuts begin before each sublayer, rather than at its output.
a.line(3.00, 3.07, .88, 3.07); a.line(.88, 3.07, .88, 3.76)
a.line(.88, 3.76, 1.05, 3.76, arrow=True)
a.line(3.00, 3.98, .88, 3.98); a.line(.88, 3.98, .88, 4.71)
a.line(.88, 4.71, 1.05, 4.71, arrow=True)
a.text("编码器输出：所有输入位置的上下文表示 z₁ … zₙ", .78, 5.36, 4.62, .44, 11.2,
       color=MUTED, align="left")

a.box("target_shift", "右移目标词元 ⟨bos⟩, y₁ …", 7.15, 1.56, 5.48, .44, TEAL, 12.5)
a.box("tgt_embed", "词嵌入 × √d_model  +  位置编码", 7.15, 2.10, 5.48, .48, TEAL, 12)
a.route("target_shift", "tgt_embed", (9.89, 2.00), (9.89, 2.07))
a.rect(7.05, 2.76, 5.67, 2.43, "#F6FBF9", stroke="#9CC8B8", sw=1)
a.text("重复层 N = 6", 7.22, 2.79, 5.26, .22, 10.5, color=MUTED)
a.box("decoder_masked", "掩码多头自注意力 · 禁看未来位置", 7.57, 3.10, 4.70, .36, TEAL, 11.4)
a.box("decoder_norm1", "残差相加 + LayerNorm", 7.57, 3.50, 4.70, .26, "#EEF7F3", 10.7)
a.box("decoder_cross", "交叉注意力 · Q 来自解码器；K/V 来自编码器", 7.57, 3.80, 4.70, .36, PURPLE, 10.9)
a.box("decoder_norm2", "残差相加 + LayerNorm", 7.57, 4.20, 4.70, .26, "#EEF7F3", 10.7)
a.box("decoder_ffn", "逐位置 FFN · 512 → 2048 → 512", 7.57, 4.50, 4.70, .36, TEAL, 11.4)
a.box("decoder_norm3", "残差相加 + LayerNorm", 7.57, 4.90, 4.70, .26, "#EEF7F3", 10.7)
a.route("tgt_embed", "decoder_masked", (9.91, 2.58), (9.91, 3.07))
for source, target, y1, y2 in [
    ("decoder_masked","decoder_norm1",3.46,3.47),
    ("decoder_norm1","decoder_cross",3.76,3.77),
    ("decoder_cross","decoder_norm2",4.16,4.17),
    ("decoder_norm2","decoder_ffn",4.46,4.47),
    ("decoder_ffn","decoder_norm3",4.86,4.87),
]:
    a.route(source,target,(9.91,y1),(9.91,y2))
a.route("encoder_norm2", "decoder_cross", (5.02,4.72),(6.42,4.72),
        (6.42,3.98),(7.50,3.98))
a.text("K, V", 6.54, 3.73, .77, .22, 10.7, bold=True, color="#705D8B")
for start, end in [(3.07,3.63),(3.78,4.33),(4.48,5.03)]:
    a.line(9.91,start,7.37,start); a.line(7.37,start,7.37,end)
    a.line(7.37,end,7.54,end,arrow=True)
a.box("linear_softmax", "线性投影  →  Softmax", 7.15, 5.56, 3.50, .48, GOLD, 12)
a.box("next_token", "下一个词元概率 / 输出", 10.99, 5.56, 1.64, .48, GOLD, 10.8)
a.route("decoder_norm3", "linear_softmax", (9.91,5.16),(9.91,5.53))
a.route("linear_softmax", "next_token", (10.65,5.80),(10.92,5.80))
a.text("推理时，已生成词元回馈到右移输入；训练时使用右移目标序列。", 7.17, 6.24, 5.45, .35,
       10.4, color=MUTED, align="left")
a.text("原论文为 post-LN；d_model = 512，h = 8，d_ff = 2048。", .78, 6.45, 5.60, .31,
       10.4, color=MUTED, align="left")
a.text("原论文共享两侧词嵌入与 Softmax 前线性层的词表权重。", .78, 6.80, 10.9, .18,
       9.8, color=MUTED, align="left")
a.text("来源：Vaswani et al., Attention Is All You Need, Fig. 1, §§3.1–3.5。", .78, 7.05, 10.9, .18,
       9.5, color=MUTED, align="left")
a.finish()

b = Figure("TR02_transformer_attention",
           "Multi-head attention projects Q/K/V into parallel heads, each using scaled dot-product attention; decoder masking blocks future positions before softmax.",
           "attention")
b.header("Transformer 注意力内部｜多头并行与因果掩码",
         "原始 base model：h = 8，d_k = d_v = 64；编码器自注意力、解码器掩码自注意力与交叉注意力共用此核心", "2 / 2")
b.text("A  多头注意力", .65, 1.25, 5.8, .30, 15, bold=True, align="left")
b.box("qkv", "输入 Q、K、V", .78, 1.72, 5.58, .55, BLUE, 13)
b.box("projections", "各头独立线性投影：Q→Qᵢ，K→Kᵢ，V→Vᵢ", .78, 2.55, 5.58, .59, BLUE, 11.8)
b.rect(.78, 3.45, 5.58, .68, TEAL, sid="heads")
for x, label in [(1.20,"Head 1"),(2.71,"Head 2"),(4.80,"Head 8")]:
    b.rect(x, 3.56, 1.09, .42, "#FFFFFF", stroke="#679D90", sw=.75)
    b.text(label, x+.04, 3.62, 1.01, .28, 11.2, bold=True)
b.text("…", 4.08, 3.60, .44, .28, 15, bold=True)
b.box("concat", "拼接 Concat(head₁, …, head₈)", .78, 4.48, 5.58, .57, TEAL, 12.4)
b.box("output_projection", "输出投影 Wᴼ  →  d_model = 512", .78, 5.39, 5.58, .56, GOLD, 12.4)
for source,target,y1,y2 in [
    ("qkv","projections",2.27,2.52),
    ("projections","heads",3.14,3.42),
    ("heads","concat",4.13,4.45),
    ("concat","output_projection",5.05,5.36),
]:
    b.route(source,target,(3.57,y1),(3.57,y2))
b.text("不同头学习不同表示子空间与位置关系；每头执行右侧的缩放点积。",
       .80, 6.15, 5.56, .49, 10.5, color=MUTED, align="left")

b.line(6.68, 1.28, 6.68, 6.62, color="#B5C5CC", sw=.85)
b.text("B  缩放点积注意力", 7.05, 1.25, 5.8, .30, 15, bold=True, align="left")
b.box("scores", "相似度 QKᵀ / √d_k", 7.18, 1.72, 5.45, .53, PURPLE, 12.7)
b.rect(7.18, 2.57, 5.45, .62, PURPLE, sid="mask")
b.text("解码器自注意力：未来位置加 −∞", 7.30, 2.70, 3.78, .33, 11.1, bold=True)
for row in range(4):
    for col in range(4):
        b.rect(11.29+col*.20, 2.68+row*.11, .18, .10,
               "#547D91" if col <= row else "#FFFFFF",
               stroke="#93A5B7", sw=.45, radius=0)
b.box("softmax", "Softmax → 每行归一化的注意力权重", 7.18, 3.48, 5.45, .53, PURPLE, 11.5)
b.box("values", "V", 7.18, 4.36, .93, .53, BLUE, 13)
b.box("weighted_values", "权重 × V → 上下文表示", 8.57, 4.36, 4.06, .53, GOLD, 12.5)
for source,target,y1,y2 in [
    ("scores","mask",2.25,2.54),
    ("mask","softmax",3.19,3.45),
    ("softmax","weighted_values",4.01,4.33),
]:
    b.route(source,target,(9.90,y1),(9.90,y2))
b.route("values", "weighted_values", (8.11,4.63),(8.50,4.63))
b.text("Attention(Q,K,V) = softmax((QKᵀ / √d_k) + M) V",
       7.20, 5.18, 5.40, .42, 13, bold=True)
b.text("M = 0（无掩码）；被禁止的位置 M = −∞（解码器自注意力）。",
       7.20, 5.68, 5.40, .30, 10.6, color=MUTED)
b.text("交叉注意力：Q 来自解码器；K、V 来自编码器输出。",
       7.20, 6.15, 5.40, .35, 10.8, color=MUTED)

b.line(.65, 6.72, 12.67, 6.72, color="#B5C5CC", sw=.75)
b.text("位置编码：PE(pos,2i)=sin(pos/10000^(2i/d_model))；PE(pos,2i+1)=cos(同项)    ·    FFN(x)=ReLU(xW₁+b₁)W₂+b₂",
       .72, 6.79, 11.87, .25, 9.6, color=MUTED, align="left")
b.finish()

# Combine the two single-slide native PPTX files without flattening any shapes.
from copy import deepcopy  # noqa: E402
deck = Presentation()
deck.slide_width = Inches(13.333); deck.slide_height = Inches(7.5)
for name in ("TR01_transformer_architecture", "TR02_transformer_attention"):
    source = Presentation(str(OUT / f"{name}.pptx"))
    target = deck.slides.add_slide(deck.slide_layouts[6])
    for shape in source.slides[0].shapes:
        target.shapes._spTree.insert_element_before(deepcopy(shape.element), "p:extLst")
deck.save(str(OUT / "Transformer_original_explained.pptx"))
clean_theme(OUT / "Transformer_original_explained.pptx")
print("Built two linked Transformer figures and editable two-slide PPTX")
