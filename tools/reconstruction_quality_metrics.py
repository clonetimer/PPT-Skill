"""Multi-dimensional quality metrics for source-PDF-to-PPTX reconstruction."""
from __future__ import annotations

import argparse
import json
import math
import unicodedata
from pathlib import Path
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE


def _read_metadata(shape):
    nodes=[node for node in shape._element.iter() if node.tag.endswith("}cNvPr")]
    if not nodes or not nodes[0].get("descr"):
        return None
    try:
        value=json.loads(nodes[0].get("descr"))
    except (TypeError,ValueError):
        return None
    return value if isinstance(value,dict) else None


def _normalize_text(value):
    return unicodedata.normalize("NFC",str(value or ""))


def _levenshtein(a: str,b: str) -> int:
    if len(a)<len(b):
        a,b=b,a
    previous=list(range(len(b)+1))
    for i,ca in enumerate(a,1):
        current=[i]
        for j,cb in enumerate(b,1):
            current.append(min(
                current[-1]+1,
                previous[j]+1,
                previous[j-1]+(ca!=cb)
            ))
        previous=current
    return previous[-1]


def _bbox_iou(a,b):
    ix0=max(a[0],b[0]); iy0=max(a[1],b[1])
    ix1=min(a[2],b[2]); iy1=min(a[3],b[3])
    intersection=max(0,ix1-ix0)*max(0,iy1-iy0)
    area_a=max(0,a[2]-a[0])*max(0,a[3]-a[1])
    area_b=max(0,b[2]-b[0])*max(0,b[3]-b[1])
    union=area_a+area_b-intersection
    return intersection/union if union>0 else None


def _kendall_tau(order_a,order_b):
    common=[item for item in order_a if item in set(order_b)]
    if len(common)<2:
        return None
    pos={item:i for i,item in enumerate(order_b)}
    concordant=discordant=0
    for i in range(len(common)):
        for j in range(i+1,len(common)):
            delta=pos[common[i]]-pos[common[j]]
            if delta<0: concordant+=1
            elif delta>0: discordant+=1
    total=concordant+discordant
    return (concordant-discordant)/total if total else 1.0


