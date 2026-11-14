"""Only validated source-layout geometry can enter a figure drafting scaffold."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from source_layout_review import create_source_layout_review_template
from source_layout_constraints import compile_reviewed_layout_constraints
from test_source_layout_review import write_layout
from test_source_layout_split_review import _review


class ReviewedLayoutConstraintsTests(unittest.TestCase):
    def test_human_approved_panel_and_separator_generate_geometry_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            layout_path = write_layout(root)
            review_path = root / "review.json"
            output = root / "source_layout_constraints.json"
            review = create_source_layout_review_template(layout_path, review_path)
            review["reviewer"] = {"name": "domain expert", "type": "human"}
            decisions = {d["candidate_id"]: d for d in review["decisions"]}
            decisions["rect_candidate_01"].update({
                "decision": "accept_panel",
                "rationale": "The boundary encloses panel a in the source",
                "evidence_locator": "Figure 4(a), PDF page 3",
            })
            decisions["raster_gutter_01_horizontal_01"].update({
                "decision": "accept_region",
                "rationale": "Whitespace is a visible separator, not a panel",
                "evidence_locator": "Figure 4, PDF page 3",
            })
            review_path.write_text(json.dumps(review), encoding="utf-8")
            result = compile_reviewed_layout_constraints(layout_path, review_path, output)
            self.assertEqual(result["status"], "REVIEWED_GEOMETRIC_CONSTRAINTS")
            self.assertEqual(result["source_panel_constraint_count"], 1)
            self.assertEqual(result["region_constraint_count"], 1)
            self.assertEqual(len(result["constraints"]), 2)
            self.assertTrue(output.exists())
            self.assertTrue(all(x["scientific_relations_verified"] is False for x in result["constraints"]))
            self.assertTrue(any(x["constraint_type"] == "separator_hint" for x in result["constraints"]))
            self.assertTrue(any(x["constraint_type"] == "panel_boundary" for x in result["constraints"]))

    def test_approved_split_generates_two_region_constraints_not_semantic_panels(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            layout, review = _review(root, location=95)
            output = root / "constraints.json"
            result = compile_reviewed_layout_constraints(layout, review, output)
            self.assertEqual(result["source_panel_constraint_count"], 0)
            self.assertEqual(result["region_constraint_count"], 2)
            boxes = [c["bbox_pt"] for c in result["constraints"]]
            self.assertEqual(boxes, [[30.,40.,390.,95.], [30.,95.,390.,150.]])
            self.assertTrue(all(c["constraint_type"] == "region_bounds" for c in result["constraints"]))
            self.assertTrue(all(c["source_candidate_id"] == "rect_candidate_01" for c in result["constraints"]))

    def test_pending_review_does_not_emit_any_constraints(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            layout_path = write_layout(root)
            review_path = root / "review.json"
            output = root / "constraints.json"
            create_source_layout_review_template(layout_path, review_path)
            with self.assertRaisesRegex(ValueError, "REVIEWED_SOURCE_FACTS_REQUIRED"):
                compile_reviewed_layout_constraints(layout_path, review_path, output)
            self.assertFalse(output.exists())

    def test_invalid_review_cannot_emit_prior_output_or_partial_acceptance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            layout, review = _review(root, location=95)
            output = root / "constraints.json"
            compile_reviewed_layout_constraints(layout, review, output)
            self.assertTrue(output.exists())
            contents = json.loads(review.read_text(encoding="utf-8"))
            contents["source_layout_sha256"] = "0" * 64
            review.write_text(json.dumps(contents), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "INVALID_SOURCE_LAYOUT_REVIEW"):
                compile_reviewed_layout_constraints(layout, review, output)
            self.assertFalse(output.exists())

    def test_output_carries_pdf_and_review_hash_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            layout, review = _review(root, axis="vertical", location=200)
            output = root / "constraints.json"
            result = compile_reviewed_layout_constraints(layout, review, output)
            self.assertEqual(len(result["source_layout_sha256"]), 64)
            self.assertEqual(len(result["review_file_sha256"]), 64)
            self.assertEqual(result["source"]["sha256"], "a" * 64)
            self.assertEqual(result["source"]["figure_region_pt"], [10.,20.,410.,320.])
            self.assertEqual(result["semantic_edge_authorization"], "none")


if __name__=="__main__":
    unittest.main()
