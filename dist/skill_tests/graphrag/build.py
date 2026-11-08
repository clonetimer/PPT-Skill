#!/usr/bin/env python3
"""Build a source-grounded, editable Microsoft GraphRAG overview slide."""
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

FIGURE_ID = "GR01_graphrag_flow"
CONTRACTS[FIGURE_ID] = {
    "claim": "Microsoft GraphRAG indexes documents into graph and community artifacts, then answers via alternative global or local query paths.",
    "archetype": "schematic_led_composite",
    "output_mode": "presentation",
    "unverified": ["Exact implementation sequence and optional configuration stages are not represented."],
    "source": "dist/skill_tests/graphrag/SOURCE.md",
    "source_locator": "Four official documentation links and the scope statement in SOURCE.md",
    "evidence_status": "domain_adaptation",
    "evidence_scope": "Conceptual reconstruction of standard indexing, global search, and local search paths.",
    "reuse": "documentation-grounded schematic",
}

E: list[dict] = []
EDGES: list[tuple[str, str]] = []
INK = "#243447"
BLUE = "#DDEBFA"
GREEN = "#DFF2E8"
WARM = "#FFF1D7"
RULE = "#9CB0C1"


def txt(value: str, x: float, y: float, w: float, h: float, size: float = 14,
        *, bold: bool = False, color: str = INK, align: str = "center") -> None:
    E.append({"type": "text", "text": value, "x": x, "y": y, "w": w, "h": h,
              "size": size, "bold": bold, "color": color, "align": align})


def box(key: str, label: str, x: float, y: float, w: float, h: float,
        fill: str, size: float = 15) -> None:
    E.append({"type": "rect", "semantic_id": key, "x": x, "y": y, "w": w,
              "h": h, "fill": fill, "stroke": "#547087", "sw": 1.1, "radius": .08})
    txt(label, x + .05, y + .06, w - .1, h - .12, size, bold=True)


def line(x1: float, y1: float, x2: float, y2: float, *, arrow: bool = False,
         link: str | None = None, dash: bool = False, color: str = "#51667B") -> None:
    e = {"type": "line", "x1": x1, "y1": y1, "x2": x2, "y2": y2,
         "color": color, "sw": 1.6, "arrow": arrow}
    if link:
        e["semantic_link"] = link
    if dash:
        e["dash"] = True
    E.append(e)


def edge(a: str, b: str, segments: list[tuple[float, float, float, float]]) -> None:
    EDGES.append((a, b))
    for i, (x1, y1, x2, y2) in enumerate(segments):
        line(x1, y1, x2, y2, arrow=i == len(segments) - 1, link=f"{a}__{b}")


txt("GraphRAG：从文档到回答", .55, .25, 11.9, .52, 25, bold=True, align="left")
txt("Microsoft GraphRAG 标准路径 · 概念性重构", .55, .79, 11.9, .29, 12.5,
    color="#63778A", align="left")
line(.55, 1.18, 12.78, 1.18, color=RULE)

txt("01  离线索引", .58, 1.35, 2.5, .35, 17, bold=True, align="left")
top = [
    ("docs", "文档", .60, 1.89, 1.47),
    ("units", "文本块\nText units", 2.33, 1.89, 1.55),
    ("extract", "实体与关系\n抽取 / 摘要", 4.15, 1.89, 1.77),
    ("graph", "知识图谱", 6.19, 1.89, 1.46),
    ("community", "社区发现", 7.92, 1.89, 1.51),
    ("reports", "社区报告", 9.70, 1.89, 2.48),
]
for key, label, x, y, w in top:
    box(key, label, x, y, w, .84, BLUE, 14.5)
for left, right in zip(top, top[1:]):
    a, _, x, y, w = left
    b, _, nx, _, _ = right
    edge(a, b, [(x + w, y + .42, nx - .07, y + .42)])
txt("索引产物：图谱 · 社区报告 · 向量嵌入（文本块、实体描述、社区报告）",
    .70, 2.97, 11.8, .38, 13.6, color="#3F5870", align="left")
line(.55, 3.56, 12.78, 3.56, color=RULE)

txt("02  在线查询", .58, 3.73, 2.5, .35, 17, bold=True, align="left")
txt("两种可选的检索模式", 3.18, 3.75, 5.5, .31, 12.5,
    color="#63778A", align="left")
box("question", "用户问题", .72, 4.96, 1.78, .84, GREEN, 15)

box("global", "全局检索\n社区报告", 3.35, 4.35, 2.10, .86, GREEN, 14.5)
box("map", "Map–Reduce\n归纳", 6.20, 4.35, 2.10, .86, GREEN, 14.5)
box("ganswer", "全局回答\n跨主题总结", 9.05, 4.35, 2.63, .86, WARM, 14.5)
edge("question", "global", [(2.50, 5.38, 2.85, 5.38),
                             (2.85, 5.38, 2.85, 4.78),
                             (2.85, 4.78, 3.28, 4.78)])
edge("global", "map", [(5.45, 4.78, 6.13, 4.78)])
edge("map", "ganswer", [(8.30, 4.78, 8.98, 4.78)])

box("local", "局部检索\n实体匹配", 3.35, 5.72, 2.10, .86, GREEN, 14.5)
box("context", "图邻域 + 原文块", 6.20, 5.72, 2.10, .86, GREEN, 14.5)
box("lanswer", "局部回答\n实体相关细节", 9.05, 5.72, 2.63, .86, WARM, 14.5)
edge("question", "local", [(2.50, 5.38, 2.85, 5.38),
                            (2.85, 5.38, 2.85, 6.15),
                            (2.85, 6.15, 3.28, 6.15)])
edge("local", "context", [(5.45, 6.15, 6.13, 6.15)])
edge("context", "lanswer", [(8.30, 6.15, 8.98, 6.15)])

txt("全局检索使用社区报告；局部检索结合实体、图关系与原始文本块。两条路径表示选择，而非同时执行。",
    .70, 6.82, 12.0, .31, 10.5, color="#586D7F", align="left")

spec = enrich_spec({"id": FIGURE_ID, "title": "GraphRAG：从文档到回答",
                    "canvas": {"width_in": 13.333, "height_in": 7.5},
                    "style": {"font": "Microsoft YaHei"},
                    "semantic_edges": [list(e) for e in EDGES], "elements": E})
jsonschema.validate(spec, json.loads((ROOT / "specs/figure_spec_v76.schema.json").read_text(encoding="utf-8")))
validate_spec(spec)
validate_drawn_routes(spec, set(EDGES))
(OUT / f"{FIGURE_ID}.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
render(spec, OUT / f"{FIGURE_ID}.svg", OUT / f"{FIGURE_ID}.pptx")
print(f"Built {FIGURE_ID}: {len(E)} elements, {len(EDGES)} checked relations")
