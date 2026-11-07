#!/usr/bin/env python3
"""Validate standalone SVG examples using only the Python standard library."""
import sys, xml.etree.ElementTree as ET
from pathlib import Path
NS="{http://www.w3.org/2000/svg}"
def check(p):
    root=ET.parse(p).getroot()
    ok=root.tag==NS+"svg" and all(root.attrib.get(k) for k in ("width","height","viewBox"))
    images=root.findall(".//"+NS+"image")
    if images:
        ok=ok and p.name=="I01_cell_image_quant.svg" and len(images)==1
        ok=ok and images[0].attrib.get("href","").startswith("data:image/png;base64,")
    ok=ok and root.find(".//"+NS+"foreignObject") is None
    print(("PASS " if ok else "FAIL ")+str(p))
    return ok
paths=[Path(x) for x in sys.argv[1:]] or sorted(Path("examples").glob("*.svg"))
raise SystemExit(0 if all(check(p) for p in paths) else 1)
