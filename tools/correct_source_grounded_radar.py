#!/usr/bin/env python3
"""Create an explicit, non-destructive table-corrected radar alternative."""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
import math
from pathlib import Path

from pptx import Presentation

from audit_source_grounded_radar import (
    audit_radar, DEFAULT_SERIES, read_source_table, source_axis,
    shape_stroke, shape_vertices,
)


def _rewrite_freeform(shape, absolute_points):
    minx = min(x for x,y in absolute_points)
    miny = min(y for x,y in absolute_points)
    maxx = max(x for x,y in absolute_points)
    maxy = max(y for x,y in absolute_points)
    xfrm = shape._element.spPr.xfrm
    xfrm.off.x = round(minx*914400)
    xfrm.off.y = round(miny*914400)
    xfrm.ext.cx = round((maxx-minx)*914400)
    xfrm.ext.cy = round((maxy-miny)*914400)
    path = shape._element.xpath(".//a:custGeom/a:pathLst/a:path")[0]
    path.set("w", str(max(1,round((maxx-minx)*10000))))
    path.set("h", str(max(1,round((maxy-miny)*10000))))
    points = path.xpath("./a:moveTo/a:pt|./a:lnTo/a:pt")
    assert len(points) == len(absolute_points)
    for item,(x,y) in zip(points,absolute_points):
        item.set("x",str(round((x-minx)*10000)))
        item.set("y",str(round((y-miny)*10000)))


def corrected_candidate(source_pptx: Path, table: Path, manifest: Path,
                        output: Path, *, threshold: float = .003) -> dict:
    if output.resolve() == source_pptx.resolve():
        raise ValueError("Never overwrite source-faithful candidate")
    source_values = read_source_table(table)
    manifest_values = json.loads(Path(manifest).read_text(encoding="utf-8"))
    original_audit = audit_radar(source_pptx, table, manifest, tolerance=threshold)
    deck = Presentation(source_pptx)
    slide = deck.slides[0]
    changes = []
    for panel in manifest_values["radars"]:
        xmin,ymin,xmax,ymax = panel["bbox_inches"]
        axes = [source_axis(axis,source_values) for axis in panel["axes"]]
        colors = defaultdict(list)
        for shape in slide.shapes:
            verts = shape_vertices(shape)
            color = shape_stroke(shape)
            if not verts or color not in {c for _,c in DEFAULT_SERIES}:
                continue
            x,y,w,h = (z/914400 for z in (shape.left,shape.top,shape.width,shape.height))
            if xmin<=x and ymin<=y and x+w<=xmax and y+h<=ymax:
                colors[color].append((shape,verts))
        if not colors.get("EA4335"):
            raise ValueError("Missing red reference")
        red = colors["EA4335"][0][1][:9]
        cx = sum(p[0] for p in red)/9
        cy = sum(p[1] for p in red)/9
        for series,color in DEFAULT_SERIES[:-1]:
            for shape,original in colors[color]:
                revised = original[:]
                for j,axis in enumerate(axes):
                    radius = math.dist((cx,cy), red[j])
                    measured = math.dist((cx,cy), original[j])/radius
                    expected = axis[series]/axis["mmgraph_agent"]
                    if abs(measured-expected) <= threshold:
                        continue
                    ux = (red[j][0]-cx)/radius
                    uy = (red[j][1]-cy)/radius
                    corrected=(cx+ux*radius*expected,cy+uy*radius*expected)
                    changes.append({
                        "panel":panel["name"],"series":series,"axis_index":j,
                        "dataset":panel["axes"][j],"shape":shape.name,
                        "before_ratio":round(measured,7),
                        "source_table_ratio":round(expected,7),
                        "point_shift_inches":round(math.dist(revised[j],corrected),7),
                    })
                    revised[j]=corrected
                if revised!=original:
                    revised[-1]=revised[0]
                    _rewrite_freeform(shape,revised)
    if not changes:
        raise ValueError("No data correction required")
    output.parent.mkdir(parents=True,exist_ok=True)
    deck.save(output)
    final_audit=audit_radar(output,table,manifest,tolerance=threshold)
    if final_audit["status"]!="PASS":
        raise RuntimeError("Data-corrected file did not pass source audit")
    return {
        "source_candidate":str(source_pptx),
        "corrected_candidate":str(output),
        "input_status":original_audit["status"],
        "output_status":final_audit["status"],
        "correction_count":len(changes),
        "corrections":changes,
        "input_preserved":True,
        "note":"Research-table-corrected alternative; not an exact publisher-artwork claim.",
        "numeric_source":manifest_values.get("source")
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx",type=Path)
    parser.add_argument("--table",type=Path,required=True)
    parser.add_argument("--manifest",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--report",type=Path,required=True)
    parser.add_argument("--apply-data-corrections",action="store_true")
    args=parser.parse_args()
    if not args.apply_data_corrections:
        parser.error("Explicit --apply-data-corrections required")
    result=corrected_candidate(args.pptx,args.table,args.manifest,args.output)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"status":result["output_status"],"changes":result["correction_count"]}))
    if result["output_status"]!="PASS":
        raise SystemExit(1)


if __name__=="__main__":
    main()
