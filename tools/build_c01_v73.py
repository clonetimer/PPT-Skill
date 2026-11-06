#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
for stem in ("C01_FBG_construction","C01_SEANet_graph_level"):
 spec=ROOT/"figure_specs"/"c01"/(stem+".json")
 subprocess.run([sys.executable,str(ROOT/"tools"/"render_figure_spec.py"),str(spec),"--svg",str(ROOT/"examples"/(stem+"_v73.svg")),"--pptx",str(ROOT/"dist"/(stem+"_v73.pptx"))],check=True)
 print("Built",stem)
