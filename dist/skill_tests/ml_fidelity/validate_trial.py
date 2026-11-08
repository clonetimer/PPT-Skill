"""Independent semantic checks for the three paper-figure fidelity trials."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"tools"))
from scientific_ir import CONTRACTS,validate_expected_topology,validate_spec

HERE=Path(__file__).resolve().parent

def load(subdir,stem):
    return json.loads((HERE/subdir/(stem+".json")).read_text(encoding="utf-8"))

def by_id(spec):
    return {e["semantic_id"]:e for e in spec["elements"] if e.get("semantic_id")}

for folder,stem in [("resnet","MLR01_resnet_residual_block"),
                    ("unet","MLU01_unet_architecture"),("clip","MLC01_clip_overview")]:
    spec=load(folder,stem)
    # Trial-specific contracts are embedded in the standalone FigureSpecs.
    CONTRACTS[stem]=spec["figure_contract"]
    validate_spec(spec)
    validate_expected_topology(spec,json.loads((HERE/folder/"expected_topology.json").read_text(encoding="utf-8")))

u=by_id(load("unet","MLU01_unet_architecture"))
dimensions={
    "input":"572×572", "enc0_first":"570×570", "enc0":"568×568",
    "pool0":"284×284", "pool1":"140×140", "pool2":"68×68",
    "bottleneck_input":"32×32", "bottleneck_first":"30×30", "bottleneck":"28×28",
    "copy3":"56×56", "dec3_first":"54×54", "dec3":"52×52",
    "copy0":"392×392", "dec0_first":"390×390", "dec0":"388×388", "output":"388×388",
}
for key,value in dimensions.items():
    assert u[key+"_dimension"]["text"]==value,(key,"dimension")
    assert u[key+"_dimension"]["rotation"]==-90,(key,"orientation")
for key,c in {"enc0":64,"pool0":64,"enc1":128,"pool1":128,"enc2":256,"pool2":256,
              "enc3":512,"bottleneck":1024,"copy3":1024,"copy2":512,
              "copy1":256,"copy0":128,"output":2}.items():
    assert u[key+"_channels"]["text"]==str(c),(key,"channels")
assert len([e for e in load("unet","MLU01_unet_architecture")["semantic_edges"] if e[0].startswith("enc") and e[1].startswith("copy")])==4
for level in range(4):
    white,blue=u[f"copy{level}"],u[f"up{level}"]
    assert abs(white["y"]-blue["y"])<.001 and abs(white["h"]-blue["h"])<.001
    assert 0<=blue["x"]-(white["x"]+white["w"])<=.025
    route=[e for e in load("unet","MLU01_unet_architecture")["elements"]
           if e.get("semantic_link") and e["semantic_link"].endswith(f"__up{level}")]
    assert route and route[-1]["x1"]==route[-1]["x2"]
    assert blue["x"]<=route[-1]["x2"]<=blue["x"]+blue["w"]
    assert route[-1]["y1"]>route[-1]["y2"]>=blue["y"]+blue["h"]-.001
    assert blue["h"]<u[f"enc{level}"]["h"] if "h" in u[f"enc{level}"] else True
assert u["output"]["h"]<u["input"]["h"]

r=load("resnet","MLR01_resnet_residual_block")
redges={tuple(x) for x in r["semantic_edges"]}
assert ("x","add") in redges and ("weight2","add") in redges
assert ("add","relu2") in redges and ("weight2","relu2") not in redges
assert ("x","weight1") in redges

c=by_id(load("clip","MLC01_clip_overview"))
assert len([k for k in c if k.startswith("matrix_cell_")])==25
for i in range(5):
    for j in range(5):
        assert c[f"matrix_cell_{i}_{j}"]["fill"]==("#d8e7fb" if i==j else "#ffffff")
cedges={tuple(x) for x in load("clip","MLC01_clip_overview")["semantic_edges"]}
assert ("class_vectors","score_row") in cedges and ("query_vector","score_row") in cedges
assert ("class_labels","prompt") in cedges and ("prompt","class_text_encoder") in cedges
assert c["query_image"]["type"]=="image" and c["train_image_encoder"]["type"]=="polygon"
clip_spec=load("clip","MLC01_clip_overview")
lines=[e for e in clip_spec["elements"] if e["type"]=="line"]
yn=c["train_image_vectors"]["y"]+4.5*(c["train_image_vectors"]["h"]/5)
assert any(abs(e["x1"]-4.17)<.001 and abs(e["x2"]-4.17)<.001 and
           min(e["y1"],e["y2"])<=4.65 and max(e["y1"],e["y2"])>=yn
           for e in lines),("I_n","disconnected image-vector trunk")
images=[e for e in clip_spec["elements"] if e["type"]=="image"]
assert images and all(e["evidence_ref"]=="asset_1" for e in images)
assert any(e["id"]=="asset_1" and "CC0" in e["source_locator"] for e in clip_spec["evidence_records"])
print("Three ML figure topology, dimension, and matrix checks passed")
