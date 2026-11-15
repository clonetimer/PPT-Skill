#!/usr/bin/env python3
"""Regression tests for the Image-first V8 two-stage workflow."""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches

from audit_image_first_reconstruction import inspect_reconstruction
from build_image2_slide_prompt import build_prompt
from compare_image_first_renders import compare_images
from create_image_first_manifest import create_manifest
from validate_image_first_workflow import (
    WorkflowValidationError,
    validate_manifest,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKS = (
    "scientific_content",
    "exact_text",
    "source_fidelity",
    "visual_hierarchy",
    "projection_readability",
    "reconstruction_feasibility",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ImageFirstWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "specs").mkdir()
        (self.root / "prompts").mkdir()
        (self.root / "docs").mkdir()
        shutil.copy2(
            REPO_ROOT / "specs/image_first_workflow_v8.schema.json",
            self.root / "specs/image_first_workflow_v8.schema.json"
        )
        shutil.copy2(
            REPO_ROOT / "prompts/image2_slide_prompt_template.md",
            self.root / "prompts/image2_slide_prompt_template.md"
        )
        (self.root / "docs/source.md").write_text("Source evidence.\n", encoding="utf-8")
        deck = {
            "schema_version": "7.6.0-dev",
            "deck": {"topic": "Test deck", "audience": "research committee",
                     "style_ref": "restrained_academic"},
            "slides": [{
                "id": "s01",
                "role": "method",
                "claim": "The test method has two linked stages.",
                "evidence": [{"source": "docs/source.md", "status": "source_visible"}],
                "layout": "left_to_right_process",
                "figure_ref": None,
                "on_slide": ["Two-stage method", "Stage A", "Stage B"],
                "speaker_notes": "PRIVATE SPEAKER NOTES MUST NOT APPEAR IN THE IMAGE PROMPT."
            }]
        }
        self.deck_path = self.root / "specs/deck.json"
        self.deck_path.write_text(json.dumps(deck, ensure_ascii=False, indent=2), encoding="utf-8")
        self.output_dir = self.root / "dist/image_first/s01"
        self.prompt_path, self.manifest_path = create_manifest(
            self.deck_path, "s01", self.output_dir, root=self.root
        )
        self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.target_path = self.root / "assets/target.png"
        self.preview_path = self.root / "assets/preview.png"
        self.pptx_path = self.root / "assets/reconstructed.pptx"
        self.target_path.parent.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.temp.cleanup()

    def _save(self):
        self.manifest_path.write_text(
            json.dumps(self.manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8"
        )

    def _make_image(self, path: Path, altered: bool = False):
        image = Image.new("RGB", (1920, 1080), "white")
        draw = ImageDraw.Draw(image)
        draw.rectangle((100, 100, 800, 260), outline="#1F4E79", width=8)
        if altered:
            draw.rectangle((1000, 100, 1800, 900), fill="#EAF2F8")
        image.save(path, format="PNG")

    def _approve_stage_a(self):
        self._make_image(self.target_path)
        self.manifest["stage_a"]["status"] = "approved"
        self.manifest["stage_a"]["target_image"] = {
            "path": self.target_path.relative_to(self.root).as_posix(),
            "sha256": digest(self.target_path),
            "width_px": 1920,
            "height_px": 1080,
            "media_type": "image/png"
        }
        self.manifest["stage_a"]["review"] = {
            "decision": "approved",
            "reviewer": {"name": "domain reviewer", "type": "human"},
            "reviewed_at": "2026-11-15T10:00:00+09:00",
            "checks": {key: True for key in CHECKS},
            "issues": []
        }

    def _make_pptx(self, include_all_text=True, full_slide_picture=False):
        deck = Presentation()
        deck.slide_width = Inches(13.333)
        deck.slide_height = Inches(7.5)
        slide = deck.slides.add_slide(deck.slide_layouts[6])
        if full_slide_picture:
            slide.shapes.add_picture(
                str(self.target_path), 0, 0,
                width=deck.slide_width, height=deck.slide_height
            )
        labels = ["Two-stage method", "Stage A", "Stage B"] if include_all_text else ["Two-stage method"]
        for index, label in enumerate(labels):
            shape = slide.shapes.add_textbox(
                Inches(.6), Inches(.5 + index * .7), Inches(5.2), Inches(.42)
            )
            shape.text = label
        rect = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7), Inches(2), Inches(2), Inches(1)
        )
        rect.text = ""
        deck.save(self.pptx_path)

    def _build_reconstructed_stage(self, include_all_text=True, full_slide_picture=False):
        self._approve_stage_a()
        self._make_pptx(include_all_text, full_slide_picture)
        shutil.copy2(self.target_path, self.preview_path)
        inventory, audit = inspect_reconstruction(
            self.pptx_path, 1, self.manifest["content_lock"]["on_slide"]
        )
        audit["office_2016_evidence"] = None
        self.manifest["stage_b"] = {
            "status": "reconstructed",
            "target_image_sha256": digest(self.target_path),
            "pptx": {
                "path": self.pptx_path.relative_to(self.root).as_posix(),
                "sha256": digest(self.pptx_path)
            },
            "rendered_preview": {
                "path": self.preview_path.relative_to(self.root).as_posix(),
                "sha256": digest(self.preview_path),
                "width_px": 1920,
                "height_px": 1080,
                "media_type": "image/png"
            },
            "object_inventory": inventory,
            "parity": None,
            "audit": audit
        }
        self._save()

    def test_prompt_uses_locked_copy_and_never_renders_speaker_notes(self):
        deck = json.loads(self.deck_path.read_text(encoding="utf-8"))
        prompt = build_prompt(deck, deck["slides"][0])
        self.assertIn("Two-stage method", prompt)
        self.assertIn("Stage A", prompt)
        self.assertIn("Stage B", prompt)
        self.assertNotIn("PRIVATE SPEAKER NOTES MUST NOT APPEAR", prompt)
        self.assertIn("Presenter notes intentionally withheld", prompt)

    def test_manifest_builder_creates_stage_a_plan_and_hashed_prompt(self):
        self.assertTrue(self.prompt_path.is_file())
        self.assertTrue(self.manifest_path.is_file())
        self.assertEqual(self.manifest["stage_a"]["status"], "planned")
        self.assertEqual(
            self.manifest["stage_a"]["prompt"]["rendered_asset"]["sha256"],
            digest(self.prompt_path)
        )
        result = validate_manifest(
            self.manifest_path, self.root,
            self.root / "specs/image_first_workflow_v8.schema.json"
        )
        self.assertEqual(result["stage"], "STAGE_A_PLANNED")

    def test_stage_b_cannot_start_before_human_approved_target(self):
        self.manifest["stage_a"]["status"] = "generated"
        self.manifest["stage_a"]["target_image"] = {
            "path": "assets/target.png", "sha256": "a" * 64,
            "width_px": 1920, "height_px": 1080, "media_type": "image/png"
        }
        self.manifest["stage_b"]["status"] = "in_progress"
        self.manifest["stage_b"]["target_image_sha256"] = "a" * 64
        self._save()
        with self.assertRaises(WorkflowValidationError):
            validate_manifest(
                self.manifest_path, self.root,
                self.root / "specs/image_first_workflow_v8.schema.json"
            )

    def test_stage_a_approval_requires_human_and_all_review_checks(self):
        self._approve_stage_a()
        self.manifest["stage_a"]["review"]["reviewer"]["type"] = "assistant_visual_triage"
        self._save()
        with self.assertRaises(WorkflowValidationError):
            validate_manifest(
                self.manifest_path, self.root,
                self.root / "specs/image_first_workflow_v8.schema.json"
            )

    def test_reconstructed_pptx_records_editable_text_and_native_shapes(self):
        self._build_reconstructed_stage()
        result = validate_manifest(
            self.manifest_path, self.root,
            self.root / "specs/image_first_workflow_v8.schema.json"
        )
        self.assertEqual(result["stage"], "STAGE_B_RECONSTRUCTED")
        self.assertEqual(result["audit"]["editable_text_coverage"], 1.0)
        self.assertGreater(result["object_inventory"]["native_shape_objects"], 3)

    def test_missing_required_text_is_reported_not_hidden_by_image_similarity(self):
        self._build_reconstructed_stage(include_all_text=False)
        self.assertEqual(self.manifest["stage_b"]["audit"]["status"], "fail")
        self.assertIn("Stage A", self.manifest["stage_b"]["audit"]["missing_text"])
        result = validate_manifest(
            self.manifest_path, self.root,
            self.root / "specs/image_first_workflow_v8.schema.json"
        )
        self.assertEqual(result["audit"]["status"], "fail")

    def test_full_slide_raster_background_is_a_hard_failure(self):
        self._build_reconstructed_stage(full_slide_picture=True)
        self.assertEqual(
            self.manifest["stage_b"]["audit"]["full_slide_image_backgrounds"], 1
        )
        self.assertEqual(self.manifest["stage_b"]["audit"]["status"], "fail")

    def test_accepted_requires_parity_human_review_and_office_2016_evidence(self):
        self._build_reconstructed_stage()
        parity = compare_images(self.target_path, self.preview_path)
        self.manifest["stage_b"]["status"] = "accepted"
        self.manifest["stage_b"]["parity"] = {
            "target_image_sha256": digest(self.target_path),
            "rendered_preview_sha256": digest(self.preview_path),
            "metrics": parity["metrics"],
            "thresholds": {
                "global_ssim_min": .95,
                "mean_absolute_error_max": .02,
                "dhash_hamming_distance_max": 2
            },
            "human_review": {
                "decision": "approved",
                "reviewer": {"name": "independent reviewer", "type": "human"},
                "reviewed_at": "2026-11-15T11:00:00+09:00",
                "notes": ["Visual parity and final-size readability checked."]
            },
            "method": parity["method"]
        }
        self.manifest["stage_b"]["audit"]["office_2016_roundtrip"] = "passed"
        self._save()
        with self.assertRaises(WorkflowValidationError):
            validate_manifest(
                self.manifest_path, self.root,
                self.root / "specs/image_first_workflow_v8.schema.json"
            )
        evidence = self.root / "assets/office2016-roundtrip.md"
        evidence.write_text("PowerPoint 2016 host round-trip: PASS\n", encoding="utf-8")
        self.manifest["stage_b"]["audit"]["office_2016_evidence"] = {
            "path": evidence.relative_to(self.root).as_posix(),
            "sha256": digest(evidence)
        }
        self._save()
        result = validate_manifest(
            self.manifest_path, self.root,
            self.root / "specs/image_first_workflow_v8.schema.json"
        )
        self.assertEqual(result["stage"], "FINAL_ACCEPTANCE")

    def test_target_image_hash_mismatch_fails_closed(self):
        self._approve_stage_a()
        self._save()
        self.manifest["stage_a"]["target_image"] = {
            "path": "assets/target.png", "sha256": "0" * 64,
            "width_px": 1920, "height_px": 1080, "media_type": "image/png"
        }
        self._save()
        with self.assertRaisesRegex(WorkflowValidationError, "ASSET_SHA256_MISMATCH"):
            validate_manifest(
                self.manifest_path, self.root,
                self.root / "specs/image_first_workflow_v8.schema.json"
            )

    def test_image_comparison_metrics_are_reproducible(self):
        self._make_image(self.target_path)
        shutil.copy2(self.target_path, self.preview_path)
        same = compare_images(self.target_path, self.preview_path)
        self.assertEqual(same["metrics"]["global_ssim"], 1.0)
        self.assertEqual(same["metrics"]["mean_absolute_error"], 0.0)
        self.assertEqual(same["metrics"]["dhash_hamming_distance"], 0)
        self._make_image(self.preview_path, altered=True)
        changed = compare_images(self.target_path, self.preview_path)
        self.assertLess(changed["metrics"]["global_ssim"], 1.0)
        self.assertGreater(changed["metrics"]["mean_absolute_error"], 0.0)

    def test_path_traversal_is_rejected(self):
        self.manifest["stage_a"]["prompt"]["template_ref"] = "../outside.md"
        self._save()
        with self.assertRaisesRegex(WorkflowValidationError, "PATH_ESCAPES_REPOSITORY"):
            validate_manifest(
                self.manifest_path, self.root,
                self.root / "specs/image_first_workflow_v8.schema.json"
            )


if __name__ == "__main__":
    unittest.main()
