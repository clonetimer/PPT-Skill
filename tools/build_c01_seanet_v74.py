#!/usr/bin/env python3
"""Build the source-corrected, editable C01-SEANet graph-level excerpt (v7.4)."""
from __future__ import annotations

import json
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from render_figure_spec import render

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "figure_specs/c01/C01_SEANet_graph_level_v74.json"
SVG = ROOT / "examples/C01_SEANet_graph_level_v74.svg"
PPTX = ROOT / "dist/C01_SEANet_graph_level_v74.pptx"

PANEL_ALT = (
    "SEANet graph-level diagnosis panel excerpt from the FBG-SEANet graphical abstract. "
    "A stacked schematic total-graph input flows through GCN and pooling stages. "
    "The energy-assisted branch feeds the first GCN; the first pooling stage also "
    "feeds a second SR readout. Both SR outputs merge before Dense classification "
    "and a five-square class output. FBG construction is presented separately."
)


def _c_nv_pr(shape):
    for node in shape._element.iter():
        if node.tag.endswith("}cNvPr"):
            return node
    return None


def annotate_accessibility(path: Path) -> dict:
    prs = Presentation(path)
    if len(prs.slides) != 1:
        raise ValueError("C01_SEANET_V74_EXPECTS_ONE_SLIDE")
    slide = prs.slides[0]
    missing = []
    for index, shape in enumerate(slide.shapes):
        shape.name = f"C01_SEANet_v74_obj_{index:03d}"
        if shape.has_text_frame and shape.text.strip():
            alt = "Text label: " + shape.text.replace("\n", "; ")
        elif shape.shape_type == MSO_SHAPE_TYPE.LINE:
            alt = "Editable connector or graph edge in the SEANet graph-level diagnosis excerpt."
        elif shape.width > 10 * 914400 and shape.height > 5 * 914400:
            alt = PANEL_ALT
        else:
            alt = "Editable vector object in the SEANet graph-level diagnosis excerpt."
        node = _c_nv_pr(shape)
        if node is None:
            missing.append(shape.name)
        else:
            node.set("descr", alt)
    # Give the title a whole-panel description, not only its visible title text.
    for shape in slide.shapes:
        if shape.has_text_frame and shape.text.strip() == "Graph-level fault diagnosis framework":
            node = _c_nv_pr(shape)
            if node is not None:
                node.set("descr", PANEL_ALT)
    if missing:
        raise ValueError("ALT_TEXT_METADATA_MISSING:" + ",".join(missing))
    prs.save(path)
    return {
        "shape_count": len(slide.shapes),
        "alt_text_count": len(slide.shapes),
        "alt_text_coverage": 1.0,
        "panel_description": PANEL_ALT,
        "reading_order": "top-to-bottom source order; input graph precedes GCN/pooling and EA/SR branches",
    }


def main():
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    SVG.parent.mkdir(parents=True, exist_ok=True)
    PPTX.parent.mkdir(parents=True, exist_ok=True)
    render(spec, SVG, PPTX)
    accessibility = annotate_accessibility(PPTX)
    report = {
        "spec": str(SPEC.relative_to(ROOT)),
        "svg": str(SVG.relative_to(ROOT)),
        "pptx": str(PPTX.relative_to(ROOT)),
        "element_count": len(spec["elements"]),
        "accessibility": accessibility,
    }
    report_path = ROOT / "dist/C01_SEANet_graph_level_v74_build.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
