#!/usr/bin/env python3
"""Gate FigureAST writer migration on native-object and rendered-image parity."""
from __future__ import annotations
import argparse, json
from collections import Counter
from pathlib import Path
from pptx import Presentation
from compare_rendered_images import compare


def inspect_pptx(path: Path) -> dict:
    deck=Presentation(path)
    slides=[]
    for slide in deck.slides:
        shapes=list(slide.shapes)
        slides.append({
            "shape_count":len(shapes),
            "shape_types":dict(Counter(str(shape.shape_type) for shape in shapes)),
            "texts":[shape.text for shape in shapes if getattr(shape,"has_text_frame",False) and shape.text.strip()],
            "pictures":sum(str(shape.shape_type)=="13" for shape in shapes),
            "bounds":[[shape.left,shape.top,shape.width,shape.height] for shape in shapes],
            "within_canvas":all(shape.left>=0 and shape.top>=0 and shape.left+shape.width<=deck.slide_width and shape.top+shape.height<=deck.slide_height for shape in shapes),
        })
    return {"slide_count":len(deck.slides),"slides":slides}


def validate(legacy_pptx: Path, ast_pptx: Path, legacy_png: Path, ast_png: Path,
             diff_png: Path, max_mae: float=1.0, max_changed_ratio: float=.005) -> dict:
    legacy=inspect_pptx(legacy_pptx)
    ast=inspect_pptx(ast_pptx)
    issues=[]
    if legacy["slide_count"]!=ast["slide_count"]:
        issues.append("SLIDE_COUNT_MISMATCH")
    for index,(left,right) in enumerate(zip(legacy["slides"],ast["slides"])):
        if left["shape_count"]!=right["shape_count"]:
            issues.append(f"SHAPE_COUNT_MISMATCH:{index+1}")
        if left["shape_types"]!=right["shape_types"]:
            issues.append(f"SHAPE_TYPE_INVENTORY_MISMATCH:{index+1}")
        if left["texts"]!=right["texts"]:
            issues.append(f"TEXT_SEQUENCE_MISMATCH:{index+1}")
        if left["bounds"]!=right["bounds"]:
            issues.append(f"GEOMETRY_MISMATCH:{index+1}")
        if not right["within_canvas"]:
            issues.append(f"AST_OBJECT_OUT_OF_BOUNDS:{index+1}")
    raster=compare(legacy_png,ast_png,diff_png)
    if raster["mean_absolute_error"]>max_mae:
        issues.append(f"RASTER_MAE_EXCEEDED:{raster['mean_absolute_error']:.6f}>{max_mae}")
    if raster["changed_pixel_ratio"]>max_changed_ratio:
        issues.append(f"RASTER_CHANGED_RATIO_EXCEEDED:{raster['changed_pixel_ratio']:.6f}>{max_changed_ratio}")
    return {
        "status":"PASS" if not issues else "FAIL",
        "legacy":legacy,"ast":ast,"raster":raster,
        "thresholds":{"max_mean_absolute_error":max_mae,"max_changed_pixel_ratio":max_changed_ratio},
        "issues":issues,
    }


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-pptx",type=Path,required=True)
    parser.add_argument("--ast-pptx",type=Path,required=True)
    parser.add_argument("--legacy-png",type=Path,required=True)
    parser.add_argument("--ast-png",type=Path,required=True)
    parser.add_argument("--diff",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--max-mae",type=float,default=1.0)
    parser.add_argument("--max-changed-ratio",type=float,default=.005)
    args=parser.parse_args()
    report=validate(args.legacy_pptx,args.ast_pptx,args.legacy_png,args.ast_png,args.diff,args.max_mae,args.max_changed_ratio)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"issues":report["issues"],"raster":report["raster"],"legacy_shapes":report["legacy"]["slides"][0]["shape_count"],"ast_shapes":report["ast"]["slides"][0]["shape_count"]},indent=2))
    if report["status"]!="PASS":
        raise SystemExit(1)


if __name__=="__main__":
    main()
