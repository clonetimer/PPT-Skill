"""Source-derived route and mutation checks for the two revised paper figures."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/"tools"))
from scientific_ir import (CONTRACTS,validate_expected_topology,
                           validate_head_bundles,validate_spec)


def check(folder: str, stem: str) -> dict:
    base=HERE/folder
    spec=json.loads((base/(stem+".json")).read_text(encoding="utf-8"))
    fixture=json.loads((base/"expected_revision_topology.json").read_text(encoding="utf-8"))
    CONTRACTS[spec["id"]]=spec["figure_contract"]
    validate_spec(spec)
    validate_expected_topology(spec,fixture)
    if fixture.get("head_bundles"):
        validate_head_bundles(spec,fixture["head_bundles"])
    assert len(spec["semantic_edges"])==len(fixture["required_edges"])
    return spec


gat=check("gat","GAT_Figure1_revision")
detr=check("detr","DETR_Figure2_revision")

# The first-pass self-contribution deletion and output-query deletion now fail.
for source,drop in [(gat,{"node_1__node_1"}),
                    (detr,{"query_0__transformer_decoder"})]:
    mutant=copy.deepcopy(source)
    mutant["elements"]=[e for e in mutant["elements"]
                        if e.get("semantic_link") not in drop]
    try:
        fixture=json.loads((HERE/("gat" if source is gat else "detr")/
                            "expected_revision_topology.json").read_text(encoding="utf-8"))
        validate_expected_topology(mutant,fixture)
    except AssertionError:
        pass
    else:
        raise AssertionError("Critical route deletion passed revision validation")

by_id={e["semantic_id"]:e for e in detr["elements"] if e.get("semantic_id")}
encoder=by_id["transformer_encoder"]
assert by_id["enc_input_token_0"]["y"]>encoder["y"]+encoder["h"]
assert by_id["enc_output_token_0"]["y"]+by_id["enc_output_token_0"]["h"]<encoder["y"]
assert all(by_id[f"query_{i}"]["y"]>by_id["transformer_decoder"]["y"] for i in range(4))

gat_fixture=json.loads((HERE/"gat/expected_revision_topology.json").read_text(encoding="utf-8"))
head_mutant=copy.deepcopy(gat)
head_mutant["elements"]=[e for e in head_mutant["elements"]
                         if e.get("head_id") not in {"heads_1_1:head:0","heads_1_1:head:2"}]
try:
    validate_head_bundles(head_mutant,gat_fixture["head_bundles"])
except AssertionError:
    pass
else:
    raise AssertionError("Deleting two self-attention heads passed per-head validation")
assert {"enc_input_group","enc_output_group"}<={e.get("semantic_id") for e in detr["elements"]}
bird=by_id["source_bird_example"]
bird_record=next(e for e in detr["evidence_records"] if e["id"]==bird["evidence_ref"])
assert bird_record["status"]=="source_artwork_excerpt"
assert "raster detection rectangles" in bird_record["scope"]
assert "source-paper excerpt" in detr["evidence_records"][0]["reuse"]
print("GAT/DETR revisions: 53 source-derived routes, token groups, 21 head strands and mutations passed")
