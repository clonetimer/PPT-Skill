#!/usr/bin/env python3
"""Copy diagnosed no-repair candidates without overwriting repaired artifacts."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from fifteen_figure_review_packet import TASK_FINAL_FILENAMES, TASK_FILENAMES, TASK_COMPANION_FILENAMES
from repair_case_artifacts import sha256_file, write_json
from scientific_ir import ROOT

LEDGER = ROOT / "specs/15_figure_diagnostic_ledger_v76.json"


def prepare(initial_dir: Path, final_dir: Path) -> dict:
    initial_dir, final_dir = Path(initial_dir), Path(final_dir)
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    copied, preserved = [], []
    companion_copied, companion_preserved = [], []
    for task_id, diagnosis in ledger["tasks"].items():
        if diagnosis["status"] != "NO_CONFIRMED_DEFECT":
            continue
        initial = initial_dir / TASK_FILENAMES[task_id]
        final = final_dir / TASK_FINAL_FILENAMES[task_id]
        if not initial.is_file():
            raise FileNotFoundError(f"NO_REPAIR_INITIAL_MISSING:{task_id}:{initial}")
        final.parent.mkdir(parents=True, exist_ok=True)
        if final.exists():
            if sha256_file(final) != sha256_file(initial):
                raise ValueError(f"REFUSE_TO_OVERWRITE_EXISTING_REPAIR:{task_id}")
            preserved.append(task_id)
        else:
            shutil.copy2(initial, final)
            copied.append(task_id)
        for filename in TASK_COMPANION_FILENAMES.get(task_id,()):
            companion_initial=initial_dir/filename
            companion_final=final_dir/filename
            if not companion_initial.is_file():
                raise FileNotFoundError(f"NO_REPAIR_COMPANION_INITIAL_MISSING:{task_id}:{companion_initial}")
            companion_final.parent.mkdir(parents=True,exist_ok=True)
            if companion_final.exists():
                if sha256_file(companion_final)!=sha256_file(companion_initial):
                    raise ValueError(f"REFUSE_TO_OVERWRITE_EXISTING_COMPANION_REPAIR:{task_id}:{filename}")
                companion_preserved.append({"task_id":task_id,"filename":filename})
            else:
                shutil.copy2(companion_initial,companion_final)
                companion_copied.append({"task_id":task_id,"filename":filename})
    report = {
        "schema_version": "1.0.0",
        "no_confirmed_defect_tasks": copied + preserved,
        "copied": copied,
        "already_preserved": preserved,
        "companion_copied": companion_copied,
        "companion_already_preserved": companion_preserved,
        "policy": "Byte-identical candidates are marked NO_REPAIR_APPLIED, never as repaired or human-accepted.",
    }
    write_json(final_dir / "no_repair_candidate_manifest.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("initial_dir", type=Path)
    parser.add_argument("final_dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.initial_dir, args.final_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
