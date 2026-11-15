#!/usr/bin/env python3
"""Execute the C01-FBG source-title and region-detail repair as immutable Round 01."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from pptx import Presentation

from repair_case_artifacts import (
    compare_pngs, pptx_object_diff, render_pptx, sha256_file, write_json
)
from scientific_ir import ROOT
from validate_c01_fbg_v74 import validate

INITIAL = ROOT / "dist/C01_FBG_construction_v73.pptx"
FINAL = ROOT / "dist/C01_FBG_construction_v74.pptx"


def figure_spec_diff(before_path: Path, after_path: Path) -> dict:
    before=json.loads(Path(before_path).read_text(encoding="utf-8"))
    after=json.loads(Path(after_path).read_text(encoding="utf-8"))
    a={e["id"]:e for e in before["elements"]}
    b={e["id"]:e for e in after["elements"]}
    changes=[]
    for object_id in sorted(set(a)|set(b)):
        if object_id not in a: changes.append({"id":object_id,"kind":"added","after":b[object_id]})
        elif object_id not in b: changes.append({"id":object_id,"kind":"removed","before":a[object_id]})
        else:
            fields={key:{"before":a[object_id].get(key),"after":b[object_id].get(key)}
                    for key in sorted(set(a[object_id])|set(b[object_id]))
                    if a[object_id].get(key)!=b[object_id].get(key)}
            if fields: changes.append({"id":object_id,"kind":"modified","fields":fields})
    return {"initial_elements":len(a),"final_elements":len(b),
            "added":sum(x["kind"]=="added" for x in changes),
            "removed":sum(x["kind"]=="removed" for x in changes),
            "modified":sum(x["kind"]=="modified" for x in changes),
            "changes":changes}


def run_case(output_dir: Path, accepted_output: Path, publish: bool=True) -> dict:
    output_dir=Path(output_dir).resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("C01_FBG_REPAIR_CASE_OUTPUT_DIR_MUST_BE_EMPTY")
    if not INITIAL.is_file() or not FINAL.is_file():
        raise FileNotFoundError("C01_FBG_INITIAL_OR_FINAL_PPTX_MISSING")
    output_dir.mkdir(parents=True,exist_ok=True)
    rounds=output_dir/"rounds";rounds.mkdir(parents=True,exist_ok=True)
    first_pass=rounds/"first_pass.pptx"
    round_01=rounds/"round_01.pptx"
    shutil.copy2(INITIAL,first_pass)
    shutil.copy2(FINAL,round_01)

    object_diff=pptx_object_diff(first_pass,round_01)
    spec_diff=figure_spec_diff(
        ROOT/"figure_specs/c01/C01_FBG_construction.json",
        ROOT/"figure_specs/c01/C01_FBG_construction_v74.json",
    )
    write_json(output_dir/"round_01_object_diff.json",object_diff)
    write_json(output_dir/"round_01_figure_spec_diff.json",spec_diff)
    quality=validate()
    write_json(output_dir/"round_01_quality_audit.json",quality)

    import subprocess,sys
    subprocess.run([sys.executable,str(ROOT/"tools/audit_pptx.py"),str(round_01),"--strict"],check=True)
    renders=output_dir/"renders"
    pdf0,pages0=render_pptx(first_pass,renders,"first_pass")
    pdf1,pages1=render_pptx(round_01,renders,"round_01")
    if len(pages0)!=1 or len(pages1)!=1:
        raise AssertionError("C01_FBG_EXPECTS_ONE_RENDERED_PAGE")
    comparison=compare_pngs(pages0[0],pages1[0],renders/"first_pass_vs_round_01.png")

    accepted_output=Path(accepted_output)
    accepted_output.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(round_01,accepted_output)
    if publish:
        shutil.copy2(pdf1,ROOT/"dist/C01_FBG_construction_v74.pdf")
        shutil.copy2(pages1[0],ROOT/"dist/C01_FBG_construction_v74.preview.png")

    history={
        "schema_version":"1.0.0","case":"C01_FBG","status":"COMPLETED",
        "diagnosis":{
            "confirmed_defect":"The prior redraw replaced the author-graphic title Time-Frequency Graph with the paper-method term Frequency-band Graph and omitted the explicit frequency-direction cue and some source-visible fault-sensitivity/band-order labels.",
            "operation":"Restore the exact source-visible title; add a subtitle preserving the paper's FBG term; restore qualitative OCF fault-sensitivity cues, ordinal subgraph labels, ellipsis and frequency direction.",
            "non_claims":"No numerical cutoff frequencies, measured waveform amplitudes, quantitative sensitivity scale or numerical adjacency matrix are asserted."
        },
        "first_pass":{"path":"rounds/first_pass.pptx","sha256":sha256_file(first_pass),"immutable":True},
        "rounds":[{
            "round":1,"path":"rounds/round_01.pptx","sha256":sha256_file(round_01),
            "operation":"source-grounded local FBG title and region-detail repair",
            "accepted":True,"rejected":False,
            "object_diff":"round_01_object_diff.json",
            "figure_spec_diff":"round_01_figure_spec_diff.json",
            "quality_audit":"round_01_quality_audit.json",
            "render_evidence":[str(pdf0.relative_to(output_dir)),str(pages0[0].relative_to(output_dir)),
                               str(pdf1.relative_to(output_dir)),str(pages1[0].relative_to(output_dir)),
                               str(comparison.relative_to(output_dir))]
        }],
        "accepted_rounds":1,"rejected_rounds":0,
        "final_sha256":sha256_file(round_01),
        "human_final_review":"PENDING","office_2016_host_round_trip":"PENDING"
    }
    write_json(output_dir/"repair_history.json",history)
    summary={"case":"C01_FBG","status":"ROUND_01_REPAIR_EXECUTED_AND_AUDITED",
             "initial_sha256":sha256_file(first_pass),"round_01_sha256":sha256_file(round_01),
             "pptx_object_changes":object_diff["changed_objects"],
             "figure_spec_added":spec_diff["added"],"figure_spec_modified":spec_diff["modified"],
             "quality":quality,"human_final_review":"PENDING","office_2016_host_round_trip":"PENDING"}
    write_json(output_dir/"repair_case_summary.json",summary)
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir",type=Path,required=True)
    parser.add_argument("--accepted-output",type=Path,default=ROOT/"dist/accepted_repairs/C01_FBG_construction_v74.pptx")
    args=parser.parse_args()
    print(json.dumps(run_case(args.output_dir,args.accepted_output),ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
