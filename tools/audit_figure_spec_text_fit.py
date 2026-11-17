#!/usr/bin/env python3
"""Advisory FigureSpec text-fit and WCAG contrast audit using resolved font metrics."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Any
from text_layout_metrics import FontMetrics, contrast_ratio, fit_textbox_height, resolve_font_face


def _background_for(elements: list[dict], index: int, text: dict) -> str:
    cx = float(text["x"]) + float(text["w"]) / 2
    cy = float(text["y"]) + float(text["h"]) / 2
    for candidate in reversed(elements[:index]):
        if candidate.get("type") != "rect":
            continue
        if (float(candidate.get("x",0)) <= cx <= float(candidate.get("x",0))+float(candidate.get("w",0))
                and float(candidate.get("y",0)) <= cy <= float(candidate.get("y",0))+float(candidate.get("h",0))):
            return candidate.get("fill","#FFFFFF")
    return "#FFFFFF"


def audit_spec(spec: dict[str, Any]) -> dict:
    elements=spec["elements"]
    default_font=spec.get("style",{}).get("font","Times New Roman")
    cache: dict[str,FontMetrics]={}
    results=[]
    try:
        for index,element in enumerate(elements):
            if element.get("type")!="text":
                continue
            family=element.get("font",default_font)
            font_path,face_index,resolved_family=resolve_font_face(family)
            key=f"{font_path}#face={face_index}"
            if key not in cache:
                cache[key]=FontMetrics(font_path,face_index=face_index)
            metrics=cache[key]
            font_size=float(element.get("size",14))
            width_in=float(element["w"])
            height_in=float(element["h"])
            measured=metrics.measure(element["text"],font_size,width_in,height_in)
            margins = (1.44, 1.44, .576, .576)
            line_height = metrics.line_height_pt(font_size)
            # The search ceiling must accommodate the worst case of one glyph per line;
            # a fixed 72 pt ceiling silently loses the recommendation for narrow, long labels.
            search_ceiling = max(
                72.0,
                height_in * 72.0 * 4.0,
                (len(str(element["text"])) + 1) * line_height + margins[2] + margins[3],
            )
            height_search=fit_textbox_height(
                metrics,element["text"],font_size,width_in,
                min_height_pt=1.0,max_height_pt=search_ceiling,margins_pt=margins
            )
            background=_background_for(elements,index,element)
            foreground=element.get("color","#28343C")
            ratio=contrast_ratio(foreground,background)
            is_large=float(element.get("size",14)) >= (14 if element.get("bold") else 18)
            threshold=3.0 if is_large else 4.5
            results.append({
                "element_id":element.get("id",f"element_{index+1:04d}"),
                "text":element["text"],
                "font_family_requested":family,
                "font_family_resolved":resolved_family or metrics.family_name,
                "font_face_index":face_index,
                "font_file":str(font_path),
                "font_fallbacks":dict(metrics.fallback_fonts),
                "font_size_pt":float(element.get("size",14)),
                "line_count":measured["line_count"],
                "required_height_pt":round(measured["required_height_pt"],3),
                "available_height_pt":round(measured["available_height_pt"],3),
                "fits_estimate":measured["fits"],
                "binary_search_minimum_height_pt":round(height_search["height_pt"],3) if height_search["fits"] else None,
                "additional_height_needed_pt":(
                    0.0 if measured["fits"] else
                    round(max(0.0,(height_search["height_pt"] or 0.0)-height_in*72.0),3)
                ) if height_search["fits"] else None,
                "height_search_reason":height_search["reason"],
                "foreground":foreground,
                "background_estimate":background,
                "contrast_ratio":round(ratio,3),
                "contrast_threshold":threshold,
                "contrast_pass":ratio>=threshold,
            })
    finally:
        for metrics in cache.values():
            metrics.close()
    overflow=[item for item in results if not item["fits_estimate"]]
    contrast_fail=[item for item in results if not item["contrast_pass"]]
    return {
        "schema_version":"1.0.0",
        "figure_id":spec.get("id","unnamed"),
        "font_metric_engine":"fontTools cmap/hmtx + OS/2/hhea",
        "text_elements":len(results),
        "estimated_overflow_count":len(overflow),
        "contrast_fail_count":len(contrast_fail),
        "status":"REVISE" if overflow or contrast_fail else "PASS_ESTIMATE",
        "limitations":[
            "Fast metric estimate only; not a substitute for shaped-text rendering.",
            "Font fallback, kerning, ligatures and renderer-specific line breaking require calibration with the pinned LibreOffice profile.",
            "Background resolution uses the last preceding containing rectangle and is approximate for overlapping, transparent or gradient objects.",
            "This audit does not modify or silently shrink authored font sizes."
        ],
        "elements":results,
    }


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("figure_spec",type=Path)
    parser.add_argument("--output",type=Path)
    parser.add_argument("--strict",action="store_true")
    args=parser.parse_args()
    report=audit_spec(json.loads(args.figure_spec.read_text(encoding="utf-8")))
    serialized=json.dumps(report,ensure_ascii=False,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(serialized,encoding="utf-8")
    print(serialized)
    if args.strict and report["status"]!="PASS_ESTIMATE":
        raise SystemExit(1)


if __name__=="__main__":
    main()
