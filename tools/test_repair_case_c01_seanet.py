import tempfile,unittest
from pathlib import Path
from repair_case_c01_seanet import run_case,TARGET_ID

class C01SeanetFirstRepairCaseTests(unittest.TestCase):
 def test_first_repair_changes_only_fault_class_alignment(self):
  with tempfile.TemporaryDirectory() as d:
   result=run_case(Path(d)/"case")
  self.assertEqual(result["status"],"REPAIR_EXECUTED_AND_AUDITED")
  self.assertEqual(result["accepted_rounds"],1)
  self.assertEqual(result["rejected_rounds"],0)
  self.assertEqual(result["target_source_object_id"],TARGET_ID)
  self.assertEqual(result["spec_parity"]["status"],"PASS")
  self.assertFalse(result["scientific_topology_changed"])
  self.assertFalse(result["font_or_geometry_changed"])
  self.assertEqual(len(result["object_diff"]),1)
  change=result["object_diff"][0]
  self.assertEqual(change["id"],TARGET_ID)
  self.assertEqual(change["fields"]["paragraph_alignments"],{"before":["center"],"after":["right"]})

if __name__=="__main__":unittest.main()
