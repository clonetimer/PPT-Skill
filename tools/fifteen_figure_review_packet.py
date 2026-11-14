"""Build a 15-figure repair comparison and final-review packet.

The tool never labels identical initial/reconciliation exports as a repair.
A final delivery PASS remains reserved for independent human review.
"""
from __future__ import annotations
import argparse,hashlib,json,zipfile
from pathlib import Path
from pptx import Presentation

TASKS=("B01","F07","C01_FBG","C01_SEANet","C01_composite","Q01","Q02","Q03","Q03P","Q04","Q05","Q06","Q07","I01","DECK01")
TASK_FILENAMES={
 "B01":"B01_engineering_fdir_v71.pptx",
 "F07":"F07_telemetry_embedding_v71.pptx",
 "C01_FBG":"C01_FBG_construction_v73.pptx",
 "C01_SEANet":"C01_SEANet_graph_level_v73.pptx",
 "C01_composite":"C01_composite_defense_slide_v74.pptx",
 "Q01":"Q01_iris_scatter.pptx",
 "Q02":"Q02_iris_strip.pptx",
 "Q03":"Q03_iris_mean_ci.pptx",
 "Q03P":"Q03_iris_mean_ci_nature.pptx",
 "Q04":"Q04_iris_confusion.pptx",
 "Q05":"Q05_iris_ablation.pptx",
 "Q06":"Q06_iris_trend_interval.pptx",
 "Q07":"Q07_wine_scatter.pptx",
 "I01":"I01_cell_image_quant.pptx",
 "DECK01":"DECK01_c01_defense.pptx",
}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def shape_inventory(path):
 prs=Presentation(path);out=[]
 for si,slide in enumerate(prs.slides,1):
  for ix,s in enumerate(slide.shapes):
   out.append({"slide":si,"index":ix,"name":s.name,"type":str(s.shape_type),
    "left":s.left,"top":s.top,"width":s.width,"height":s.height,
    "rotation":float(s.rotation),"text":s.text if s.has_text_frame else None})
 return out
def compare(initial,final):
 a=shape_inventory(initial);b=shape_inventory(final)
 def key(x):return (x["slide"],x["name"],x["index"])
 aa={key(x):x for x in a};bb={key(x):x for x in b};changes=[]
 for k in sorted(set(aa)|set(bb)):
  if k not in aa:changes.append({"kind":"added","after":bb[k]})
  elif k not in bb:changes.append({"kind":"removed","before":aa[k]})
  else:
   fields={f:{"before":aa[k][f],"after":bb[k][f]} for f in aa[k] if aa[k][f]!=bb[k][f]}
   if fields:changes.append({"kind":"modified","key":k,"fields":fields})
 return {"initial_sha256":sha(initial),"final_sha256":sha(final),
  "byte_identical":sha(initial)==sha(final),"initial_shape_count":len(a),"final_shape_count":len(b),
  "object_diff":changes,"changed_objects":len(changes)}
def build_packet(initial_dir,final_dir,output_dir):
 initial_dir,final_dir,output_dir=map(Path,(initial_dir,final_dir,output_dir))
 output_dir.mkdir(parents=True,exist_ok=True);rows=[]
 for task in TASKS:
  filename=TASK_FILENAMES[task]
  initial=initial_dir/filename
  final=final_dir/filename
  base={"task_id":task,"filename":filename,"final_review_status":"pending","final_decision":None}
  if not initial.is_file():
   rows.append({**base,"status":"MISSING_INITIAL"});continue
  if not final.is_file():
   rows.append({**base,"status":"NO_FINAL_REPAIR_ARTIFACT","initial":filename});continue
  diff=compare(initial,final)
  status="NO_REPAIR_APPLIED" if diff["byte_identical"] else "REPAIR_COMPARISON_READY"
  rows.append({**base,"status":status,"initial":filename,"final":filename,"diff":diff})
 packet={"schema_version":"1.0.0","population":len(TASKS),"tasks":rows,
  "summary":{"comparison_ready":sum(x["status"]=="REPAIR_COMPARISON_READY" for x in rows),
   "no_repair_applied":sum(x["status"]=="NO_REPAIR_APPLIED" for x in rows),
   "missing":sum(x["status"] not in ("REPAIR_COMPARISON_READY","NO_REPAIR_APPLIED") for x in rows)},
  "acceptance_policy":{"human_final_review_required":True,"ci_is_not_final_acceptance":True,
   "identical_files_never_count_as_repair":True}}
 path=output_dir/"15_figure_repair_comparison_review.json"
 path.write_text(json.dumps(packet,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 readme=output_dir/"README_15_FIGURE_REVIEW.md"
 readme.write_text("# 15-figure repair comparison review\n\nFor each task, inspect the initial and final PPTX side by side. Review the recorded object-level diff and verify science, data/image integrity, readability, accessibility, editability/reproducibility, and visual quality. Record reviewer identity, discipline, six scores with evidence, and explicit hard-failure clearance in the final review ledger. Do not mark byte-identical artifacts as repaired. CI does not count as independent acceptance.\n",encoding="utf-8")
 return packet
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("initial_dir",type=Path);p.add_argument("final_dir",type=Path);p.add_argument("--output-dir",type=Path,required=True);a=p.parse_args()
 r=build_packet(a.initial_dir,a.final_dir,a.output_dir);print(json.dumps(r["summary"],ensure_ascii=False))
if __name__=="__main__":main()
