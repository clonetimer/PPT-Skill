"""Prepare the immutable 15-figure initial cohort with explicit repair baselines."""
from __future__ import annotations
import argparse,shutil
from pathlib import Path
from fifteen_figure_review_packet import TASK_FILENAMES

def prepare(initial_dir:Path,output_dir:Path,overrides:dict|None=None)->dict:
    initial_dir,output_dir=Path(initial_dir),Path(output_dir);overrides=overrides or {}
    if output_dir.exists() and any(output_dir.iterdir()):raise ValueError("INITIAL_COHORT_OUTPUT_DIR_MUST_BE_EMPTY")
    output_dir.mkdir(parents=True,exist_ok=True);copied=[]
    for task,filename in TASK_FILENAMES.items():
        source=Path(overrides.get(task,initial_dir/filename))
        if not source.is_file():raise FileNotFoundError(f"MISSING_INITIAL_COHORT_INPUT:{task}:{source}")
        destination=output_dir/filename;shutil.copy2(source,destination)
        copied.append({"task_id":task,"filename":filename,"source":str(source),"destination":str(destination)})
    return {"population":len(copied),"copied":copied,"override_tasks":sorted(overrides)}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("initial_dir",type=Path)
    p.add_argument("--output-dir",type=Path,required=True);p.add_argument("--c01-seanet-initial",type=Path,required=True)
    a=p.parse_args();r=prepare(a.initial_dir,a.output_dir,{"C01_SEANet":a.c01_seanet_initial})
    print(f"Prepared {r['population']} initial figures; override={r['override_tasks']}")
if __name__=="__main__":main()
