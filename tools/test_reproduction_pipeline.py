"""End-to-end release-gate tests for both PDF import and FigureSpec routes."""
from __future__ import annotations

import io
import json
from pathlib import Path
import tempfile
import unittest

import fitz
from PIL import Image

from reproduce_research_figure import run_pipeline
from reproduction_release_gate import classify_release
from source_layout_review import create_source_layout_review_template


def make_picture_pdf(path: Path):
    doc = fitz.open()
    page = doc.new_page(width=240, height=160)
    image = io.BytesIO()
    Image.new("RGB", (24, 16), (210, 80, 60)).save(image, "PNG")
    page.insert_image(fitz.Rect(30, 30, 210, 130), stream=image.getvalue())
    doc.save(path)
    doc.close()


def make_blank_pdf(path: Path):
    doc = fitz.open()
    doc.new_page(width=240, height=160)
    doc.save(path)
    doc.close()


def make_panel_candidate_pdf(path: Path):
    doc = fitz.open()
    page = doc.new_page(width=300, height=240)
    page.draw_rect(fitz.Rect(30, 25, 270, 95), color=(.1, .2, .4), width=1)
    page.draw_rect(fitz.Rect(30, 135, 270, 210), color=(.4, .2, .1), width=1)
    page.insert_text((40, 55), "upper module", fontsize=10)
    page.insert_text((40, 165), "lower module", fontsize=10)
    doc.save(path)
    doc.close()


def make_vector_pdf(path: Path, drawings: int = 5):
    doc = fitz.open()
    page = doc.new_page(width=240, height=160)
    for i in range(drawings):
        y = 25 + i * 18
        page.draw_line((20, y), (210, y + 5), color=(.1, .2, .4), width=1)
    page.insert_text((30, 145), "source label", fontsize=9)
    doc.save(path)
    doc.close()


def make_figurespec(path: Path, *, edges=True, actual_link="a__b"):
    evidence = {
        "id": "paper-figure-1",
        "source": "user supplied paper",
        "source_file_sha256": "a" * 64,
        "source_locator": "Figure 1",
        "status": "source_visible_redraw",
        "scope": "main method flow",
        "reuse": "derivative_redraw_only",
    }
    elements = [
        {"id": "node-a", "type": "rect", "x": .5, "y": .7, "w": 1.2, "h": .7,
         "fill": "#E8EEF5", "stroke": "#334455", "semantic_id": "a",
         "semantic_role": "scientific_object", "evidence_ref": "paper-figure-1"},
        {"id": "node-b", "type": "rect", "x": 3.0, "y": .7, "w": 1.2, "h": .7,
         "fill": "#E8EEF5", "stroke": "#334455", "semantic_id": "b",
         "semantic_role": "scientific_object", "evidence_ref": "paper-figure-1"},
        {"id": "edge-ab", "type": "line", "x1": 1.7, "y1": 1.05, "x2": 3.0, "y2": 1.05,
         "semantic_link": actual_link, "semantic_role": "connector",
         "evidence_ref": "paper-figure-1"},
        {"id": "label-a", "type": "text", "x": .55, "y": .85, "w": 1.1, "h": .25,
         "text": "Encoder", "size": 11, "semantic_role": "scientific_label",
         "evidence_ref": "paper-figure-1"},
        {"id": "label-b", "type": "text", "x": 3.05, "y": .85, "w": 1.1, "h": .25,
         "text": "Decoder", "size": 11, "semantic_role": "scientific_label",
         "evidence_ref": "paper-figure-1"},
    ]
    spec = {
        "schema_version": "7.6.0-dev",
        "id": "release-gate-fixture",
        "canvas": {"width_in": 5.0, "height_in": 2.0},
        "style": {"font": "Arial"},
        "figure_contract": {
            "claim": "Encoder feeds decoder",
            "archetype": "schematic_led_composite",
            "output_mode": "publication",
            "unverified": [],
        },
        "evidence_records": [evidence],
        "semantic_edges": [["a", "b"]] if edges else [],
        "elements": elements,
    }
    path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")


