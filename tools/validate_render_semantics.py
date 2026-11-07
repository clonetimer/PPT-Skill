#!/usr/bin/env python3
"""Check that each published chart label survives SVG, PPTX and PDF rendering."""
from __future__ import annotations

import json
import re
import unicodedata
import xml.etree.ElementTree as ET

from pptx import Presentation
from pypdf import PdfReader

from record_scientific_render import IDS, ROOT

NS = "{http://www.w3.org/2000/svg}"
LEGACY = [
    ("B01_engineering_fdir", "figure_specs/B01_engineering_fdir.json", "examples/B01_engineering_fdir_v71.svg", "dist/B01_engineering_fdir_v71.pptx", None),
    ("F07_telemetry_embedding", "figure_specs/F07_telemetry_embedding.json", "examples/F07_telemetry_embedding_v71.svg", "dist/F07_telemetry_embedding_v71.pptx", None),
    ("C01_FBG_construction", "figure_specs/c01/C01_FBG_construction.json", "examples/C01_FBG_construction_v73.svg", "dist/C01_FBG_construction_v73.pptx", None),
    ("C01_SEANet_graph_level", "figure_specs/c01/C01_SEANet_graph_level.json", "examples/C01_SEANet_graph_level_v73.svg", "dist/C01_SEANet_graph_level_v73.pptx", None),
    ("C01_composite_defense_slide", "figure_specs/c01/C01_composite_defense_slide.json", "examples/C01_composite_defense_slide_v74.svg", "dist/C01_composite_defense_slide_v74.pptx", "dist/C01_composite_defense_slide_v74_preview.pdf"),
]


def normalize(value):
    value = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"[^\w.%]+", "", value)


def main():
    paths = LEGACY + [
        (figure_id, f"figure_specs/{'image' if figure_id.startswith('I') else 'quant'}/{figure_id}.json",
         f"examples/{figure_id}.svg", f"dist/{figure_id}.pptx", f"dist/{figure_id}.pdf")
        for figure_id in IDS
    ]
    for figure_id, spec_path, svg_path, pptx_path, pdf_path in paths:
        spec = json.loads((ROOT / spec_path).read_text(encoding="utf-8"))
        expected = [e["text"] for e in spec["elements"] if e["type"] == "text" and e["text"].strip()]
        svg = ET.parse(ROOT / svg_path).getroot()
        svg_texts = ["".join(e.itertext()) for e in svg.findall(f".//{NS}text")]
        pptx = Presentation(ROOT / pptx_path)
        pptx_texts = [shape.text for shape in pptx.slides[0].shapes if getattr(shape, "has_text_frame", False)
                      and shape.text.strip()]
        if pdf_path:
            pdf = PdfReader(ROOT / pdf_path)
            assert len(pdf.pages) == 1
            pdf_text = normalize(pdf.pages[0].extract_text())
        for label in expected:
            key = normalize(label)
            assert key in {normalize(value) for value in svg_texts}, (figure_id, "svg", label)
            assert key in {normalize(value) for value in pptx_texts}, (figure_id, "pptx", label)
            if pdf_path:
                assert key in pdf_text, (figure_id, "pdf", label)
        print(f"PASS {figure_id}: {len(expected)} labels found in SVG/PPTX" + ("/PDF" if pdf_path else ""))


if __name__ == "__main__":
    main()
