#!/usr/bin/env python3
"""Tree-KG high-fidelity trial checks, including licensed picture allowlist."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from pptx import Presentation
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"tools"))
from audit_figure_occlusion import audit  # noqa: E402
from audit_pptx import overlaps  # noqa: E402

ID="TK02_treekg_source_composition"
spec=json.loads((OUT/f"{ID}.json").read_text(encoding="utf-8"))
assert audit(spec)==[]
provenance=json.loads((OUT/"assets/provenance.json").read_text(encoding="utf-8"))
allowed={bytes.fromhex(provenance[k]["png_sha256"]) for k in ("robot","open_book")}
for k,name in (("robot","robot.svg"),("open_book","book-open-text.svg")):
    assert hashlib.sha256((OUT/"assets"/name).read_bytes()).hexdigest()==provenance[k]["source_sha256"]

deck=Presentation(OUT/f"{ID}.pptx")
assert len(deck.slides)==1
slide=deck.slides[0]
text_shapes=[s for s in slide.shapes if s.has_text_frame and s.text.strip()]
assert not [(a,b) for i,a in enumerate(text_shapes) for b in text_shapes[i+1:] if overlaps(a,b)]
assert all(s.left>=0 and s.top>=0 and s.left+s.width<=deck.slide_width and s.top+s.height<=deck.slide_height for s in slide.shapes)
pictures=[s for s in slide.shapes if s.shape_type==13]
assert len(pictures)==7
assert all(hashlib.sha256(s.image.blob).digest() in allowed for s in pictures)

pdf=OUT/f"{ID}.pdf";png=OUT/f"{ID}.png"
assert pdf.stat().st_size>10000 and png.stat().st_size>10000
pdf_text=" ".join(p.extract_text() or "" for p in PdfReader(pdf).pages)
for phrase in ("Initial Construction","Iterative Expansion","Contextual-based","Entity Deduplication","Structure Integration"):
    assert phrase in pdf_text,phrase
print(json.dumps({"figure":ID,"shapes":len(slide.shapes),"licensed_icons":len(pictures),
                  "text_overlaps":0,"line_occlusions":0,"out_of_bounds":0,"pdf_text_checked":True},indent=2))
