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
TASK_FINAL_FILENAMES={**TASK_FILENAMES,"C01_FBG":"C01_FBG_construction_v74.pptx","C01_SEANet":"C01_SEANet_graph_level_v74.pptx","C01_composite":"C01_composite_defense_slide_v75.pptx","DECK01":"DECK01_c01_defense_v76.pptx"}
# Q07 is a two-artifact deliverable: scatter (Q07) plus categorical distribution (Q08).
TASK_COMPANION_FILENAMES={"Q07":("Q08_wine_strip.pptx",)}
TASK_SUPPLEMENTARY_FILENAMES={"C01_composite":("C01_composite_explainer_v76.pptx","C01_composite_explainer_v76.pdf","C01_composite_explainer_v76_slide_1.png","C01_composite_explainer_v76_slide_2.png")}
TASK_SPEC_FILENAMES={"C01_FBG":{"initial":"figure_specs/c01/C01_FBG_construction.json","final":"figure_specs/c01/C01_FBG_construction_v74.json"},"C01_SEANet":{"initial":"tests/fixtures/C01_SEANet_graph_level_initial_v73.json","final":"figure_specs/c01/C01_SEANet_graph_level_v74.json"},"C01_composite":{"initial":"figure_specs/c01/C01_composite_defense_slide.json","final":"figure_specs/c01/C01_composite_defense_slide_v75.json"}}
TASK_DECK_SPEC_FILENAMES={"DECK01":{"initial":"specs/deck_spec_v75.example.json","final":"specs/deck_spec_v76.example.json"}}
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def shape_inventory(path):
 prs=Presentation(path);out=[]
 for si,slide in enumerate(prs.slides,1):
  for ix,s in enumerate(slide.shapes):
   out.append({"slide":si,"index":ix,"name":s.name,"type":str(s.shape_type),
    "left":s.left,"top":s.top,"width":s.width,"height":s.height,
    "rotation":float(s.rotation),"text":s.text if s.has_text_frame else None,
    "paragraph_alignments":[int(p.alignment) if p.alignment is not None else None for p in s.text_frame.paragraphs] if s.has_text_frame else [],
    "font_runs":[{"text":r.text,"name":r.font.name,"size_pt":r.font.size.pt if r.font.size else None,
                  "bold":r.font.bold,"italic":r.font.italic} for p in s.text_frame.paragraphs for r in p.runs] if s.has_text_frame else []})
 return out
def compare(initial,final):
 a=shape_inventory(initial);b=shape_inventory(final)
 def key(x):return (x["slide"],x["index"])
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
def compare_specs(initial_path,final_path):
 a=json.loads(Path(initial_path).read_text(encoding="utf-8"))
 b=json.loads(Path(final_path).read_text(encoding="utf-8"))
 aa={x["id"]:x for x in a["elements"]};bb={x["id"]:x for x in b["elements"]};changes=[]
 for object_id in sorted(set(aa)|set(bb)):
  if object_id not in aa:changes.append({"id":object_id,"kind":"added","after":bb[object_id]})
  elif object_id not in bb:changes.append({"id":object_id,"kind":"removed","before":aa[object_id]})
  else:
   fields={key:{"before":aa[object_id].get(key),"after":bb[object_id].get(key)}
           for key in sorted(set(aa[object_id])|set(bb[object_id]))
           if aa[object_id].get(key)!=bb[object_id].get(key)}
   if fields:changes.append({"id":object_id,"kind":"modified","fields":fields})
 return {"initial_sha256":sha(initial_path),"final_sha256":sha(final_path),
         "initial_elements":len(aa),"final_elements":len(bb),
         "added":sum(x["kind"]=="added" for x in changes),
         "removed":sum(x["kind"]=="removed" for x in changes),
         "modified":sum(x["kind"]=="modified" for x in changes),
         "changes":changes}


