import json,tempfile,unittest
from pathlib import Path
from final_delivery_success import calculate,DIMENSIONS,HARD_FAILS

def good_task():
 return {"task_id":"X","final_review_status":"completed","final_decision":"PASS","reviewer_id":"R1",
 "required_disciplines":["control"],"initial_review_before_expectations":True,"repair_rounds":2,
 "dimension_scores":{d:3 for d in DIMENSIONS},"dimension_evidence":{d:"checked against source and rendered output" for d in DIMENSIONS},
 "hard_failures":{h:False for h in HARD_FAILS}}

class FinalDeliverySuccessTests(unittest.TestCase):
 def calc(self,tasks,independent=True):
  tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);p=Path(tmp.name)
  (p/"b.json").write_text(json.dumps({"dataset_id":"frozen","first_pass_generated":2,"mean_score_24":18.2,"rows":[
   {"figure_id":"a","first_pass":{"strict_pass":False}},{"figure_id":"b","first_pass":{"strict_pass":False}}]}))
  (p/"f.json").write_text(json.dumps({"reviewers":[{"reviewer_id":"R1","independent":independent,"discipline":"control"}],"tasks":tasks}))
  return calculate(p/"b.json",p/"f.json")
 def test_valid_final_pass_after_repair_counts_without_changing_first_pass(self):
  r=self.calc([good_task()])
  self.assertEqual(r["first_pass"]["rate"],0)
  self.assertEqual(r["final_delivery"]["accepted_after_repair"],1)
  self.assertEqual(r["final_delivery"]["rate_among_completed"],1)
 def test_missing_evidence_or_hard_fail_clearance_does_not_count(self):
  t=good_task();t["dimension_evidence"]["science"]=""
  r=self.calc([t])
  self.assertEqual(r["final_delivery"]["accepted"],0)
  self.assertTrue(r["final_delivery"]["invalid_completed_reviews"])
 def test_not_independent_reviewer_does_not_count(self):
  t=good_task()
  # The registered reviewer exists but is explicitly not independent.
  r=self.calc([t],independent=False)
  self.assertEqual(r["final_delivery"]["accepted"],0)
 def test_pending_reviews_are_not_zero_rate(self):
  t=good_task();t["final_review_status"]="pending"
  r=self.calc([t])
  self.assertIsNone(r["final_delivery"]["rate_among_completed"])
  self.assertEqual(r["final_delivery"]["status"],"NOT_YET_MEASURABLE")
 def test_dimension_under_two_fails_even_if_final_decision_says_pass(self):
  t=good_task();t["dimension_scores"]["visual_quality"]=1
  r=self.calc([t])
  self.assertEqual(r["final_delivery"]["accepted"],0)

if __name__=="__main__":unittest.main()
