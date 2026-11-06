#!/usr/bin/env python3
"""Build V7.1.1 FigureSpec examples (B01 and F07) to SVG and PPTX."""
from pathlib import Path
import subprocess, sys

ROOT=Path(__file__).resolve().parents[1]
EXAMPLES=ROOT/"examples"
DIST=ROOT/"dist"
EXAMPLES.mkdir(exist_ok=True)
DIST.mkdir(exist_ok=True)

for spec_name,out_name in [
    ("B01_engineering_fdir","B01_engineering_fdir_v71"),
    ("F07_telemetry_embedding","F07_telemetry_embedding_v71"),
]:
    subprocess.run([
        sys.executable,str(ROOT/"tools"/"render_figure_spec.py"),
        str(ROOT/"figure_specs"/f"{spec_name}.json"),
        "--svg",str(EXAMPLES/f"{out_name}.svg"),
        "--pptx",str(DIST/f"{out_name}.pptx"),
    ],check=True)
