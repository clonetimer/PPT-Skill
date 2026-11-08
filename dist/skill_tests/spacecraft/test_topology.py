#!/usr/bin/env python3
"""Independent relation fixture and omission mutations for spacecraft figure."""
from __future__ import annotations
import copy,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/"tools"))
from scientific_ir import validate_drawn_routes  # noqa: E402
SPEC=json.loads((HERE/"SC01_spacecraft_bus_mechanism.json").read_text(encoding="utf-8"))
EXPECT={tuple(e) for e in json.loads((HERE/"expected_topology.json").read_text(encoding="utf-8"))["required_edges"]}

class SpacecraftTopologyTests(unittest.TestCase):
 def test_complete_relations(self):
  self.assertEqual({tuple(e) for e in SPEC["semantic_edges"]},EXPECT)
  validate_drawn_routes(SPEC,EXPECT)
 def test_critical_omissions_fail(self):
  for source,target in [("solar_array","pcdu"),("attitude","adcs_sensor"),
                        ("command_bus","prop_valve"),("radiator","space")]:
   with self.subTest(edge=(source,target)):
    changed=copy.deepcopy(SPEC)
    changed["semantic_edges"].remove([source,target])
    changed["elements"]=[e for e in changed["elements"]
                         if e.get("semantic_link")!=f"{source}__{target}"]
    with self.assertRaises(AssertionError):validate_drawn_routes(changed,EXPECT)
if __name__=="__main__":unittest.main()
