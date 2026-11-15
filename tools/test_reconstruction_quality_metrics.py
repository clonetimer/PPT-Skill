"""Tests for multi-dimensional source reconstruction quality metrics."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches

from pdf_figure_import import _annotate_source_shape
from reconstruction_quality_metrics import evaluate_reconstruction_quality


def make_manifest(path,*,crop=(0,0,300,200),text="Alpha β",image_hash="image-hash",image_transform=[60,0,0,60,120,20],pixel_size=[4,4]):
    manifest={
        "status":"COMPOSITION_PLAN_READY",
        "source":{"figure_region_pt":list(crop)},
        "policy":{"execution_authorized":False},
        "composition_units":[{
            "unit_id":"panel_a",
            "objects":[
                {"source_object_id":"draw_1","source_order":1,"object_class":"vector","treatment":"editable_vector","bbox_pt":[10,10,70,70]},
                {"source_object_id":"text_0_0_0","source_order":None,"object_class":"text","treatment":"editable_text","text":text,"bbox_pt":[20,80,100,100]},
                {"source_object_id":"image_2","source_order":2,"object_class":"image","treatment":"picture_asset","bbox_pt":[120,20,180,80],"source_image_sha256":image_hash,"source_image_transform":image_transform,"source_image_pixel_size":pixel_size},
            ]
        }]
    }
    path.write_text(json.dumps(manifest),encoding="utf-8")
    return manifest


def make_pptx(path,*,text="Alpha β",order=("draw_1","image_2","text_0_0_0"),omit=(),image_hash="image-hash",image_transform=[60,0,0,60,120,20],pixel_size=[4,4]):
    prs=Presentation();slide=prs.slides.add_slide(prs.slide_layouts[6])
    for object_id in order:
        if object_id in omit: continue
        if object_id=="draw_1":
            shape=slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(10/72),Inches(10/72),Inches(60/72),Inches(60/72))
            _annotate_source_shape(shape,object_id,1,"vector")
        elif object_id=="image_2":
            from PIL import Image
            import io
            data=io.BytesIO();Image.new("RGB",(4,4),"white").save(data,format="PNG");data.seek(0)
            shape=slide.shapes.add_picture(data,Inches(120/72),Inches(20/72),Inches(60/72),Inches(60/72))
            _annotate_source_shape(shape,object_id,2,"image",{"source_image_sha256":image_hash,"source_image_transform":image_transform,"source_image_pixel_size":pixel_size})
        else:
            shape=slide.shapes.add_textbox(Inches(20/72),Inches(80/72),Inches(80/72),Inches(20/72))
            shape.text=text
            _annotate_source_shape(shape,object_id,None,"text")
    prs.save(path)


class ReconstructionQualityMetricsTests(unittest.TestCase):
    def test_reports_separate_metrics_and_full_page_geometry(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); manifest=root/"manifest.json"; pptx=root/"figure.pptx"
            make_manifest(manifest);make_pptx(pptx)
            result=evaluate_reconstruction_quality(manifest,pptx)
        self.assertEqual(result["status"],"NEEDS_REVIEW")
        self.assertEqual(result["object_preservation"]["source_object_recall"],1.0)
        self.assertEqual(result["text_fidelity"]["character_error_rate"],0.0)
        self.assertEqual(result["source_order"]["kendall_tau"],1.0)
        self.assertEqual(result["geometry_fidelity"]["status"],"COMPARABLE_FULL_PAGE_ORIGIN")
        self.assertFalse(result["policy"]["single_blended_score_emitted"])

    def test_text_mutation_increases_cer_without_hiding_object_recall(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); manifest=root/"manifest.json"; pptx=root/"figure.pptx"
            make_manifest(manifest,text="Alpha beta");make_pptx(pptx,text="Alpha zeta")
            result=evaluate_reconstruction_quality(manifest,pptx)
        self.assertEqual(result["object_preservation"]["source_object_recall"],1.0)
        self.assertGreater(result["text_fidelity"]["character_error_rate"],0.0)

    def test_crop_geometry_is_explicitly_not_comparable(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);manifest=root/"manifest.json";pptx=root/"figure.pptx"
            make_manifest(manifest,crop=(20,30,320,230));make_pptx(pptx)
            result=evaluate_reconstruction_quality(manifest,pptx)
        self.assertEqual(result["geometry_fidelity"]["status"],"NOT_COMPARABLE_CROP_OR_UNKNOWN_TRANSFORM")
        self.assertEqual(result["geometry_fidelity"]["mean_bbox_iou"],None)

    def test_raster_identity_dimensions_and_transform_are_compared(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);manifest=root/"manifest.json";pptx=root/"figure.pptx"
            make_manifest(manifest);make_pptx(pptx)
            result=evaluate_reconstruction_quality(manifest,pptx)
        raster=result["raster_fidelity"]["assets"][0]
        self.assertEqual(raster["status"],"COMPARED")
        self.assertEqual(raster["asset_hash_status"],"MATCH")
        self.assertEqual(raster["pixel_size_status"],"MATCH")
        self.assertEqual(raster["transform_status"],"MATCH")

    def test_raster_mutation_is_reported_as_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);manifest=root/"manifest.json";pptx=root/"figure.pptx"
            make_manifest(manifest);make_pptx(pptx,image_hash="altered-image-hash")
            result=evaluate_reconstruction_quality(manifest,pptx)
        self.assertEqual(result["status"],"FAIL")
        self.assertIn("RASTER_SOURCE_IDENTITY_OR_TRANSFORM_MISMATCH",result["blockers"])

    def test_missing_source_object_is_a_fail_not_a_lower_blended_score(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);manifest=root/"manifest.json";pptx=root/"figure.pptx"
            make_manifest(manifest);make_pptx(pptx,omit=("image_2",))
            result=evaluate_reconstruction_quality(manifest,pptx)
        self.assertEqual(result["status"],"FAIL")
        self.assertIn("MISSING_SOURCE_OBJECTS",result["blockers"])
        self.assertIn("image_2",result["object_preservation"]["missing_object_ids"])


if __name__=="__main__":
    unittest.main()
