#!/usr/bin/env python3
"""Compare two same-size rendered slide PNGs and write an explicit pixel-diff record."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageChops


def compare(first: Path, second: Path, diff_path: Path) -> dict:
    a=Image.open(first).convert("RGB")
    b=Image.open(second).convert("RGB")
    if a.size!=b.size:
        raise ValueError(f"IMAGE_SIZE_MISMATCH:{a.size}:{b.size}")
    aa=np.asarray(a,dtype=np.int16)
    bb=np.asarray(b,dtype=np.int16)
    delta=np.abs(aa-bb)
    changed=np.any(delta>0,axis=2)
    diff_path.parent.mkdir(parents=True,exist_ok=True)
    ImageChops.difference(a,b).save(diff_path)
    return {"size":list(a.size),"mean_absolute_error":float(delta.mean()),
            "max_absolute_error":int(delta.max()),"changed_pixel_ratio":float(changed.mean()),
            "diff_png":str(diff_path)}


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("first",type=Path)
    parser.add_argument("second",type=Path)
    parser.add_argument("--diff",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=compare(args.first,args.second,args.diff)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\\n",encoding="utf-8")
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
