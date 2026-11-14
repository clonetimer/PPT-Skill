#!/usr/bin/env python3
"""Apply explicitly bound, human-reviewed SourceLayout geometry to FigureSpec.

Only x/y/w/h geometry changes, never scientific text, edge direction, labels
or model structure. A new FigureSpec is always created; originals remain intact.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def apply_reviewed_geometry(
    figure_spec: Path,
    constraints_file: Path,
    bindings_file: Path,
    output_file: Path,
) -> dict:
    figure_spec,constraints_file,bindings_file,output_file=map(
        Path,(figure_spec,constraints_file,bindings_file,output_file)
    )
    if output_file.resolve()==figure_spec.resolve():
        raise ValueError("REFUSE_TO_OVERWRITE_SOURCE")
    if output_file.exists():
        output_file.unlink()

    spec=json.loads(figure_spec.read_text(encoding="utf-8"))
    constraints=json.loads(constraints_file.read_text(encoding="utf-8"))
    binding=json.loads(bindings_file.read_text(encoding="utf-8"))
    if binding.get("schema_version")!="1.0.0":
        raise ValueError("UNSUPPORTED_GEOMETRY_BINDING_SCHEMA")
    if binding.get("figure_spec_sha256") != sha256(figure_spec):
        raise ValueError("FIGURESPEC_HASH_MISMATCH")
    if binding.get("source_constraints_sha256") != sha256(constraints_file):
        raise ValueError("REVIEWED_CONSTRAINTS_HASH_MISMATCH")
    if constraints.get("status")!="REVIEWED_GEOMETRIC_CONSTRAINTS":
        raise ValueError("SOURCE_LAYOUT_CONSTRAINTS_NOT_REVIEWED")
    if constraints.get("semantic_edge_authorization")!="none":
        raise ValueError("UNEXPECTED_SEMANTIC_EDGE_AUTHORIZATION")

    region=constraints["source"]["figure_region_pt"]
    source_w=float(region[2]-region[0])
    source_h=float(region[3]-region[1])
    canvas=spec["canvas"]
    canvas_w,canvas_h=float(canvas["width_in"]),float(canvas["height_in"])
    if min(source_w,source_h,canvas_w,canvas_h)<=0:
        raise ValueError("INVALID_LAYOUT_DIMENSIONS")
    if abs(source_w/source_h - canvas_w/canvas_h)/(source_w/source_h) > .02:
        raise ValueError("SOURCE_ASPECT_RATIO_MISMATCH")

    accepted={}
    for item in constraints.get("constraints",[]):
        if (item.get("constraint_type") not in ("panel_boundary","region_bounds") or
            item.get("scientific_relations_verified") is not False or
            item.get("semantic_edges") != [] or
            item.get("reviewer",{}).get("type")!="human"):
            continue
        if not isinstance(item.get("bbox_normalized"),list):
            continue
        accepted[item["id"]]=item

    mappings=binding.get("bindings",[])
    if not mappings:
        raise ValueError("GEOMETRY_BINDINGS_REQUIRED")
    if (len({m.get("target_element_id") for m in mappings}) != len(mappings) or
        len({m.get("source_constraint_id") for m in mappings}) != len(mappings)):
        raise ValueError("DUPLICATE_GEOMETRY_BINDING")
    result=copy.deepcopy(spec)
    by_id={e.get("id"):e for e in result.get("elements",[])}
    applied=[]
    for mapping in mappings:
        source_id=mapping.get("source_constraint_id")
        target_id=mapping.get("target_element_id")
        if source_id not in accepted:
            raise ValueError(f"UNKNOWN_REVIEWED_CONSTRAINT:{source_id}")
        if target_id not in by_id:
            raise ValueError(f"UNKNOWN_FIGURESPEC_ELEMENT:{target_id}")
        element=by_id[target_id]
        if (element.get("type") not in ("rect","roundRect","ellipse","image","group")
            or any(key not in element for key in ("x","y","w","h"))):
            raise ValueError(f"TARGET_NOT_BOUNDING_BOX_ELEMENT:{target_id}")
        normalized=accepted[source_id]["bbox_normalized"]
        if len(normalized)!=4 or not all(
            isinstance(v,(float,int)) and not isinstance(v,bool) and math.isfinite(v)
            for v in normalized
        ):
            raise ValueError(f"INVALID_REVIEWED_BBOX:{source_id}")
        x,y,w,h=normalized
        if min(x,y)<0 or min(w,h)<=0 or x+w>1.00001 or y+h>1.00001:
            raise ValueError(f"REVIEWED_BBOX_OUT_OF_BOUNDS:{source_id}")
        old={key:element[key] for key in ("x","y","w","h")}
        new={
            "x":round(x*canvas_w,4),
            "y":round(y*canvas_h,4),
            "w":round(w*canvas_w,4),
            "h":round(h*canvas_h,4),
        }
        element.update(new)
        applied.append({
            "source_constraint_id":source_id,
            "target_element_id":target_id,
            "before_inches":old,
            "after_inches":new,
            "source_bbox_pt":accepted[source_id]["bbox_pt"],
        })

    result["layout_provenance"]={
        "source_layout_constraints_sha256":sha256(constraints_file),
        "geometry_bindings_sha256":sha256(bindings_file),
        "figure_spec_original_sha256":sha256(figure_spec),
        "bound_element_count":len(applied),
        "geometry_applied":True,
        "scientific_relations_verified":False,
        "note":"Only explicitly mapped human-reviewed source geometry was transferred; science relations and final visual fidelity remain unverified.",
        "applied_mappings":applied,
    }
    output_file.parent.mkdir(parents=True,exist_ok=True)
    output_file.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return {
        "status":"GEOMETRY_CONSTRAINTS_APPLIED",
        "bound_element_count":len(applied),
        "output":str(output_file),
        "output_sha256":sha256(output_file),
        "mapping_audit":applied,
        "scientific_relations_verified":False,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("figure_spec",type=Path)
    parser.add_argument("reviewed_source_constraints",type=Path)
    parser.add_argument("bindings",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=apply_reviewed_geometry(
        args.figure_spec,args.reviewed_source_constraints,args.bindings,args.output
    )
    print(json.dumps(result,ensure_ascii=False))


if __name__=="__main__":
    main()
