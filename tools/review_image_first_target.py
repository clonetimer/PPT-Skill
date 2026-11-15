#!/usr/bin/env python3
"""Record a human/assistant-triage Stage-A review in a V8 workflow manifest."""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CHECKS=("scientific_content","exact_text","source_fidelity","visual_hierarchy","projection_readability","reconstruction_feasibility")
def record_review(manifest_path:Path,decision:str,reviewer:str,reviewer_type:str,checks:list[str]|None=None,
                  issues:list[str]|None=None,reviewed_at:str|None=None)->dict:
    p=Path(manifest_path).resolve();m=json.loads(p.read_text(encoding="utf-8"));a=m["stage_a"]
    if a.get("target_image") is None:raise ValueError("STAGE_A_TARGET_IMAGE_REQUIRED_BEFORE_REVIEW")
    if decision not in {"approve","revise"}:raise ValueError("UNSUPPORTED_REVIEW_DECISION")
    if reviewer_type not in {"human","assistant_visual_triage"}:raise ValueError("UNSUPPORTED_REVIEWER_TYPE")
    if not reviewer.strip():raise ValueError("REVIEWER_NAME_REQUIRED")
    checked=set(checks or []);unknown=checked-set(CHECKS)
    if unknown:raise ValueError(f"UNKNOWN_REVIEW_CHECKS:{','.join(sorted(unknown))}")
    issues=[str(x).strip() for x in (issues or []) if str(x).strip()]
    if decision=="approve":
        if reviewer_type!="human":raise ValueError("STAGE_A_APPROVAL_REQUIRES_HUMAN_REVIEWER")
        if checked!=set(CHECKS):
            missing=sorted(set(CHECKS)-checked);raise ValueError(f"STAGE_A_APPROVAL_CHECKS_INCOMPLETE:{','.join(missing)}")
        if issues:raise ValueError("STAGE_A_APPROVAL_CANNOT_HAVE_BLOCKING_ISSUES")
        a["status"]="approved";d="approved"
    else:
        if not issues:raise ValueError("STAGE_A_REVISION_REQUIRES_AT_LEAST_ONE_ISSUE")
        a["status"]="needs_revision";d="revise"
    ts=reviewed_at or datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
    a["review"]={"decision":d,"reviewer":{"name":reviewer.strip(),"type":reviewer_type},"reviewed_at":ts,
                 "checks":{k:k in checked for k in CHECKS},"issues":issues}
    p.write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return {"workflow_id":m["workflow_id"],"stage_a_status":a["status"],"decision":d,
            "reviewer":a["review"]["reviewer"],"reviewed_at":ts,"issues":issues}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("manifest",type=Path)
    p.add_argument("--decision",choices=("approve","revise"),required=True);p.add_argument("--reviewer",required=True)
    p.add_argument("--reviewer-type",choices=("human","assistant_visual_triage"),default="human")
    p.add_argument("--check",action="append",choices=CHECKS,default=[]);p.add_argument("--issue",action="append",default=[])
    p.add_argument("--reviewed-at");a=p.parse_args()
    print(json.dumps(record_review(a.manifest,a.decision,a.reviewer,a.reviewer_type,a.check,a.issue,a.reviewed_at),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
