"""Calculate first-pass and final-delivery success separately.

First-pass scores are read from the immutable frozen baseline. Final success is
counted only from a completed, human-reviewed final acceptance ledger.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

def calculate(baseline_path: Path, final_review_path: Path) -> dict:
    baseline=json.loads(Path(baseline_path).read_text(encoding="utf-8"))
    rows=baseline.get("rows",[])
    first_generated=int(baseline.get("first_pass_generated",len(rows)))
    first_passed=sum(bool(row.get("first_pass",{}).get("strict_pass")) for row in rows)
    final=json.loads(Path(final_review_path).read_text(encoding="utf-8"))
    tasks=final.get("tasks",[])
    eligible=[t for t in tasks if t.get("final_review_status")=="completed"]
    accepted=[t for t in eligible if t.get("final_decision")=="PASS"]
    repaired=[t for t in accepted if int(t.get("repair_rounds",0))>0]
    first_pass_ids={r["figure_id"] for r in rows if r.get("first_pass",{}).get("strict_pass")}
    return {
      "schema_version":"1.0.0",
      "first_pass":{
        "dataset_id":baseline.get("dataset_id"),
        "population":first_generated,
        "passed":first_passed,
        "rate":round(first_passed/max(1,first_generated),6),
        "mean_score_24":baseline.get("mean_score_24"),
        "score_source":"frozen model-assessed baseline; not independent domain review"
      },
      "final_delivery":{
        "registered_tasks":len(tasks),
        "completed_human_reviews":len(eligible),
        "accepted":len(accepted),
        "accepted_after_repair":len(repaired),
        "rate_among_completed":round(len(accepted)/max(1,len(eligible)),6) if eligible else None,
        "rate_over_registered_population":round(len(accepted)/max(1,len(tasks)),6) if tasks else None,
        "status":"MEASURED" if eligible else "NOT_YET_MEASURABLE",
        "rule":"Only completed human reviews with PASS count; CI and model scores are not substitutes."
      },
      "cohort_policy":{
        "first_pass_baseline_immutable":True,
        "development_cohort_is_not_blind_holdout":True,
        "first_pass_ids":sorted(first_pass_ids),
        "scientific_and_office_host_gates_separate":True
      }
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("baseline",type=Path)
    p.add_argument("final_review",type=Path)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    report=calculate(a.baseline,a.final_review)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
