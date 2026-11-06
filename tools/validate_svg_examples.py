#!/usr/bin/env python3
"""Validate standalone SVG examples using only the Python standard library."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

def main(paths):
    failed=False
    for path in paths:
        root=ET.parse(path).getroot()
        view_box=root.attrib.get("viewBox")
        width=root.attrib.get("width")
        height=root.attrib.get("height")
        if not view_box or not width or not height:
            print(f"FAIL {path}: missing width/height/viewBox");failed=True
        else: print(f"PASS {path}: {width} x {height}, viewBox={view_box}")
    return 1 if failed else 0

if __name__=="__main__":
    args=[Path(p) for p in sys.argv[1:]] or sorted(Path("examples").glob("*.svg"))
    raise SystemExit(main(args))
