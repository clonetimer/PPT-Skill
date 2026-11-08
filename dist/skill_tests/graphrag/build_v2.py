#!/usr/bin/env python3
"""GraphRAG method figure: native editable shapes and independent topology check."""
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

ID = "GR02_graphrag_method"
TOPOLOGY = json.loads((OUT / "GR02_expected_topology.json").read_text(encoding="utf-8"))
REQUIRED = {tuple(pair) for pair in TOPOLOGY["critical_edges"]}
CONTRACTS[ID] = {
    "claim": TOPOLOGY["claim"], "archetype": "schematic_led_composite",
    "output_mode": "presentation", "unverified": TOPOLOGY["excluded"],
    "source": "dist/skill_tests/graphrag/SOURCE.md",
    "source_locator": "Original paper Figure 1 and Section 3.1; official indexing/global-search pages",
    "evidence_status": "paper_grounded",
    "evidence_scope": "Paper-grounded reconstruction of the global GraphRAG method; schematic graph and community examples are illustrative, not extracted research data.",
    "reuse": "Original diagram was analyzed but not copied; this figure is a new editable schematic.",
}

E: list[dict] = []
ROUTES: list[tuple[str, str]] = []
INK = "#203343"
MUTED = "#536B7A"
BLUE = "#E8F1F5"
TEAL = "#DDF1EB"
GOLD = "#F8EDD4"
LINE = "#47677A"


def text(s, x, y, w, h, size=12, *, bold=False, color=INK, align="center"):
    E.append(dict(type="text", text=s, x=x, y=y, w=w, h=h, size=size,
                  bold=bold, color=color, align=align))


def rect(x, y, w, h, *, fill="#FFFFFF", stroke="#A8BEC9", sw=1,
         radius=0, semantic_id=None):
    e = dict(type="rect", x=x, y=y, w=w, h=h, fill=fill, stroke=stroke,
             sw=sw, radius=radius)
    if semantic_id:
        e["semantic_id"] = semantic_id
    E.append(e)


def ellipse(x, y, w, h, *, fill=TEAL, stroke=LINE, sw=1):
    E.append(dict(type="ellipse", x=x, y=y, w=w, h=h, fill=fill, stroke=stroke, sw=sw))


def line(x1, y1, x2, y2, *, color=LINE, sw=1.25, arrow=False, link=None, dash=False):
    e = dict(type="line", x1=x1, y1=y1, x2=x2, y2=y2,
             color=color, sw=sw, arrow=arrow)
    if link:
        e["semantic_link"] = link
    if dash:
        e["dash"] = True
    E.append(e)


def route(a, b, points):
    ROUTES.append((a, b))
    for i, (p, q) in enumerate(zip(points, points[1:])):
        line(*p, *q, link=f"{a}__{b}", arrow=i == len(points)-2, sw=1.55)


def stage(key, x, w, title, subtitle, fill=BLUE):
    rect(x, 1.46, w, 1.60, fill=fill, stroke="#B7CBD2", radius=.06,
         semantic_id=key)
    text(title, x+.07, 2.59, w-.14, .28, 13.8, bold=True)
    text(subtitle, x+.07, 2.87, w-.14, .17, 9.3, color=MUTED)


text("GraphRAG｜层级社区如何支持全局问题回答", .55, .20, 12.15, .46,
     22, bold=True, align="left")
text("索引阶段构建图与社区摘要；查询阶段对多个社区分别作答并汇总。",
     .55, .69, 12.15, .28, 11.3, color=MUTED, align="left")
line(.55, 1.13, 12.78, 1.13, color="#A7BCC7", sw=1)
text("A  离线索引", .58, 1.18, 2.4, .26, 12, bold=True, align="left")

stage("documents", .55, 1.80, "源文档", "原始语料")
stage("text_units", 2.92, 1.80, "文本块", "切分 / 保留来源")
stage("entity_graph", 5.29, 1.80, "实体关系图", "LLM 抽取与摘要")
stage("communities", 7.66, 1.80, "层级社区", "图社区检测")
stage("community_reports", 10.03, 2.75, "社区报告", "逐社区生成摘要")
for a, b, x1, x2 in [
    ("documents", "text_units", 2.35, 2.85),
    ("text_units", "entity_graph", 4.72, 5.22),
    ("entity_graph", "communities", 7.09, 7.59),
    ("communities", "community_reports", 9.46, 9.96),
]:
    route(a, b, [(x1, 2.12), (x2, 2.12)])

# The small native-vector depictions encode data structures, not decoration.
for ox, oy in [(0, .10), (.10, .04), (.20, -.02)]:
    rect(.94+ox, 1.73+oy, .72, .63, fill="#FFFFFF", stroke="#6E8B9A", sw=.7)
    for j in range(3):
        line(1.04+ox, 1.85+oy+j*.10, 1.50+ox, 1.85+oy+j*.10,
             color="#91A8B3", sw=.65)
for i in range(3):
    rect(3.31, 1.75+i*.20, 1.02, .14, fill="#FFFFFF", stroke="#6E8B9A", sw=.7)
