#!/usr/bin/env python3
"""Preflight: find line segments that run through figure text or circular nodes."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def point_inside(e: dict, x: float, y: float) -> bool:
    if e["type"] == "text":
        if e.get("rotation"):
            cx=e["x"]+e["w"]/2;cy=e["y"]+e["h"]/2
            angle=math.radians(e["rotation"])
            dx=x-cx;dy=y-cy
            x=cx+dx*math.cos(angle)+dy*math.sin(angle)
            y=cy-dx*math.sin(angle)+dy*math.cos(angle)
        pad = min(.025, e["w"] / 10, e["h"] / 10)
        return e["x"] + pad < x < e["x"] + e["w"] - pad and e["y"] + pad < y < e["y"] + e["h"] - pad
    if e["type"] == "ellipse":
        cx,cy=e["x"]+e["w"]/2,e["y"]+e["h"]/2
        rx,ry=e["w"]/2,e["h"]/2
        return ((x-cx)/rx)**2+((y-cy)/ry)**2 < .72
    return False


def audit(spec: dict) -> list[dict]:
    marks=[e for e in spec["elements"] if e["type"]=="ellipse" or (e["type"]=="text" and e.get("text","").strip())]
    ellipses=[e for e in marks if e["type"]=="ellipse"]
    # A node label's rectangular text box reaches the circular boundary; the
    # ellipse check is the meaningful occlusion test for these contained labels.
    def is_node_label(mark: dict) -> bool:
        if mark["type"]!="text":return False
        return any(mark["x"]>=o["x"] and mark["y"]>=o["y"] and
                   mark["x"]+mark["w"]<=o["x"]+o["w"] and
                   mark["y"]+mark["h"]<=o["y"]+o["h"] for o in ellipses)
    marks=[e for e in marks if not is_node_label(e)]
    problems=[]
    for i,line in enumerate(spec["elements"]):
        if line["type"] != "line":
            continue
        for mark in marks:
            if any(point_inside(mark,line["x1"]+(line["x2"]-line["x1"])*j/40,
                                line["y1"]+(line["y2"]-line["y1"])*j/40) for j in range(1,40)):
                problems.append({"line_index":i,"line_link":line.get("semantic_link"),
                                 "occluded_type":mark["type"],"occluded_id":mark.get("semantic_id"),
                                 "occluded_text":mark.get("text","")[:32]})
    return problems


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("spec",type=Path)
    args=p.parse_args()
    problems=audit(json.loads(args.spec.read_text(encoding="utf-8")))
    print(json.dumps({"spec":args.spec.name,"line_occlusions":problems},ensure_ascii=False,indent=2))
    if problems:raise SystemExit(1)


if __name__ == "__main__":main()
