import json, tempfile, unittest
from pathlib import Path
from final_delivery_success import calculate

class FinalDeliverySuccessTests(unittest.TestCase):
 def test_first_pass_is_immutable_and_final_requires_human_review(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d); baseline=root/"baseline.json"; final=root/"final.json"
   baseline.write_text(json.dumps({"dataset_id":"frozen","first_pass_generated":2,"mean_score_24":18.2,"rows":[
    {"figure_id":"a","first_pass":{"strict_pass":False}},
    {"figure_id":"b","first_pass":{"strict_pass":False}}]}))
   final.write_text(json.dumps({"tasks":[
    {"final_review_status":"completed","final_decision":"PASS","repair_rounds":2},
    {"final_review_status":"pending","final_decision":None,"repair_rounds":0}]}))
   r=calculate(baseline,final)
   self.assertEqual(r["first_pass"]["rate"],0)
   self.assertEqual(r["final_delivery"]["accepted"],1)
   self.assertEqual(r["final_delivery"]["accepted_after_repair"],1)
   self.assertEqual(r["final_delivery"]["rate_among_completed"],1)
   self.assertEqual(r["final_delivery"]["rate_over_registered_population"],0.5)
 def test_no_human_reviews_is_not_reported_as_zero_percent(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d); baseline=root/"baseline.json"; final=root/"final.json"
   baseline.write_text(json.dumps({"first_pass_generated":1,"rows":[{"figure_id":"x","first_pass":{"strict_pass":False}}]}))
   final.write_text(json.dumps({"tasks":[{"final_review_status":"pending","final_decision":None}]}))
   r=calculate(baseline,final)
   self.assertIsNone(r["final_delivery"]["rate_among_completed"])
   self.assertEqual(r["final_delivery"]["status"],"NOT_YET_MEASURABLE")

if __name__=="__main__": unittest.main()
