"""Calculate immutable first-pass and evidence-backed final delivery rates.

A final PASS requires a completed independent human review, all six dimensions
>=2, evidence for each dimension, and all hard-fail checks explicitly false.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path

DIMENSIONS=("science","data_image_integrity","readability","accessibility","editability_reproducibility","visual_quality")
HARD_FAILS=("critical_scientific_error","source_or_provenance_error","undisclosed_image_processing","unreadable_critical_content")

def calculate(baseline_path:Path,ledger_path:Path)->dict:
 baseline=json.loads(Path(baseline_path).read_text(encoding="utf-8"))
 ledger=json.loads(Path(ledger_path).read_text(encoding="utf-8"))
 rows=baseline.get("rows",[])
 population=int(baseline.get("first_pass_generated",len(rows)))
 first=sum(bool(x.get("first_pass",{}).get("strict_pass")) for x in rows)
 reviewers={x.get("reviewer_id"):x for x in ledger.get("reviewers",[]) if x.get("reviewer_id")}
 tasks=ledger.get("tasks",[])
 completed=[];accepted=[];invalid=[];repaired=[]
 for task in tasks:
  if task.get("final_review_status")!="completed":
   continue
  reasons=[]
  reviewer=reviewers.get(task.get("reviewer_id"))
  if not reviewer: reasons.append("REVIEWER_NOT_REGISTERED")
  elif reviewer.get("independent") is not True: reasons.append("REVIEWER_NOT_INDEPENDENT")
  elif reviewer.get("discipline") not in task.get("required_disciplines",[]): reasons.append("REVIEWER_DISCIPLINE_MISMATCH")
  if task.get("initial_review_before_expectations") is not True: reasons.append("INITIAL_REVIEW_ORDER_NOT_ATTESTED")
  scores=task.get("dimension_scores",{})
  evidence=task.get("dimension_evidence",{})
  for dim in DIMENSIONS:
   score=scores.get(dim)
   if not isinstance(score,int) or isinstance(score,bool) or score<0 or score>4:
    reasons.append("INVALID_SCORE:"+dim)
   elif score<2: reasons.append("DIMENSION_BELOW_THRESHOLD:"+dim)
   if not isinstance(evidence.get(dim),str) or not evidence[dim].strip():
    reasons.append("MISSING_EVIDENCE:"+dim)
  hard=task.get("hard_failures",{})
  for flag in HARD_FAILS:
   if hard.get(flag) is not False: reasons.append("HARD_FAIL_NOT_EXPLICITLY_CLEARED:"+flag)
  if task.get("final_decision") not in ("PASS","FAIL"): reasons.append("INVALID_FINAL_DECISION")
  if reasons:
   invalid.append({"task_id":task.get("task_id"),"reasons":reasons})
   continue
  completed.append(task)
  if task["final_decision"]=="PASS":
   accepted.append(task)
   if int(task.get("repair_rounds",0))>0: repaired.append(task)
 eligible_count=len(completed)
 registered=len(tasks)
 return {
  "schema_version":"1.1.0",
  "first_pass":{
   "dataset_id":baseline.get("dataset_id"),"population":population,"passed":first,
   "rate":round(first/max(1,population),6),
   "mean_score_24":baseline.get("mean_score_24"),
   "immutable":True,"score_source":"frozen historical model-assessed baseline"
  },
  "final_delivery":{
   "registered_tasks":registered,"completed_valid_reviews":eligible_count,
   "accepted":len(accepted),"accepted_after_repair":len(repaired),
   "rate_among_completed":round(len(accepted)/eligible_count,6) if eligible_count else None,
   "rate_over_registered_population":round(len(accepted)/registered,6) if registered else None,
   "status":"MEASURED" if eligible_count else "NOT_YET_MEASURABLE",
   "invalid_completed_reviews":invalid,
   "repair_rounds_mean_for_accepted":round(sum(int(t.get("repair_rounds",0)) for t in accepted)/len(accepted),3) if accepted else None,
   "rule":"PASS requires independent reviewer, prior blind initial review, six evidenced dimensions >=2, and all hard-fail checks explicitly false."
  },
  "cohort_policy":{
   "first_pass_baseline_immutable":True,
   "development_cohort_is_not_blind_holdout":True,
   "scientific_and_office_host_gates_separate":True
  }
 }

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("baseline",type=Path);p.add_argument("ledger",type=Path)
 p.add_argument("--output",type=Path,required=True);a=p.parse_args()
 result=calculate(a.baseline,a.ledger)
 a.output.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
