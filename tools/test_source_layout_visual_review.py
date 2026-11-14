"""Visual-candidate review tests for P1-01B/P1-01C."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from source_layout_review import create_source_layout_review_template, validate_source_layout_review


def write_layout(path):
    layout={
        "schema_version":"1.1.0",
        "source":{"filename":"paper.pdf","sha256":"a"*64,"page_index":0},
        "figure_region_pt":[0.0,0.0,400.0,300.0],
        "panel_detection":{
            "unlabeled_panel_candidates":[],
            "alignment_groups":[],
            "raster_gutter_candidates":[],
            "visual_region_candidates":[{
                "id":"visual_region_001",
                "candidate_type":"visual_region",
                "model_label":"image",
                "model_score":0.96,
                "bbox_pt":[20.0,20.0,180.0,180.0],
                "bbox_normalized":[0.05,0.066667,0.4,0.533333],
                "parent_candidate_id":None,
                "depth":0,
                "source_object_ids":["image_1"],
                "owned_source_object_ids":["image_1"],
                "source_object_count":1,
                "ownership_coverage":1.0,
                "confidence_score":0.972,
                "confidence":"high",
                "confidence_basis":"heuristic proposal",
                "review_status":"needs_human_review",
                "needs_human_review":True,
                "evidence_source":"paddleocr_layout_detection"
            }],
            "ocr_panel_markers":[{
                "id":"ocr_marker_001","label":"a","text":"(a)",
                "marker_style":"parenthesized","ocr_score":0.98,
                "bbox_pt":[25.0,25.0,35.0,35.0],"bbox_normalized":[0.0625,0.0833,0.025,0.0333],
                "candidate_type":"ocr_panel_marker","confidence":"high",
                "confidence_basis":"OCR candidate","needs_human_review":True,
                "anchor_status":"ANCHORED_CANDIDATE","matched_region_candidate_id":"visual_region_001"
            }],
            "panel_hypotheses":[{
                "id":"panel_hypothesis_a_001","candidate_id":"visual_region_001",
                "candidate_type":"label_anchored_visual_region",
                "region_candidate_id":"visual_region_001","marker_candidate_id":"ocr_marker_001",
                "label":"a","marker_text":"(a)","bbox_pt":[20.0,20.0,180.0,180.0],
                "bbox_normalized":[0.05,0.066667,0.4,0.533333],
                "confidence_score":0.97,"confidence":"high",
                "confidence_basis":"label anchor","needs_human_review":True,
                "review_status":"needs_human_review"
            }],
            "visual_alignment_groups":[]
        }
    }
    path.write_text(json.dumps(layout,indent=2),encoding="utf-8")


class VisualCandidateReviewTests(unittest.TestCase):
    def test_visual_region_can_be_human_accepted_as_panel(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); layout_path=root/"layout.json"; review_path=root/"review.json"
            write_layout(layout_path)
            review=create_source_layout_review_template(layout_path,review_path)
            self.assertEqual([d["candidate_id"] for d in review["decisions"]],
                             ["panel_hypothesis_a_001","visual_region_001"])
            review["reviewer"]={"name":"domain reviewer","type":"human"}
            item=next(d for d in review["decisions"] if d["candidate_id"]=="panel_hypothesis_a_001")
            item.update({"decision":"accept_panel","rationale":"The marker and region align with the source panel.",
                         "evidence_locator":"Figure 1(a), page 1"})
            review_path.write_text(json.dumps(review),encoding="utf-8")
            audit=validate_source_layout_review(layout_path,review_path)
            self.assertEqual(audit["status"],"VALIDATED_WITH_ACCEPTED_FACTS")
            self.assertEqual(audit["accepted_panel_count"],1)
            self.assertEqual(audit["accepted_source_panels"][0]["candidate_type"],
                             "label_anchored_visual_region")

    def test_visual_region_split_produces_geometric_regions_not_panels(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); layout_path=root/"layout.json"; review_path=root/"review.json"
            write_layout(layout_path)
            review=create_source_layout_review_template(layout_path,review_path)
            review["reviewer"]={"name":"domain reviewer","type":"human"}
            item=next(d for d in review["decisions"] if d["candidate_id"]=="visual_region_001")
            item.update({"decision":"split_region","split_axis":"vertical","split_position_pt":100.0,
                         "rationale":"A visible gutter divides the raster region.",
                         "evidence_locator":"Figure 1, page 1"})
            review_path.write_text(json.dumps(review),encoding="utf-8")
            audit=validate_source_layout_review(layout_path,review_path)
            self.assertEqual(audit["status"],"VALIDATED_WITH_ACCEPTED_FACTS")
            self.assertEqual(audit["split_region_count"],1)
            self.assertEqual(len(audit["accepted_source_layout_regions"]),2)
            self.assertEqual(audit["accepted_panel_count"],0)

    def test_raw_ocr_markers_are_never_reviewable_or_promoted(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); layout_path=root/"layout.json"; review_path=root/"review.json"
            write_layout(layout_path)
            review=create_source_layout_review_template(layout_path,review_path)
            ids={d["candidate_id"] for d in review["decisions"]}
            self.assertNotIn("ocr_marker_001",ids)
            self.assertNotIn("visual_alignment_001",ids)


if __name__=="__main__":
    unittest.main()
