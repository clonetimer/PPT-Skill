"""Compile *human-accepted* source geometry into provenance-locked constraints.

This does not create scientific nodes, semantics, equation meaning or directed
edges. The result can guide FigureSpec drafting only as geometric evidence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from source_layout_review import validate_source_layout_review


def _normalized_bbox(box, region):
    x0,y0,x1,y1=(float(x) for x in box)
    rx0,ry0,rx1,ry1=(float(x) for x in region)
    if (rx1<=rx0 or ry1<=ry0 or x0<rx0 or y0<ry0 or x1>rx1 or y1>ry1
        or x1<=x0 or y1<=y0):
        raise ValueError("REVIEWED_REGION_OUTSIDE_SOURCE_CROP")
    return [
        round((x0-rx0)/(rx1-rx0),6),
        round((y0-ry0)/(ry1-ry0),6),
        round((x1-x0)/(rx1-rx0),6),
        round((y1-y0)/(ry1-ry0),6),
    ]


def _constraint(item, *, panel, figure_region):
    typ=item.get("candidate_type")
    common = {
        "id": item["candidate_id"],
        "source_candidate_id": item.get("derived_from_candidate",item["candidate_id"]),
        "source_type": typ,
        "confidence": item.get("confidence"),
        "rationale": item["rationale"],
        "evidence_locator": item["evidence_locator"],
        "reviewer": item["reviewer"],
        "scientific_relations_verified": False,
        "semantic_edges": [],
        "use": "source_geometry_hint_only",
    }
    if typ == "raster_gutter":
        return {
            **common,
            "constraint_type": "separator_hint",
            "axis": item["axis"],
            "start_pt": item["start_pt"],
            "end_pt": item["end_pt"],
            "source_image_id": item["source_image_id"],
            "bbox_pt": None,
            "bbox_normalized": None,
        }
    bbox = item.get("bbox_pt")
    if not isinstance(bbox,(list,tuple)) or len(bbox)!=4:
        raise ValueError("REVIEWED_GEOMETRY_MISSING_BBOX")
    return {
        **common,
        "constraint_type": "panel_boundary" if panel else "region_bounds",
        "bbox_pt": [float(x) for x in bbox],
        "bbox_normalized": _normalized_bbox(bbox, figure_region),
        "review_state": item.get("review_state", "human_accepted_geometry_not_science"),
    }


def compile_reviewed_layout_constraints(
    layout_path: Path, review_path: Path, output_path: Path
) -> dict:
    """Only emit geometry after an all-or-nothing review validation.

    Stale output is deleted *before* review verification. This prevents a
    corrupted newer review leaving a trusted-looking prior constraints file.
    """
    layout_path,review_path,output_path=map(Path,(layout_path,review_path,output_path))
    if output_path.exists():
        output_path.unlink()
    audit=validate_source_layout_review(layout_path,review_path)
    if audit["status"]=="INVALID":
        raise ValueError("INVALID_SOURCE_LAYOUT_REVIEW: "+"; ".join(audit["errors"]))
    if audit["status"]!="VALIDATED_WITH_ACCEPTED_FACTS":
        raise ValueError("REVIEWED_SOURCE_FACTS_REQUIRED")
    layout=json.loads(layout_path.read_text(encoding="utf-8"))
    region=layout["figure_region_pt"]
    reviewed_panels=audit["accepted_source_panels"]
    reviewed_regions=audit["accepted_source_layout_regions"]
    constraints=[
        *(_constraint(item,panel=True,figure_region=region) for item in reviewed_panels),
        *(_constraint(item,panel=False,figure_region=region) for item in reviewed_regions),
    ]
    constraints.sort(key=lambda x:x["id"])
    result={
        "schema_version":"1.0.0",
        "status":"REVIEWED_GEOMETRIC_CONSTRAINTS",
        "source":{
            "filename":layout["source"]["filename"],
            "sha256":layout["source"]["sha256"],
            "page_index":layout["source"]["page_index"],
            "figure_region_pt":region,
        },
        "source_layout_sha256":audit["source_layout_sha256"],
        "review_file_sha256":audit["review_file_sha256"],
        "source_panel_constraint_count":len(reviewed_panels),
        "region_constraint_count":len(reviewed_regions),
        "constraint_count":len(constraints),
        "semantic_edge_authorization":"none",
        "constraints":constraints,
        "review_scope":"Geometric/source-style evidence only; scientific topology and final acceptance require separate review.",
    }
    output_path.parent.mkdir(parents=True,exist_ok=True)
    output_path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_layout",type=Path)
    parser.add_argument("human_review",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=compile_reviewed_layout_constraints(args.source_layout,args.human_review,args.output)
    print(json.dumps({
        "status":result["status"],"constraints":result["constraint_count"],
        "source_panels":result["source_panel_constraint_count"],
        "source_regions":result["region_constraint_count"],
        "output":str(args.output)
    },ensure_ascii=False))


if __name__=="__main__":
    main()