def evaluate_reconstruction_quality(manifest_path: Path,pptx_path: Path,visual_report_path: Path|None=None) -> dict:
    manifest_path,pptx_path=Path(manifest_path),Path(pptx_path)
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status")!="COMPOSITION_PLAN_READY":
        raise ValueError("COMPOSITION_MANIFEST_NOT_EXECUTABLE")
    if manifest.get("policy",{}).get("execution_authorized") is not False:
        raise ValueError("COMPOSITION_MANIFEST_AUTHORIZATION_INVALID")
    expected={}
    for unit in manifest.get("composition_units",[]):
        for item in unit.get("objects",[]):
            if item.get("treatment") not in ("editable_vector","editable_text","picture_asset"):
                continue
            object_id=item["source_object_id"]
            if object_id in expected:
                raise ValueError(f"DUPLICATE_EXPECTED_SOURCE_OBJECT:{object_id}")
            expected[object_id]=item

    deck=Presentation(pptx_path)
    if len(deck.slides)!=1:
        raise ValueError("SOURCE_FIGURE_EXPECTS_SINGLE_SLIDE")
    shapes=[]
    by_id={}
    malformed=[]
    for index,shape in enumerate(deck.slides[0].shapes):
        meta=_read_metadata(shape)
        if meta is None or not meta.get("source_object_id"):
            malformed.append({"shape_index":index,"shape_name":shape.name})
            continue
        record={
            "shape_index":index,
            "source_object_id":meta["source_object_id"],
            "source_order":meta.get("source_order"),
            "object_class":meta.get("object_class"),
            "source_image_sha256":meta.get("source_image_sha256"),
            "source_image_xref":meta.get("source_image_xref"),
            "source_image_transform":meta.get("source_image_transform"),
            "source_image_pixel_size":meta.get("source_image_pixel_size"),
            "text":_normalize_text(shape.text if shape.has_text_frame else ""),
            "bbox_pt":[shape.left.pt,shape.top.pt,shape.left.pt+shape.width.pt,shape.top.pt+shape.height.pt],
            "is_picture":shape.shape_type==MSO_SHAPE_TYPE.PICTURE,
            "has_text_frame":bool(shape.has_text_frame),
            "shape_type":str(shape.shape_type),
        }
        shapes.append(record)
        by_id.setdefault(record["source_object_id"],[]).append(record)

    missing=sorted(set(expected)-set(by_id))
    unexpected=sorted(set(by_id)-set(expected))
    duplicates=sorted(key for key,values in by_id.items() if len(values)!=1)
    class_mismatches=[]
    for object_id,item in expected.items():
        values=by_id.get(object_id,[])
        if len(values)!=1: continue
        actual=values[0]
        treatment=item["treatment"]
        valid=(
            actual["is_picture"] if treatment=="picture_asset"
            else actual["has_text_frame"] and bool(actual["text"]) if treatment=="editable_text"
            else not actual["is_picture"] and actual["object_class"]=="vector"
        )
        if not valid:
            class_mismatches.append({"source_object_id":object_id,"expected":treatment,"actual":actual["shape_type"]})

    expected_order=sorted(
        [key for key,item in expected.items() if item.get("source_order") is not None],
        key=lambda key:(expected[key]["source_order"],key)
    )
    actual_order=[item["source_object_id"] for item in shapes
                  if item["source_order"] is not None and item["source_object_id"] in expected]
    exact_order=actual_order==expected_order
    tau=_kendall_tau(expected_order,actual_order)

    text_rows=[]
    for object_id,item in expected.items():
        if item.get("treatment")!="editable_text": continue
        actual=by_id.get(object_id,[])
        if len(actual)!=1:
            text_rows.append({"source_object_id":object_id,"status":"MISSING_OR_DUPLICATED","cer":None})
            continue
        source_text=_normalize_text(item.get("text",""))
        output_text=actual[0]["text"]
        if not source_text:
            text_rows.append({"source_object_id":object_id,"status":"NOT_COMPARABLE_NO_SOURCE_TEXT","cer":None})
            continue
        edits=_levenshtein(source_text,output_text)
        text_rows.append({
            "source_object_id":object_id,
            "status":"COMPARED",
            "source_characters":len(source_text),
            "output_characters":len(output_text),
            "edit_distance":edits,
            "cer":round(edits/len(source_text),6),
            "exact_match":source_text==output_text,
        })
    compared_text=[item for item in text_rows if item["status"]=="COMPARED"]
    total_chars=sum(item["source_characters"] for item in compared_text)
    total_edits=sum(item["edit_distance"] for item in compared_text)


    image_rows=[]
    for object_id,item in expected.items():
        if item.get("treatment")!="picture_asset":
            continue
        actual=by_id.get(object_id,[])
        if len(actual)!=1:
            image_rows.append({"source_object_id":object_id,"status":"MISSING_OR_DUPLICATED"})
            continue
        source_hash=item.get("source_image_sha256")
        actual_hash=actual[0].get("source_image_sha256")
        source_transform=item.get("source_image_transform")
        actual_transform=actual[0].get("source_image_transform")
        hash_status=("MATCH" if source_hash and source_hash==actual_hash else
                     "MISMATCH" if source_hash and actual_hash else "NOT_COMPARABLE")
        transform_status=("MATCH" if source_transform is not None and source_transform==actual_transform else
                          "MISMATCH" if source_transform is not None and actual_transform is not None else "NOT_COMPARABLE")
        source_pixels=item.get("source_image_pixel_size")
        output_pixels=actual[0].get("source_image_pixel_size")
        pixel_size_status=("MATCH" if source_pixels and source_pixels==output_pixels else
                           "MISMATCH" if source_pixels and output_pixels else "NOT_COMPARABLE")
        image_rows.append({
            "source_object_id":object_id,
            "source_image_sha256":source_hash,
            "output_image_sha256":actual_hash,
            "asset_hash_status":hash_status,
            "source_transform":source_transform,
            "output_transform":actual_transform,
            "transform_status":transform_status,
            "source_pixel_size":source_pixels,
            "output_pixel_size":output_pixels,
            "pixel_size_status":pixel_size_status,
            "status":"COMPARED" if hash_status=="MATCH" and transform_status=="MATCH" and pixel_size_status=="MATCH" else
                     "FAIL" if "MISMATCH" in (hash_status,transform_status,pixel_size_status) else "NOT_COMPARABLE",
        })
    image_failures=[row["source_object_id"] for row in image_rows if row["status"]=="FAIL"]

    region=manifest.get("source",{}).get("figure_region_pt")
    geometry_comparable=(
        isinstance(region,list) and len(region)==4
        and abs(float(region[0]))<1e-6 and abs(float(region[1]))<1e-6
    )
    geometry=[]
    if geometry_comparable:
        for object_id,item in expected.items():
            actual=by_id.get(object_id,[])
            source_box=item.get("bbox_pt")
            if len(actual)!=1 or not isinstance(source_box,list) or len(source_box)!=4:
                continue
            geometry.append({
                "source_object_id":object_id,
                "bbox_iou":round(_bbox_iou(source_box,actual[0]["bbox_pt"]),6),
            })
    geometry_status="COMPARABLE_FULL_PAGE_ORIGIN" if geometry_comparable else "NOT_COMPARABLE_CROP_OR_UNKNOWN_TRANSFORM"

    visual=None
    if visual_report_path is not None:
        visual=json.loads(Path(visual_report_path).read_text(encoding="utf-8"))

    blockers=[]
    if missing: blockers.append("MISSING_SOURCE_OBJECTS")
    if unexpected: blockers.append("UNEXPECTED_SOURCE_OBJECTS")
    if duplicates: blockers.append("DUPLICATED_SOURCE_OBJECTS")
    if malformed: blockers.append("MALFORMED_SHAPE_PROVENANCE")
    if class_mismatches: blockers.append("OBJECT_CLASS_MISMATCH")
    if image_failures: blockers.append("RASTER_SOURCE_IDENTITY_OR_TRANSFORM_MISMATCH")
    if not exact_order: blockers.append("SOURCE_ORDER_MISMATCH")
    if visual is not None and visual.get("requires_visual_review",False):
        blockers.append("VISUAL_DISCREPANCY_REQUIRES_REVIEW")
    status="FAIL" if blockers else "NEEDS_REVIEW" if geometry_status.startswith("NOT_COMPARABLE") or visual is None else "TECHNICAL_PASS"
    return {
        "schema_version":"1.0.0",
        "status":status,
        "provenance":{
            "composition_manifest_sha256":__import__("hashlib").sha256(manifest_path.read_bytes()).hexdigest(),
            "pptx_sha256":__import__("hashlib").sha256(pptx_path.read_bytes()).hexdigest(),
        },
        "object_preservation":{
            "expected_objects":len(expected),
            "actual_annotated_objects":len(shapes),
            "matched_unique_objects":sum(1 for key in expected if len(by_id.get(key,[]))==1),
            "source_object_recall":round(sum(1 for key in expected if len(by_id.get(key,[]))==1)/max(1,len(expected)),6),
            "unexpected_object_count":len(unexpected),
            "unexpected_object_rate":round(len(unexpected)/max(1,len(shapes)),6),
            "duplicate_object_ids":duplicates,
            "missing_object_ids":missing,
            "unexpected_object_ids":unexpected,
            "class_mismatches":class_mismatches,
            "malformed_shape_metadata":malformed,
        },
        "source_order":{
            "expected_order":expected_order,
            "actual_order":actual_order,
            "exact_order_match":exact_order,
            "kendall_tau":tau,
            "unsequenced_text_excluded":True,
        },
        "text_fidelity":{
            "compared_text_spans":len(compared_text),
            "exact_match_spans":sum(1 for item in compared_text if item["exact_match"]),
            "character_error_rate":round(total_edits/max(1,total_chars),6) if compared_text else None,
            "spans":text_rows,
        },
        "raster_fidelity":{
            "compared_assets":sum(row["status"]=="COMPARED" for row in image_rows),
            "not_comparable_assets":sum(row["status"]=="NOT_COMPARABLE" for row in image_rows),
            "failed_assets":image_failures,
            "assets":image_rows,
        },
        "geometry_fidelity":{
            "status":geometry_status,
            "compared_objects":len(geometry),
            "mean_bbox_iou":round(sum(item["bbox_iou"] for item in geometry)/len(geometry),6) if geometry else None,
            "per_object":geometry,
        },
        "visual_similarity":visual,
        "scientific_correctness":{
            "status":"NOT_AUTOMATED",
            "human_domain_review_required":True,
        },
        "office2016_host":{
            "status":"NOT_VERIFIED_BY_THIS_METRIC",
            "real_host_test_required":True,
        },
        "blockers":blockers,
        "policy":{
            "single_blended_score_emitted":False,
            "scientific_relations_verified":False,
            "execution_authorized":False,
        },
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("composition_manifest",type=Path)
    parser.add_argument("imported_pptx",type=Path)
    parser.add_argument("--visual-report",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=evaluate_reconstruction_quality(args.composition_manifest,args.imported_pptx,args.visual_report)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"object_recall":result["object_preservation"]["source_object_recall"],
                      "text_cer":result["text_fidelity"]["character_error_rate"],
                      "geometry":result["geometry_fidelity"]["status"],"blockers":result["blockers"],
                      "output":str(args.output)},ensure_ascii=False))
    if result["status"]=="FAIL": raise SystemExit(1)


if __name__=="__main__":
    main()
