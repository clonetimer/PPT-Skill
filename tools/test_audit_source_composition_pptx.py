"""Tests for imported PPTX source-object provenance and fidelity audit."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

from audit_source_composition_pptx import audit_imported_pptx_against_composition
from pdf_figure_import import _annotate_source_shape


def make_manifest(path):
    manifest={
        "schema_version":"1.0.0",
        "status":"COMPOSITION_PLAN_READY",
        "policy":{"execution_authorized":False},
        "composition_units":[{
            "unit_id":"panel_a",
            "objects":[
                {"source_object_id":"draw_1","source_order":1,"object_class":"vector","treatment":"editable_vector"},
                {"source_object_id":"text_0_0_0","source_order":None,"object_class":"text","treatment":"editable_text"},
                {"source_object_id":"image_2","source_order":2,"object_class":"image","treatment":"picture_asset"},
            ]
        }]
    }
    path.write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    return manifest


def make_pptx(path, *, omit=(), duplicate=(), wrong_class=()):
    prs=Presentation()
    slide=prs.slides.add_slide(prs.slide_layouts[6])
    if "draw_1" not in omit:
        shape=slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1), Inches(1), Inches(1), Inches(1))
        _annotate_source_shape(shape,"draw_1",1,"vector")
    if "text_0_0_0" not in omit:
        shape=slide.shapes.add_textbox(Inches(1), Inches(2), Inches(1), Inches(.3))
        shape.text="label"
        _annotate_source_shape(shape,"text_0_0_0",None,"text")
    if "image_2" not in omit:
        if "image_2" in wrong_class:
            shape=slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(2), Inches(2), Inches(1), Inches(1))
            _annotate_source_shape(shape,"image_2",2,"image")
        else:
            from PIL import Image
            import io
            buffer=io.BytesIO()
            Image.new("RGB",(4,4),"white").save(buffer,format="PNG")
            buffer.seek(0)
            shape=slide.shapes.add_picture(buffer, Inches(2), Inches(2), Inches(1), Inches(1))
            _annotate_source_shape(shape,"image_2",2,"image")
    for object_id in duplicate:
        shape=slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(3), Inches(3), Inches(1), Inches(1))
        _annotate_source_shape(shape,object_id,1,"vector")
    prs.save(path)


class SourceCompositionPptxAuditTests(unittest.TestCase):
    def test_valid_import_matches_object_identity_class_and_order(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); manifest=root/"manifest.json"; pptx=root/"figure.pptx"
            make_manifest(manifest); make_pptx(pptx)
            result=audit_imported_pptx_against_composition(manifest,pptx)
        self.assertEqual(result["status"],"PASS")
        self.assertEqual(result["expected_source_order"],["draw_1","image_2"])
        self.assertEqual(result["actual_source_order"],["draw_1","image_2"])
        self.assertFalse(result["policy"]["visual_fidelity_verified"])

    def test_missing_and_duplicate_objects_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); manifest=root/"manifest.json"; pptx=root/"figure.pptx"
            make_manifest(manifest); make_pptx(pptx,omit=("image_2",),duplicate=("draw_1",))
            result=audit_imported_pptx_against_composition(manifest,pptx)
        self.assertEqual(result["status"],"FAIL")
        self.assertIn("image_2",result["missing_source_object_ids"])
        self.assertIn("draw_1",result["duplicate_source_object_ids"])

    def test_picture_expected_but_vector_returned_fails_class_check(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); manifest=root/"manifest.json"; pptx=root/"figure.pptx"
            make_manifest(manifest); make_pptx(pptx,wrong_class=("image_2",))
            result=audit_imported_pptx_against_composition(manifest,pptx)
        self.assertEqual(result["status"],"FAIL")
        self.assertIn("OBJECT_CLASS_MISMATCH",result["failures"])

    def test_blocked_manifest_cannot_be_used(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); manifest=root/"manifest.json"; pptx=root/"figure.pptx"
            value=make_manifest(manifest); value["status"]="BLOCKED"
            manifest.write_text(json.dumps(value),encoding="utf-8")
            make_pptx(pptx)
            with self.assertRaisesRegex(ValueError,"COMPOSITION_MANIFEST_NOT_EXECUTABLE"):
                audit_imported_pptx_against_composition(manifest,pptx)


if __name__=="__main__":
    unittest.main()
