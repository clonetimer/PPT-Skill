#!/usr/bin/env python3
"""Record an Image2 target image in a V8 per-slide workflow manifest."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
EXPECTED_SIZE=(1920,1080)
def _resolve_inside(root:Path,path:Path)->Path:
    root=Path(root).resolve();candidate=Path(path)
    if not candidate.is_absolute():candidate=root/candidate
    candidate=candidate.resolve()
    if not candidate.is_relative_to(root):raise ValueError(f"ASSET_OUTSIDE_REPOSITORY:{path}")
    return candidate
def _sha256(path:Path)->str:
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()
def record_target(manifest_path:Path,image_path:Path,root:Path=ROOT,iteration:int|None=None)->dict:
    root=Path(root).resolve();manifest_path=_resolve_inside(root,manifest_path);image_path=_resolve_inside(root,image_path)
    if not manifest_path.is_file():raise FileNotFoundError(f"MANIFEST_MISSING:{manifest_path}")
    if not image_path.is_file():raise FileNotFoundError(f"TARGET_IMAGE_MISSING:{image_path}")
    m=json.loads(manifest_path.read_text(encoding="utf-8"));a=m["stage_a"]
    if a["status"] in {"approved","locked"}:raise ValueError("CANNOT_REPLACE_APPROVED_STAGE_A_TARGET")
    try:
        with Image.open(image_path) as im:
            size=im.size;media={"PNG":"image/png","JPEG":"image/jpeg","WEBP":"image/webp"}.get(im.format)
    except Exception as exc:raise ValueError(f"TARGET_IMAGE_UNREADABLE:{exc}") from exc
    if media is None:raise ValueError("UNSUPPORTED_TARGET_IMAGE_FORMAT")
    if size!=EXPECTED_SIZE:raise ValueError(f"TARGET_IMAGE_DIMENSIONS_MUST_BE_1920x1080:{size[0]}x{size[1]}")
    current=int(a["generation"]["iteration"]);next_i=current+1 if iteration is None else int(iteration)
    if next_i<1 or next_i<=current:raise ValueError("IMAGE_ITERATION_MUST_INCREASE")
    a["generation"]["iteration"]=next_i;a["status"]="generated"
    a["target_image"]={"path":image_path.relative_to(root).as_posix(),"sha256":_sha256(image_path),
                       "width_px":size[0],"height_px":size[1],"media_type":media}
    a["review"]={"decision":"pending","reviewer":None,"reviewed_at":None,
                 "checks":{"scientific_content":False,"exact_text":False,"source_fidelity":False,
                           "visual_hierarchy":False,"projection_readability":False,
                           "reconstruction_feasibility":False},"issues":[]}
    manifest_path.write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return {"workflow_id":m["workflow_id"],"iteration":next_i,"target_image":a["target_image"]}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("manifest",type=Path);p.add_argument("target_image",type=Path)
    p.add_argument("--root",type=Path,default=ROOT);p.add_argument("--iteration",type=int);a=p.parse_args()
    print(json.dumps(record_target(a.manifest,a.target_image,a.root,a.iteration),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
