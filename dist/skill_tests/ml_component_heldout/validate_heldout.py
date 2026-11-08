"""Independent checks for the held-out Wide Residual Networks Figure 1 trial."""
from __future__ import annotations

import json
import copy
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/"tools"))
from scientific_ir import CONTRACTS,validate_expected_topology,validate_spec

spec=json.loads((HERE/"MLH01_wide_resnet_variants.json").read_text(encoding="utf-8"))
expected=json.loads((HERE/"expected_topology.json").read_text(encoding="utf-8"))
CONTRACTS[spec["id"]]=spec["figure_contract"]
validate_spec(spec)
validate_expected_topology(spec,expected)
by_id={e["semantic_id"]:e for e in spec["elements"] if e.get("semantic_id")}
expected_layers={
    "a":[("conv3×3","#F0BD96"),("conv3×3","#F0BD96")],
    "b":[("conv1×1","#8DCFE4"),("conv3×3","#F0BD96"),("conv1×1","#8DCFE4")],
    "c":[("conv3×3","#F0BD96"),("conv3×3","#F0BD96")],
    "d":[("conv3×3","#F0BD96"),("dropout","#E59DA5"),("conv3×3","#F0BD96")],
}
for key,layers in expected_layers.items():
    shapes=[by_id[f"{key}_layer_{i}"] for i in range(len(layers))]
    for i,((label,color),shape) in enumerate(zip(layers,shapes)):
        assert shape["fill"].lower()==color.lower(),(key,i,"fill")
        # Text is the next editable element, directly after its layer bar.
        pos=spec["elements"].index(shape)
        assert spec["elements"][pos+1]["text"]==label,(key,i,"label")
    assert all(shapes[i]["y"]<shapes[i+1]["y"] for i in range(len(shapes)-1))
assert by_id["c_layer_0"]["w"]>by_id["a_layer_0"]["w"]
assert by_id["b_layer_0"]["w"]>by_id["b_layer_1"]["w"]
assert all(by_id[f"{k}_add"]["type"]=="ellipse" for k in expected_layers)
assert len(spec["semantic_edges"])==22
mutant=copy.deepcopy(spec)
next(e for e in mutant["elements"] if e.get("semantic_id")=="d_layer_1_label")["text"]="conv3×3"
try:
    validate_expected_topology(mutant,expected)
except AssertionError:
    pass
else:
    raise AssertionError("A corrupted dropout label passed the held-out contract")
print("Held-out Figure 1: four variants, widths, labels, 22 routes and corrupted-label rejection passed")
