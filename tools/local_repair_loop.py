"""Run evidence-backed, non-destructive local PPTX repair rounds.

Each round starts from the previous accepted candidate, writes a new immutable
PPTX, computes a source-object diff, runs the quality audit, and only promotes
the candidate when it introduces no hard regression.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches,Pt

ALLOWED={"move","rotate","set_text"}
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def metadata(shape):
 nodes=[n for n in shape._element.iter() if n.tag.endswith("}cNvPr")]
 if not nodes or not nodes[0].get("descr"): return {}
 try:return json.loads(nodes[0].get("descr"))
 except Exception:return {}
def snapshot(path):
 prs=Presentation(path);out={}
 for sh in prs.slides[0].shapes:
  m=metadata(sh);sid=m.get("source_object_id")
  if not sid: continue
  out[sid]={"name":sh.name,"left":sh.left,"top":sh.top,"width":sh.width,"height":sh.height,
   "rotation":float(sh.rotation),"text":sh.text if sh.has_text_frame else None,
   "font_sizes":[float(r.font.size.pt) for p in sh.text_frame.paragraphs for r in p.runs if r.font.size] if sh.has_text_frame else []}
 return out
def diff(before,after):
 changes=[]
 for sid in sorted(set(before)|set(after)):
  if sid not in before: changes.append({"id":sid,"kind":"added"});continue
  if sid not in after: changes.append({"id":sid,"kind":"removed"});continue
  fields={}
  for k in before[sid]:
   if before[sid][k]!=after[sid][k]:fields[k]={"before":before[sid][k],"after":after[sid][k]}
  if fields:changes.append({"id":sid,"kind":"modified","fields":fields})
 return changes
def apply_operation(shape,op):
 kind=op["operation"]
 if kind not in ALLOWED: raise ValueError("UNSUPPORTED_REPAIR_OPERATION:"+str(kind))
 if kind=="move":
  shape.left=int(op["left_emu"]);shape.top=int(op["top_emu"])
 elif kind=="rotate":
  shape.rotation=float(op["rotation_degrees"])%360
 elif kind=="set_text":
  if not shape.has_text_frame:raise ValueError("TARGET_HAS_NO_TEXT_FRAME")
  shape.text=str(op["text"])
def run_repair_loop(source_pptx,plan_path,manifest_path,output_dir,max_rounds=3):
 source_pptx,plan_path,manifest_path,output_dir=map(Path,(source_pptx,plan_path,manifest_path,output_dir))
 plan=json.loads(plan_path.read_text(encoding="utf-8"))
 manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
 if manifest.get("status")!="COMPOSITION_PLAN_READY":raise ValueError("COMPOSITION_MANIFEST_NOT_EXECUTABLE")
 if manifest.get("policy",{}).get("execution_authorized") is not False:raise ValueError("COMPOSITION_AUTHORIZATION_INVALID")
 rounds=plan.get("rounds",[])
 if len(rounds)>max_rounds:raise ValueError("MAX_REPAIR_ROUNDS_EXCEEDED")
 output_dir.mkdir(parents=True,exist_ok=True)
 immutable=output_dir/"first_pass.pptx"
 if not immutable.exists():shutil.copy2(source_pptx,immutable)
 elif sha(immutable)!=sha(source_pptx):raise ValueError("FIRST_PASS_IMMUTABLE_BASELINE_MISMATCH")
 accepted=immutable
 history=[]
 from reconstruction_quality_metrics import evaluate_reconstruction_quality
 previous_metrics=evaluate_reconstruction_quality(manifest_path,accepted)
 for index,round_spec in enumerate(rounds,1):
  candidate=output_dir/f"round_{index:02d}.pptx"
  shutil.copy2(accepted,candidate)
  before=snapshot(accepted)
  prs=Presentation(candidate)
  lookup={}
  for slide in prs.slides:
   for sh in slide.shapes:
    sid=metadata(sh).get("source_object_id")
    if sid:lookup[sid]=sh
  applied=[]
  for op in round_spec.get("operations",[]):
   sid=op.get("source_object_id")
   if sid not in lookup:raise ValueError("UNKNOWN_REPAIR_SOURCE_OBJECT:"+str(sid))
   sh=lookup[sid]
   if op.get("expected_text") is not None and (not sh.has_text_frame or sh.text!=op["expected_text"]):
    raise ValueError("REPAIR_PRECONDITION_TEXT_MISMATCH:"+sid)
   if op.get("expected_rotation") is not None and abs(float(sh.rotation)-float(op["expected_rotation"]))>0.01:
    raise ValueError("REPAIR_PRECONDITION_ROTATION_MISMATCH:"+sid)
   apply_operation(sh,op);applied.append({"source_object_id":sid,"operation":op["operation"]})
  prs.save(candidate)
  after=snapshot(candidate)
  changes=diff(before,after)
  metrics=evaluate_reconstruction_quality(manifest_path,candidate)
  regression=[]
  if metrics["object_preservation"]["source_object_recall"] < previous_metrics["object_preservation"]["source_object_recall"]:
   regression.append("OBJECT_RECALL_REGRESSION")
  if metrics["object_preservation"]["duplicate_object_ids"]:
   regression.append("DUPLICATE_SOURCE_OBJECTS")
  if metrics["object_preservation"]["missing_object_ids"]:
   regression.append("MISSING_SOURCE_OBJECTS")
  if metrics["object_order"]["exact_order_match"] if "object_order" in metrics else False:
   pass
  if metrics["status"]=="FAIL":regression.extend(metrics.get("blockers",[]))
  accepted_round=not regression
  record={"round":index,"candidate":candidate.name,"candidate_sha256":sha(candidate),
   "base_sha256":sha(accepted),"applied_operations":applied,"object_diff":changes,
   "quality_status":metrics["status"],"quality_report":metrics,"regressions":sorted(set(regression)),
   "accepted":accepted_round}
  history.append(record)
  if accepted_round:
   accepted=candidate;previous_metrics=metrics
  else:
   candidate.unlink(missing_ok=True)
   record["candidate"]="REJECTED_AND_REMOVED"
   break
 report={"schema_version":"1.0.0","status":"COMPLETED" if history else "NO_REPAIR_ROUNDS",
  "first_pass_path":str(immutable),"first_pass_sha256":sha(immutable),
  "final_path":str(accepted),"final_sha256":sha(accepted),
  "accepted_rounds":sum(x["accepted"] for x in history),"rejected_rounds":sum(not x["accepted"] for x in history),
  "repair_history":history,"final_quality_status":previous_metrics["status"],
  "policy":{"first_pass_immutable":True,"round_artifacts_immutable":True,"object_level_diff":True,"automatic_scientific_approval":False}}
 (output_dir/"repair_history.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 return report
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("source_pptx",type=Path);p.add_argument("repair_plan",type=Path);p.add_argument("composition_manifest",type=Path);p.add_argument("--output-dir",type=Path,required=True);p.add_argument("--max-rounds",type=int,default=3);a=p.parse_args()
 r=run_repair_loop(a.source_pptx,a.repair_plan,a.composition_manifest,a.output_dir,a.max_rounds)
 print(json.dumps({"status":r["status"],"accepted_rounds":r["accepted_rounds"],"rejected_rounds":r["rejected_rounds"],"final":r["final_path"],"quality":r["final_quality_status"]},ensure_ascii=False))
if __name__=="__main__":main()