class ReproductionPipelineReleaseTests(unittest.TestCase):
    def test_blank_source_writes_structural_fail_manifest_without_candidate(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "blank.pdf"
            output = root / "out"
            make_blank_pdf(source)
            result = run_pipeline(source, output, mode="import", render_host="none")
            manifest = json.loads((output / "delivery_manifest.json").read_text())
            self.assertEqual(result["status"], "STRUCTURE_FAIL")
            self.assertEqual(manifest["status"], "STRUCTURE_FAIL")
            self.assertFalse((output / "candidate_editable.pptx").exists())
            self.assertFalse(manifest["final_release_approved"])

    def test_picture_only_import_is_not_counted_as_native_editable_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "picture.pdf"
            output = root / "out"
            make_picture_pdf(source)
            result = run_pipeline(source, output, mode="import", render_host="none")
            manifest = json.loads((output / "delivery_manifest.json").read_text())
            self.assertEqual(result["status"], "UNSUPPORTED_SOURCE")
            self.assertEqual(manifest["reconstruction_class"], "source_picture_only")
            self.assertEqual(manifest["source_route_recommendation"]["recommended_reconstruction_class"],
                             "source_picture_only")
            self.assertFalse(manifest["final_release_approved"])

    def test_resource_limit_is_recorded_and_no_partial_pptx_is_left(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "dense.pdf"
            output = root / "out"
            make_vector_pdf(source, drawings=5)
            result = run_pipeline(
                source, output, mode="import", render_host="none", max_drawings=2
            )
            manifest = json.loads((output / "delivery_manifest.json").read_text())
            self.assertEqual(result["status"], "RESOURCE_LIMIT")
            self.assertIn("RESOURCE_LIMIT", manifest["error"])
            self.assertFalse((output / "candidate_editable.pptx").exists())

    def test_figurespec_without_declared_semantic_edges_requires_science_review(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source.pdf"
            spec = root / "figure.json"
            output = root / "out"
            make_vector_pdf(source, drawings=2)
            make_figurespec(spec, edges=False)
            result = run_pipeline(
                source, output, mode="figurespec", figure_spec=spec, render_host="none"
            )
            manifest = json.loads((output / "delivery_manifest.json").read_text())
            self.assertEqual(result["status"], "NEEDS_SCIENTIFIC_REVIEW")
            self.assertIn("SEMANTIC_RELATION_AUDIT_MISSING", manifest["blockers"])

    def test_figurespec_wrong_semantic_link_fails_even_if_shape_render_succeeds(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source.pdf"
            spec = root / "figure.json"
            output = root / "out"
            make_vector_pdf(source, drawings=2)
            make_figurespec(spec, edges=True, actual_link="a__wrong")
            result = run_pipeline(
                source, output, mode="figurespec", figure_spec=spec, render_host="none"
            )
            manifest = json.loads((output / "delivery_manifest.json").read_text())
            self.assertEqual(result["status"], "NEEDS_SCIENTIFIC_REVIEW")
            self.assertIn("SEMANTIC_RELATION_FAILURE", manifest["blockers"])

    def test_figurespec_without_visual_export_never_claims_technical_or_full_acceptance(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source.pdf"
            spec = root / "figure.json"
            output = root / "out"
            make_vector_pdf(source, drawings=2)
            make_figurespec(spec, edges=True)
            result = run_pipeline(
                source, output, mode="figurespec", figure_spec=spec, render_host="none"
            )
            self.assertEqual(result["status"], "NEEDS_VISUAL_REVIEW")

    def test_pipeline_emits_source_layout_evidence_before_conversion(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source.pdf"
            output = root / "out"
            make_vector_pdf(source, drawings=2)
            result = run_pipeline(source, output, mode="import", render_host="none")
            layout = json.loads((output / "source_layout.json").read_text())
            manifest = json.loads((output / "delivery_manifest.json").read_text())
            self.assertEqual(layout["source"]["sha256"], manifest["source"]["sha256"])
            self.assertIn("panel_detection", layout)
            self.assertIn("source_layout", manifest)
            self.assertEqual(manifest["source_layout"]["path"], str(output / "source_layout.json"))

    def test_pipeline_records_pending_human_layout_review_without_promoting_candidates(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source.pdf"
            output = root / "out"
            review_path = root / "source_layout_review.json"
            make_vector_pdf(source, drawings=2)
            run_pipeline(source, output, mode="import", render_host="none")
            create_source_layout_review_template(output / "source_layout.json", review_path)
            result = run_pipeline(
                source, output, mode="import", render_host="none",
                source_layout_review=review_path,
            )
            manifest = json.loads((output / "delivery_manifest.json").read_text())
            self.assertEqual(result["source_layout_review"]["status"], "REVIEW_PENDING")
            self.assertEqual(manifest["accepted_source_layout_facts"], {"regions": [], "panels": []})
            self.assertEqual(manifest["source_route_recommendation"]["recommended_reconstruction_class"],
                             "native_only")
            self.assertTrue((output / "source_layout_review_audit.json").exists())
            self.assertIsNone(manifest["source_layout_constraints"])
            self.assertFalse((output / "source_layout_constraints.json").exists())

    def test_pipeline_consumes_only_human_accepted_source_layout_facts(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "panels.pdf"
            output = root / "out"
            review_path = root / "source_layout_review.json"
            make_panel_candidate_pdf(source)
            run_pipeline(source, output, mode="import", render_host="none")
            layout = json.loads((output / "source_layout.json").read_text())
            candidates = layout["panel_detection"]["unlabeled_panel_candidates"]
            self.assertTrue(candidates)
            review = create_source_layout_review_template(output / "source_layout.json", review_path)
            review["reviewer"] = {"name": "domain reviewer", "type": "human"}
            decision = next(x for x in review["decisions"] if x["candidate_id"] == candidates[0]["id"])
            decision["decision"] = "accept_panel"
            decision["rationale"] = "The source rectangle encloses a labeled method panel."
            decision["evidence_locator"] = "Source PDF page 1, upper module"
            review_path.write_text(json.dumps(review), encoding="utf-8")
            result = run_pipeline(
                source, output, mode="import", render_host="none",
                source_layout_review=review_path,
            )
            manifest = json.loads((output / "delivery_manifest.json").read_text())
            self.assertEqual(result["source_layout_review"]["status"], "VALIDATED_WITH_ACCEPTED_FACTS")
            self.assertEqual(len(manifest["accepted_source_layout_facts"]["panels"]), 1)
            self.assertEqual(manifest["accepted_source_layout_facts"]["panels"][0]["candidate_id"],
                             candidates[0]["id"])
            self.assertEqual(manifest["source_layout_constraints"]["constraint_count"], 1)
            self.assertTrue((output / "source_layout_constraints.json").exists())
            constraints = json.loads((output / "source_layout_constraints.json").read_text())
            self.assertEqual(constraints["constraints"][0]["constraint_type"], "panel_boundary")
            self.assertEqual(constraints["semantic_edge_authorization"], "none")

    def test_invalid_layout_review_fails_before_candidate_generation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source.pdf"
            output = root / "out"
            review_path = root / "source_layout_review.json"
            make_vector_pdf(source, drawings=2)
            run_pipeline(source, output, mode="import", render_host="none")
            review = create_source_layout_review_template(output / "source_layout.json", review_path)
            review["source_layout_sha256"] = "0" * 64
            review_path.write_text(json.dumps(review), encoding="utf-8")
            result = run_pipeline(
                source, output, mode="import", render_host="none",
                source_layout_review=review_path,
            )
            self.assertEqual(result["status"], "STRUCTURE_FAIL")
            self.assertIn("SOURCE_LAYOUT_REVIEW_INVALID", result["error"])
            self.assertFalse((output / "candidate_editable.pptx").exists())
            self.assertFalse((output / "source_layout_constraints.json").exists())

    def test_import_without_visual_export_is_not_technical_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source.pdf"
            output = root / "out"
            make_vector_pdf(source, drawings=2)
            result = run_pipeline(source, output, mode="import", render_host="none")
            self.assertEqual(result["status"], "NEEDS_VISUAL_REVIEW")

    def test_text_geometry_is_mandatory_for_both_routes(self):
        base = dict(
            route="import",
            candidate={"shape_count": 50, "native_vectors": 40, "picture_objects": 0, "full_page_pictures": 0},
            import_report={"reconstruction_class": "native_only"},
            structure={"status": "PASS"},
            visual={"status": "PASS", "requires_visual_review": False,
                    "evidence_type": "source_comparison", "renderer": "test"},
            office={"status": "PASS"},
        )
        missing = classify_release(**base, text_geometry=None)
        self.assertEqual(missing["status"], "STRUCTURE_FAIL")
        self.assertIn("TEXT_GEOMETRY_AUDIT_MISSING", missing["blockers"])

    def test_raster_only_mode_has_explicit_non_native_status(self):
        result = classify_release(
            route="import",
            candidate={"shape_count": 1, "full_page_pictures": 0},
            import_report={"reconstruction_class": "source_picture_only"},
            structure={"status": "PASS"},
            text_geometry={"status": "PASS"},
            office={"status": "PASS"},
            visual={"status": "PASS", "requires_visual_review": False,
                    "evidence_type": "source_comparison", "renderer": "test"},
            require_native=False,
        )
        self.assertEqual(result["status"], "SOURCE_PICTURE_ONLY")
        self.assertFalse(result["full_accepted"])


if __name__ == "__main__":
    unittest.main()