nodes = [(5.69, 1.80), (6.14, 1.70), (6.57, 1.89), (5.88, 2.20), (6.46, 2.32)]
for i, j in [(0,1),(1,2),(0,3),(1,3),(2,4),(3,4)]:
    line(nodes[i][0]+.07, nodes[i][1]+.07, nodes[j][0]+.07, nodes[j][1]+.07,
         color="#638D92", sw=1)
for x, y in nodes:
    ellipse(x, y, .14, .14, fill="#4E9A8B", stroke="#2D7066", sw=.5)
# One parent community contains two smaller clusters.
rect(8.03, 1.68, 1.02, .80, fill="#FFFFFF", stroke="#729C93", sw=.8, radius=.16)
rect(8.12, 1.77, .36, .56, fill="#ECF8F4", stroke="#85ACA3", sw=.7, radius=.13)
rect(8.57, 1.77, .36, .56, fill="#ECF8F4", stroke="#85ACA3", sw=.7, radius=.13)
for x, y in [(8.20,1.91),(8.28,2.08),(8.65,1.92),(8.73,2.08)]:
    ellipse(x,y,.09,.09,fill="#4E9A8B",stroke="#2D7066",sw=.4)
for ox, oy in [(.00,.09),(.12,.04),(.24,-.01)]:
    rect(10.65+ox, 1.75+oy, 1.15, .60, fill="#FFFFFF", stroke="#7899A4", sw=.7)
    for j in range(3):
        line(10.78+ox, 1.90+oy+j*.10, 11.60+ox, 1.90+oy+j*.10,
             color="#91A8B3", sw=.6)

# The cross-stage route is required by a source-derived fixture, not inferred from drawing.
route("community_reports", "query_reports", [
    (11.37, 3.06), (11.37, 3.39), (3.90, 3.39), (3.90, 4.49)])
text("索引产物供查询复用", 6.30, 3.42, 2.50, .20, 9.6, color=MUTED)
text("B  在线全局查询", .58, 3.81, 3.2, .30, 12, bold=True, align="left")

rect(.55, 4.55, 1.56, 1.12, fill=TEAL, stroke="#88B6AA", radius=.06,
     semantic_id="question")
text("用户问题", .64, 4.91, 1.38, .34, 13.5, bold=True)
rect(2.75, 4.49, 2.30, 1.24, fill=TEAL, stroke="#88B6AA", radius=.06,
     semantic_id="query_reports")
text("社区报告 1 … N", 2.85, 5.22, 2.10, .30, 13.2, bold=True)
for i in range(3):
    rect(3.18+i*.35, 4.70, .34, .37, fill="#FFFFFF", stroke="#5A988A", sw=.75)
route("question", "query_reports", [(2.11, 5.11), (2.68, 5.11)])

rect(5.65, 4.49, 2.42, 1.24, fill=TEAL, stroke="#88B6AA", radius=.06,
     semantic_id="partial_answers")
text("并行的分社区回答", 5.74, 5.22, 2.24, .30, 13.2, bold=True)
for i in range(3):
    rect(6.08+i*.37, 4.70, .32, .37, fill="#FFFFFF", stroke="#5A988A", sw=.75)
route("query_reports", "partial_answers", [(5.05, 5.11), (5.58, 5.11)])

rect(8.67, 4.55, 1.35, 1.12, fill=TEAL, stroke="#88B6AA", radius=.06,
     semantic_id="reduce")
text("归并", 8.76, 4.88, 1.16, .33, 13.5, bold=True)
text("Reduce", 8.76, 5.23, 1.16, .23, 10.3, color=MUTED)
route("partial_answers", "reduce", [(8.07, 5.11), (8.60, 5.11)])

rect(10.63, 4.55, 2.15, 1.12, fill=GOLD, stroke="#BD9C5E", radius=.06,
     semantic_id="global_answer")
text("全局回答", 10.75, 4.92, 1.91, .37, 15, bold=True)
route("reduce", "global_answer", [(10.02, 5.11), (10.56, 5.11)])

line(.55, 6.03, 12.78, 6.03, color="#A7BCC7", sw=.85)
text("图中节点与社区为示意；核心关系依据 Edge 等的 Figure 1 与方法章节。局部检索属于另一查询模式，此图聚焦全局回答。",
     .58, 6.20, 12.08, .48, 10.1, color=MUTED, align="left")
text("来源：Edge et al., From Local to Global (2025), Fig. 1；Microsoft GraphRAG 官方文档。",
     .58, 6.75, 12.08, .28, 9.5, color=MUTED, align="left")

assert set(ROUTES) == REQUIRED, ("declared versus source-required routes", set(ROUTES) ^ REQUIRED)
spec = enrich_spec({"id": ID, "title": "GraphRAG global-answer method figure",
                    "canvas": {"width_in": 13.333, "height_in": 7.5},
                    "style": {"font": "Microsoft YaHei"},
                    "semantic_edges": [list(pair) for pair in ROUTES],
                    "elements": E})
jsonschema.validate(spec, json.loads((ROOT / "specs/figure_spec_v76.schema.json").read_text(encoding="utf-8")))
validate_spec(spec)
validate_drawn_routes(spec, REQUIRED)
(OUT / f"{ID}.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
render(spec, OUT / f"{ID}.svg", OUT / f"{ID}.pptx")
print(f"Built {ID}: {len(E)} elements; {len(REQUIRED)} independent required routes")
