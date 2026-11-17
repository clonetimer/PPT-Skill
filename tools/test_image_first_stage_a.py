#!/usr/bin/env python3
"""Regression tests for Image-first Stage-A target recording and review."""
from __future__ import annotations
import json,shutil,tempfile,unittest
from pathlib import Path
from PIL import Image
from create_image_first_manifest import create_manifest
from record_image_first_target import record_target
from review_image_first_target import record_review
from validate_image_first_workflow import validate_manifest
ROOT=Path(__file__).resolve().parents[1]
CHECKS=["scientific_content","exact_text","source_fidelity","visual_hierarchy","projection_readability","reconstruction_feasibility"]
class StageATargetReviewTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  for n in ("specs","prompts","docs"):(self.root/n).mkdir()
  shutil.copy2(ROOT/"specs/image_first_workflow_v8.schema.json",self.root/"specs/image_first_workflow_v8.schema.json")
  shutil.copy2(ROOT/"prompts/image2_slide_prompt_template.md",self.root/"prompts/image2_slide_prompt_template.md")
  (self.root/"docs/source.md").write_text("Source evidence.",encoding="utf-8")
  deck={"schema_version":"7.6.0-dev","deck":{"topic":"Stage-A test","audience":"research committee","style_ref":"restrained_academic"},
        "slides":[{"id":"s01","role":"method","claim":"The method has two linked stages.",
        "evidence":[{"source":"docs/source.md","status":"source_visible"}],"layout":"left_to_right_process","figure_ref":None,
        "on_slide":["Two-stage method","Stage A","Stage B"],"speaker_notes":"Presenter-only notes."}]}
  self.deck_path=self.root/"specs/deck.json";self.deck_path.write_text(json.dumps(deck,indent=2),encoding="utf-8")
  self.output_dir=self.root/"dist/image_first/s01";_,self.manifest_path=create_manifest(self.deck_path,"s01",self.output_dir,root=self.root)
  self.image_path=self.output_dir/"target.png"
 def tearDown(self):self.temp.cleanup()
 def _make_image(self,size=(1920,1080)):Image.new("RGB",size,"white").save(self.image_path,format="PNG")
 def test_record_target_hashes_image_and_moves_stage_to_generated(self):
  self._make_image();r=record_target(self.manifest_path,self.image_path,self.root);m=json.loads(self.manifest_path.read_text())
  self.assertEqual(r["iteration"],1);self.assertEqual(m["stage_a"]["status"],"generated")
  self.assertEqual(m["stage_a"]["target_image"]["width_px"],1920);self.assertEqual(m["stage_a"]["target_image"]["height_px"],1080)
  self.assertEqual(validate_manifest(self.manifest_path,self.root,self.root/"specs/image_first_workflow_v8.schema.json")["stage"],"STAGE_A_REVIEW_OR_RECONSTRUCTION_READY")
 def test_wrong_dimensions_are_rejected(self):
  self._make_image((1672,941))
  with self.assertRaisesRegex(ValueError,"TARGET_IMAGE_DIMENSIONS_MUST_BE_1920x1080"):record_target(self.manifest_path,self.image_path,self.root)
 def test_revision_review_records_issues_and_keeps_stage_b_blocked(self):
  self._make_image();record_target(self.manifest_path,self.image_path,self.root)
  r=record_review(self.manifest_path,"revise","assistant visual triage","assistant_visual_triage",["exact_text","source_fidelity"],
                  ["Frequency axis direction is wrong.","Input-to-EA branch is missing."])
  m=json.loads(self.manifest_path.read_text());self.assertEqual(r["stage_a_status"],"needs_revision")
  self.assertEqual(m["stage_b"]["status"],"not_started");self.assertEqual(len(m["stage_a"]["review"]["issues"]),2)
  self.assertEqual(validate_manifest(self.manifest_path,self.root,self.root/"specs/image_first_workflow_v8.schema.json")["stage"],"STAGE_A_REVIEW_OR_RECONSTRUCTION_READY")
 def test_approval_requires_human_and_all_six_checks(self):
  self._make_image();record_target(self.manifest_path,self.image_path,self.root)
  with self.assertRaisesRegex(ValueError,"STAGE_A_APPROVAL_REQUIRES_HUMAN_REVIEWER"):record_review(self.manifest_path,"approve","assistant","assistant_visual_triage",CHECKS)
  with self.assertRaisesRegex(ValueError,"STAGE_A_APPROVAL_CHECKS_INCOMPLETE"):record_review(self.manifest_path,"approve","reviewer","human",CHECKS[:-1])
  r=record_review(self.manifest_path,"approve","domain reviewer","human",CHECKS);self.assertEqual(r["stage_a_status"],"approved")
  self.assertEqual(validate_manifest(self.manifest_path,self.root,self.root/"specs/image_first_workflow_v8.schema.json")["stage"],"STAGE_A_REVIEW_OR_RECONSTRUCTION_READY")
 def test_approved_target_cannot_be_replaced_without_new_workflow(self):
  self._make_image();record_target(self.manifest_path,self.image_path,self.root);record_review(self.manifest_path,"approve","domain reviewer","human",CHECKS)
  with self.assertRaisesRegex(ValueError,"CANNOT_REPLACE_APPROVED_STAGE_A_TARGET"):record_target(self.manifest_path,self.image_path,self.root)
if __name__=="__main__":unittest.main()
