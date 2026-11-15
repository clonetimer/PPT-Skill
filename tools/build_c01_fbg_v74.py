#!/usr/bin/env python3
"""Build source-corrected C01 FBG v7.4 with the original title and frequency-axis cues."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from render_figure_spec import render
from scientific_ir import ROOT, CONTRACTS

SOURCE = ROOT / "figure_specs/c01/C01_FBG_construction.json"
SPEC = ROOT / "figure_specs/c01/C01_FBG_construction_v74.json"
SVG = ROOT / "examples/C01_FBG_construction_v74.svg"
PPTX = ROOT / "dist/C01_FBG_construction_v74.pptx"

PANEL_ALT = (
    "Graph Construction (Time-Frequency Graph), corresponding to the paper's frequency-band graph (FBG) method. "
    "Sensor signals pass through OCF notch filtering, where operational components are removed and fault-sensitivity "
    "cues become clearer qualitatively. Band-pass filters produce one subgraph per frequency band; the first, second, "
    "third and Nth bands are arranged along the frequency direction and connected into a total graph. "
    "Sensor glyphs, waveforms, node coordinates and inter-band links are schematic; no numerical cutoffs or adjacency matrix are asserted."
)


def build_spec() -> dict:
    spec = copy.deepcopy(json.loads(SOURCE.read_text(encoding="utf-8")))
    by_id = {element["id"]: element for element in spec["elements"]}

    # Preserve the exact source-visible heading while retaining the paper's FBG terminology.
    by_id["el_0001"]["text"] = "Graph Construction (Time-Frequency Graph)"
    by_id["el_0001"]["size"] = 21
    by_id["el_0003"]["text"] = "Band-pass filters"
    by_id["el_0003"]["size"] = 10.5

    labels = [
        ("el_0026", "Sub graph 1:\n1st band", 6.06, 2.03, 1.03),
        ("el_0028", "Sub graph 2:\n2nd band", 6.06, 2.91, 1.03),
        ("el_0030", "Sub graph 3:\n3rd band", 6.06, 3.79, 1.03),
        ("el_0032", "Sub graph N:\nNth band", 6.06, 4.67, 1.03),
    ]
    for object_id, value, x, y, width in labels:
        element = by_id[object_id]
        element.update(text=value, x=x, y=y, w=width, h=.40, size=9.5, align="left")

    # Keep the original OCF waveform sequence and add the source-visible qualitative cue.
    by_id["el_0011"]["text"] = "Operational component\nremoved"
    by_id["el_0011"].update(y=4.48, h=.48, size=9.5)
    by_id["el_0041"]["text"] = "Fault-sensitivity cues\nclearer (qualitative)"
    by_id["el_0041"].update(x=4.54, y=5.00, w=1.43, h=.38, size=9.5)
    extra = [
        {
            "type":"text","text":"Fault sensitivity","x":4.62,"y":3.45,"w":1.27,"h":.18,
            "size":9.5,"font":"Times New Roman","color":"#43525B","align":"center",
            "id":"el_0042","semantic_role":"annotation","evidence_ref":"source_1"
        },
        {
            "type":"text","text":"Fault sensitivity","x":4.62,"y":4.22,"w":1.27,"h":.18,
            "size":9.0,"font":"Times New Roman","color":"#43525B","align":"center",
            "id":"el_0043","semantic_role":"annotation","evidence_ref":"source_1"
        },
        {
            "type":"text","text":"…","x":6.38,"y":4.30,"w":.20,"h":.18,
            "size":11,"font":"Times New Roman","color":"#687780","align":"center",
            "id":"el_0044","semantic_role":"annotation","evidence_ref":"source_1"
        },
        {
            "type":"line","x1":9.36,"y1":2.03,"x2":9.36,"y2":5.10,
            "color":"#43525B","sw":1.2,"arrow":True,"dash":False,
            "id":"el_0045","semantic_role":"connector","evidence_ref":"source_1"
        },
        {
            "type":"text","text":"Frequency","x":8.90,"y":5.22,"w":.92,"h":.20,
            "size":9.5,"font":"Times New Roman","color":"#28343C","align":"center",
            "id":"el_0046","semantic_role":"annotation","evidence_ref":"source_1"
        },
    ]
    extra.append({
        "type":"text","text":"Frequency-band graph (FBG) construction","x":0.45,"y":0.66,"w":12.43,"h":0.18,
        "size":10.5,"font":"Times New Roman","color":"#687780","align":"left",
        "id":"el_0047","semantic_role":"annotation","evidence_ref":"source_1"
    })
    spec["elements"].extend(extra)
    by_id["el_0039"]["text"] = (
        "One subgraph is formed per frequency band; connected subgraphs form the final frequency-band graph."
    )
    by_id["el_0039"].update(size=10.2, y=5.90, h=.40)
    by_id["el_0040"]["text"] = (
        "Sensor glyphs and waveforms, graph coordinates and inter-band links are schematic; "
        "no numerical band cutoffs or adjacency matrix are asserted."
    )
    by_id["el_0040"].update(size=8.8, y=6.42, h=.30)

    spec["schema_version"] = "7.6.0-dev"
    spec["version"] = "7.4.0"
    spec["source"] = {
        **spec.get("source", {}),
        "figure": "Author-published graphical abstract; exact source-visible title retained as 'Graph Construction (Time-Frequency Graph)'",
        "terminology": "The article text calls the proposed construction a frequency-band graph (FBG). The figure title and paper-method term are both retained and distinguished.",
        "evidence": "Source-visible structural redraw. Sensor photographs and waveforms are editable vector stand-ins; graph coordinates and inter-band links are schematic."
    }
    spec["evidence_status"] = "source_visible_redraw"
    spec["scientific_source_ref"] = "docs/C01_V73_SOURCE.md"
    spec["claim"] = (
        "Sensor signals pass through OCF notch filtering; band-pass filters create one subgraph per frequency band; "
        "the subgraphs are connected into a total graph."
    )
    spec["figure_contract"] = {
        "claim": spec["claim"],
        "archetype": "schematic_led_composite",
        "output_mode": "presentation",
        "unverified": [
            "Exact numerical frequency cutoffs",
            "Measured waveform amplitudes",
            "Numerical graph adjacency and exact node coordinates",
            "Quantitative fault-sensitivity scale",
            "Pixel-level source-image match"
        ]
    }
    source_path=ROOT/"docs/C01_V73_SOURCE.md"
    source_hash=hashlib.sha256(source_path.read_bytes()).hexdigest()
    spec["evidence_records"] = [{
        "id":"source_1",
        "source":"docs/C01_V73_SOURCE.md",
        "source_file_sha256":source_hash,
        "source_locator":"Author-lab graphical abstract, upper Graph Construction (Time-Frequency Graph) panel; public abstract and method description for FBG terminology; publisher high-resolution image not directly accessed",
        "status":"source_visible_redraw",
        "scope":"Sensor signals, OCF/notch filter, qualitative fault-sensitivity cue, band-pass subgraphs, frequency direction and total graph. Sensor glyphs, waveforms and graph coordinates are schematic.",
        "reuse":"derivative_redraw_only"
    }]
    return spec


def _c_nv_pr(shape):
    for node in shape._element.iter():
        if node.tag.endswith("}cNvPr"):
            return node
    return None


def annotate_accessibility(path: Path) -> dict:
    deck=Presentation(path)
    if len(deck.slides)!=1:
        raise ValueError("C01_FBG_V74_EXPECTS_ONE_SLIDE")
    slide=deck.slides[0]
    missing=[]
    for index,shape in enumerate(slide.shapes):
        shape.name=f"C01_FBG_v74_obj_{index:03d}"
        if shape.has_text_frame and shape.text.strip():
            description="Text label: "+shape.text.replace("\n","; ")
        elif shape.shape_type==MSO_SHAPE_TYPE.LINE:
            description="Connector showing the OCF, frequency-band or total-graph construction flow."
        elif shape.shape_type==MSO_SHAPE_TYPE.FREEFORM:
            description="Editable schematic sensor waveform; not measured telemetry."
        elif shape.width>10*914400 and shape.height>5*914400:
            description=PANEL_ALT
        else:
            description="Editable vector object in the FBG time-frequency graph construction schematic."
        node=_c_nv_pr(shape)
        if node is None:
            missing.append(shape.name)
        else:
            node.set("descr",description)
    if missing:
        raise ValueError("ALT_TEXT_METADATA_MISSING:"+",".join(missing))
    for shape in slide.shapes:
        if shape.has_text_frame and "Graph Construction (Time-Frequency Graph)" in shape.text:
            node=_c_nv_pr(shape)
            if node is not None: node.set("descr",PANEL_ALT)
    deck.save(path)
    return {"shape_count":len(slide.shapes),"alt_text_count":len(slide.shapes),
            "alt_text_coverage":1.0,"panel_description":PANEL_ALT,
            "reading_order":"title, sensor signals, OCF before/after cue, frequency-band subgraphs in increasing frequency order, total graph"}


def main():
    spec=build_spec()
    SPEC.parent.mkdir(parents=True,exist_ok=True)
    SVG.parent.mkdir(parents=True,exist_ok=True)
    PPTX.parent.mkdir(parents=True,exist_ok=True)
    SPEC.write_text(json.dumps(spec,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    render(spec,SVG,PPTX)
    accessibility=annotate_accessibility(PPTX)
    report={"spec":str(SPEC.relative_to(ROOT)),"svg":str(SVG.relative_to(ROOT)),
            "pptx":str(PPTX.relative_to(ROOT)),"element_count":len(spec["elements"]),
            "accessibility":accessibility}
    (ROOT/"dist/C01_FBG_construction_v74_build.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
