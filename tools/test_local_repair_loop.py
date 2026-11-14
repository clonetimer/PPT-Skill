import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches
from pdf_figure_import import _annotate_source_shape
from local_repair_loop import run_repair_loop

def make_inputs(root):
 source=root/"first.pptx";manifest=root/"manifest.json";plan=root/"plan.json"
 prs=Presentation();slide=prs.slides.add_slide(prs.slide_layouts[6])
 shape=slide.shapes.add_textbox(Inches(1),Inches(1),Inches(2),Inches(.5));shape.text="Label"
 _annotate_source_shape(shape,"text_1",None,"text")
 prs.save(source)
 manifest.write_text(json.dumps({"status":"COMPOSITION_PLAN_READY","policy":{"execution_authorized":False},
 "composition_units":[{"objects":[{"source_object_id":"text_1","source_order":None,"object_class":"text","treatment":"editable_text","text":"Label","bbox_pt":[72,72,216,108]}]}]}))
 plan.write_text(json.dumps({"rounds":[{"operations":[{"source_object_id":"text_1","operation":"move","left_emu":914400,"top_emu":1097280}]}]}))
 return source,manifest,plan

class LocalRepairLoopTests(unittest.TestCase):
 def test_round_artifact_diff_and_first_pass_are_preserved(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);source,manifest,plan=make_inputs(root);out=root/"rounds"
   fake={"status":"NEEDS_REVIEW","object_preservation":{"source_object_recall":1.0,"duplicate_object_ids":[],"missing_object_ids":[]},"blockers":[]}
   with patch("reconstruction_quality_metrics.evaluate_reconstruction_quality",return_value=fake):
    report=run_repair_loop(source,plan,manifest,out)
   self.assertTrue((out/"first_pass.pptx").exists())
   self.assertTrue((out/"round_01.pptx").exists())
   self.assertTrue((out/"repair_history.json").exists())
   self.assertEqual(report["accepted_rounds"],1)
   self.assertTrue(report["repair_history"][0]["object_diff"])
   self.assertNotEqual(report["first_pass_sha256"],report["final_sha256"])
 def test_failed_quality_audit_rejects_round_and_keeps_previous_candidate(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);source,manifest,plan=make_inputs(root);out=root/"rounds"
   bad={"status":"FAIL","object_preservation":{"source_object_recall":0.0,"duplicate_object_ids":[],"missing_object_ids":["text_1"]},"blockers":["MISSING_SOURCE_OBJECTS"]}
   with patch("reconstruction_quality_metrics.evaluate_reconstruction_quality",return_value=bad):
    report=run_repair_loop(source,plan,manifest,out)
   self.assertEqual(report["accepted_rounds"],0)
   self.assertEqual(report["rejected_rounds"],1)
   self.assertEqual(report["first_pass_sha256"],report["final_sha256"])
   self.assertTrue((out/"round_01.pptx").exists())
   self.assertEqual(report["repair_history"][0]["candidate_status"],"REJECTED_BUT_PRESERVED_FOR_AUDIT")
 def test_unknown_source_object_fails_closed(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);source,manifest,plan=make_inputs(root)
   plan.write_text(json.dumps({"rounds":[{"operations":[{"source_object_id":"missing","operation":"rotate","rotation_degrees":45}]}]}))
   with patch("reconstruction_quality_metrics.evaluate_reconstruction_quality",return_value={"status":"NEEDS_REVIEW","object_preservation":{"source_object_recall":1,"duplicate_object_ids":[],"missing_object_ids":[]},"blockers":[]}):
    with self.assertRaisesRegex(ValueError,"UNKNOWN_REPAIR_SOURCE_OBJECT"):
     run_repair_loop(source,plan,manifest,root/"rounds")
 def test_text_repair_preserves_existing_font_run(self):
  from pptx.util import Pt
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);source,manifest,plan=make_inputs(root)
   prs=Presentation(source)
   shape=prs.slides[0].shapes[0]
   shape.text_frame.paragraphs[0].runs[0].font.size=Pt(15)
   shape.text_frame.paragraphs[0].runs[0].font.bold=True
   from local_repair_loop import apply_operation
   apply_operation(shape,{"operation":"set_text","expected_text":"Label","text":"Label revised"})
   self.assertEqual(shape.text,"Label revised")
   run=shape.text_frame.paragraphs[0].runs[0]
   self.assertAlmostEqual(run.font.size.pt,15,places=1)
   self.assertTrue(run.font.bold)
 def test_text_repair_with_multiple_format_runs_fails_closed(self):
  from local_repair_loop import apply_operation
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);source,manifest,plan=make_inputs(root)
   prs=Presentation(source);shape=prs.slides[0].shapes[0]
   shape.text_frame.paragraphs[0].add_run().text=" second"
   with self.assertRaisesRegex(ValueError,"MULTIRUN_TEXT_REPAIR_REQUIRES_MANUAL_REVIEW"):
    apply_operation(shape,{"operation":"set_text","expected_text":"Label second","text":"replaced"})
 def test_existing_repair_round_is_not_overwritten(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);source,manifest,plan=make_inputs(root);out=root/"rounds"
   fake={"status":"NEEDS_REVIEW","object_preservation":{"source_object_recall":1.0,"duplicate_object_ids":[],"missing_object_ids":[]},"blockers":[]}
   with patch("reconstruction_quality_metrics.evaluate_reconstruction_quality",return_value=fake):
    first=run_repair_loop(source,plan,manifest,out)
    previous=(out/"round_01.pptx").read_bytes()
    with self.assertRaisesRegex(ValueError,"REPAIR_ROUND_ARTIFACT_IMMUTABLE"):
     run_repair_loop(source,plan,manifest,out)
   self.assertEqual((out/"round_01.pptx").read_bytes(),previous)

if __name__=="__main__":unittest.main()
