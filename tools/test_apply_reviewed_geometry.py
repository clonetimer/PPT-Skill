"""Constrain FigureSpec geometry from reviewed SourceLayout without inventing science."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from source_layout_review import create_source_layout_review_template
from source_layout_constraints import compile_reviewed_layout_constraints
from apply_reviewed_geometry import apply_reviewed_geometry
from test_source_layout_review import write_layout


def create_inputs(root):
    layout=write_layout(root)
    review_path=root/"review.json"
    review=create_source_layout_review_template(layout,review_path)
    review["reviewer"]={"name":"human domain reviewer","type":"human"}
    d=next(d for d in review["decisions"] if d["candidate_id"]=="rect_candidate_01")
    d.update({"decision":"accept_panel","rationale":"enclosed panel source","evidence_locator":"source Fig 2 page 3"})
    review_path.write_text(json.dumps(review),encoding="utf-8")
    constraints=root/"constraints.json"
    compile_reviewed_layout_constraints(layout,review_path,constraints)
    spec_path=root/"figure.json"
    spec={
        "schema_version":"7.6.0-dev","id":"example",
        "canvas":{"width_in":8,"height_in":6},
        "style":{"font":"Arial"},
        "semantic_edges":[["a","b"]],
        "elements":[
            {"id":"panel-a","type":"rect","x":.2,"y":.3,"w":2,"h":.5,
             "stroke":"#123456","fill":"#FFFFFF","semantic_id":"a"},
            {"id":"panel-b","type":"rect","x":5,"y":2,"w":1,"h":1,
             "stroke":"#123456","fill":"#EEEEEE","semantic_id":"b"}
        ]
    }
    spec_path.write_text(json.dumps(spec),encoding="utf-8")
    binding_path=root/"bindings.json"
    binding={
        "schema_version":"1.0.0",
        "source_constraints_sha256":hashlib.sha256(constraints.read_bytes()).hexdigest(),
        "figure_spec_sha256":hashlib.sha256(spec_path.read_bytes()).hexdigest(),
        "bindings":[{"source_constraint_id":"rect_candidate_01","target_element_id":"panel-a"}]
    }
    binding_path.write_text(json.dumps(binding),encoding="utf-8")
    return spec_path,constraints,binding_path


class GeometryBindingTests(unittest.TestCase):
    def test_moves_only_explicitly_bound_editable_source_panel(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            spec,constraints,bindings=create_inputs(root)
            out=root/"reviewed.json"
            result=apply_reviewed_geometry(spec,constraints,bindings,out)
            self.assertEqual(result["bound_element_count"],1)
            before=json.loads(spec.read_text(encoding="utf-8"))
            after=json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(after["elements"][1],before["elements"][1])
            self.assertEqual(after["semantic_edges"],before["semantic_edges"])
            self.assertEqual([after["elements"][0][key] for key in ("x","y","w","h")],
                             [.4,.4,7.2,2.2])
            self.assertFalse(after["layout_provenance"]["scientific_relations_verified"])

    def test_unknown_or_unreviewed_constraint_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            spec,constraints,bindings=create_inputs(root)
            payload=json.loads(bindings.read_text())
            payload["bindings"][0]["source_constraint_id"]="not_reviewed"
            bindings.write_text(json.dumps(payload))
            out=root/"bad.json"
            with self.assertRaisesRegex(ValueError,"UNKNOWN_REVIEWED_CONSTRAINT"):
                apply_reviewed_geometry(spec,constraints,bindings,out)
            self.assertFalse(out.exists())

    def test_mismatched_source_spec_hash_rejected_and_stale_output_removed(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            spec,constraints,bindings=create_inputs(root)
            out=root/"result.json"
            apply_reviewed_geometry(spec,constraints,bindings,out)
            payload=json.loads(bindings.read_text())
            payload["figure_spec_sha256"]="0"*64
            bindings.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError,"FIGURESPEC_HASH_MISMATCH"):
                apply_reviewed_geometry(spec,constraints,bindings,out)
            self.assertFalse(out.exists())

    def test_duplicate_target_binding_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            spec,constraints,bindings=create_inputs(root)
            payload=json.loads(bindings.read_text())
            payload["bindings"].append(payload["bindings"][0].copy())
            bindings.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError,"DUPLICATE_GEOMETRY_BINDING"):
                apply_reviewed_geometry(spec,constraints,bindings,root/"bad.json")

    def test_unreviewed_raster_separator_is_not_promoted_to_a_panel_shape(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            spec,constraints,bindings=create_inputs(root)
            payload=json.loads(bindings.read_text())
            payload["bindings"][0]["source_constraint_id"]="raster_gutter_01_horizontal_01"
            bindings.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError,"UNKNOWN_REVIEWED_CONSTRAINT"):
                apply_reviewed_geometry(spec,constraints,bindings,root/"bad.json")

    def test_reject_canvas_aspect_ratio_drift_in_source_faithful_mode(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            spec,constraints,bindings=create_inputs(root)
            content=json.loads(spec.read_text())
            content["canvas"]["width_in"]=16
            spec.write_text(json.dumps(content))
            payload=json.loads(bindings.read_text())
            payload["figure_spec_sha256"]=hashlib.sha256(spec.read_bytes()).hexdigest()
            bindings.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError,"SOURCE_ASPECT_RATIO_MISMATCH"):
                apply_reviewed_geometry(spec,constraints,bindings,root/"bad.json")

    def test_never_overwrite_original_spec(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            spec,constraints,bindings=create_inputs(root)
            with self.assertRaisesRegex(ValueError,"REFUSE_TO_OVERWRITE_SOURCE"):
                apply_reviewed_geometry(spec,constraints,bindings,spec)


if __name__=="__main__":
    unittest.main()