def compare_json(initial_path,final_path):
 a=json.loads(Path(initial_path).read_text(encoding="utf-8"))
 b=json.loads(Path(final_path).read_text(encoding="utf-8"));changes=[]
 def walk(path,left,right):
  if isinstance(left,dict) and isinstance(right,dict):
   for key in sorted(set(left)|set(right)):
    if key not in left:changes.append({"path":f"{path}.{key}","kind":"added","after":right[key]})
    elif key not in right:changes.append({"path":f"{path}.{key}","kind":"removed","before":left[key]})
    else:walk(f"{path}.{key}",left[key],right[key])
  elif isinstance(left,list) and isinstance(right,list):
   if left!=right:changes.append({"path":path,"kind":"modified","before":left,"after":right})
  elif left!=right:changes.append({"path":path,"kind":"modified","before":left,"after":right})
 walk("deck_spec",a,b)
 return {"initial_sha256":sha(initial_path),"final_sha256":sha(final_path),
         "changed_fields":len(changes),"changes":changes}

def build_packet(initial_dir,final_dir,output_dir):
 initial_dir,final_dir,output_dir=map(Path,(initial_dir,final_dir,output_dir))
 output_dir.mkdir(parents=True,exist_ok=True);rows=[]
 diagnostics=json.loads((ROOT/"specs/15_figure_diagnostic_ledger_v76.json").read_text(encoding="utf-8"))["tasks"]
 for task in TASKS:
  initial_filename=TASK_FILENAMES[task]
  final_filename=TASK_FINAL_FILENAMES[task]
  initial=initial_dir/initial_filename
  final=final_dir/final_filename
  diagnosis=diagnostics[task]
  base={"task_id":task,"initial_filename":initial_filename,"final_filename":final_filename,"diagnosis_status":diagnosis["status"],"diagnosis_note":diagnosis["note"],"final_review_status":"pending","final_decision":None}
  if not initial.is_file():
   rows.append({**base,"status":"MISSING_INITIAL"});continue
  if not final.is_file():
   rows.append({**base,"status":"NO_FINAL_REPAIR_ARTIFACT","initial":initial_filename});continue
  diff=compare(initial,final)
  companion_diffs=[]
  companion_missing=[]
  supplementary_artifacts=[]
  supplementary_missing=[]
  for filename in TASK_SUPPLEMENTARY_FILENAMES.get(task,()):
   supplementary=final_dir/filename
   if supplementary.is_file():
    supplementary_artifacts.append({"filename":filename,"sha256":sha(supplementary),"size_bytes":supplementary.stat().st_size})
   else:
    supplementary_missing.append(filename)
  for companion_filename in TASK_COMPANION_FILENAMES.get(task,()):
   companion_initial=initial_dir/companion_filename
   companion_final=final_dir/companion_filename
   if not companion_initial.is_file() or not companion_final.is_file():
    companion_missing.append({"filename":companion_filename,
      "initial_exists":companion_initial.is_file(),"final_exists":companion_final.is_file()})
    continue
   companion_diffs.append({"filename":companion_filename,
      "diff":compare(companion_initial,companion_final)})
  diff["companion_artifacts"]=companion_diffs
  diff["companion_missing"]=companion_missing
  diff["supplementary_artifacts"]=supplementary_artifacts
  diff["supplementary_missing"]=supplementary_missing
  if task in TASK_SPEC_FILENAMES:
   spec_paths=TASK_SPEC_FILENAMES[task]
   diff["figure_spec_diff"]=compare_specs(ROOT/spec_paths["initial"],ROOT/spec_paths["final"])
  if task in TASK_DECK_SPEC_FILENAMES:
   spec_paths=TASK_DECK_SPEC_FILENAMES[task]
   diff["deck_spec_diff"]=compare_json(ROOT/spec_paths["initial"],ROOT/spec_paths["final"])
  status=("MISSING_COMPANION_ARTIFACT" if companion_missing else "MISSING_SUPPLEMENTARY_ARTIFACT" if supplementary_missing else
          "NO_REPAIR_APPLIED" if diff["byte_identical"] and all(x["diff"]["byte_identical"] for x in companion_diffs)
          else "REPAIR_COMPARISON_READY")
  rows.append({**base,"status":status,"initial":initial_filename,"final":final_filename,"diff":diff})
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
