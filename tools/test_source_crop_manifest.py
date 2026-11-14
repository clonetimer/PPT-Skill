"""Tests for source crop provenance and caption-containment auditing."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import fitz

from audit_source_crop_manifest import audit_source_crop_manifest


def make_pdf(path: Path):
    doc = fitz.open()
    page = doc.new_page(width=300, height=200)
    page.draw_rect(fitz.Rect(20, 30, 280, 140), color=(.2, .3, .4), width=1)
    page.draw_line((40, 100), (260, 100), color=(.4, .2, .1), width=1)
    page.insert_text((30, 165), "Source figure caption", fontsize=9)
    doc.save(path)
    doc.close()


def write_manifest(root: Path, pdf: Path, *, region=(20, 30, 280, 180), sha=None, page=1):
    payload = {
        "benchmark_id": "crop-audit-test",
        "cohort_role": "test",
        "sources": [{
            "figure_id": "one",
            "filename": pdf.name,
            "sha256": sha or hashlib.sha256(pdf.read_bytes()).hexdigest(),
            "page_1based": page,
            "region_pt": list(region),
            "caption_text": "Source figure caption",
        }],
    }
    manifest = root / "manifest.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    return manifest


class SourceCropManifestAuditTests(unittest.TestCase):
    def test_valid_hash_crop_and_caption_anchor_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_dir = root / "sources"
            source_dir.mkdir()
            pdf = source_dir / "one.pdf"
            make_pdf(pdf)
            manifest = write_manifest(root, pdf)
            result = audit_source_crop_manifest(source_dir, manifest)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["passed"], 1)
            self.assertEqual(result["rows"][0]["caption"]["anchor"], "Source figure caption")
            self.assertTrue(result["rows"][0]["source_content"]["has_visual_content"])
            self.assertGreaterEqual(result["rows"][0]["source_content"]["stroke_segment_candidates"], 1)

    def test_hash_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_dir = root / "sources"
            source_dir.mkdir()
            pdf = source_dir / "one.pdf"
            make_pdf(pdf)
            manifest = write_manifest(root, pdf, sha="0" * 64)
            result = audit_source_crop_manifest(source_dir, manifest)
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("SOURCE_HASH_MISMATCH", result["rows"][0]["failures"])

    def test_caption_outside_crop_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_dir = root / "sources"
            source_dir.mkdir()
            pdf = source_dir / "one.pdf"
            make_pdf(pdf)
            manifest = write_manifest(root, pdf, region=(20, 30, 280, 130))
            result = audit_source_crop_manifest(source_dir, manifest)
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("CAPTION_OUTSIDE_CROP", result["rows"][0]["failures"])

    def test_crop_outside_page_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_dir = root / "sources"
            source_dir.mkdir()
            pdf = source_dir / "one.pdf"
            make_pdf(pdf)
            manifest = write_manifest(root, pdf, region=(20, 30, 320, 180))
            result = audit_source_crop_manifest(source_dir, manifest)
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("REGION_OUT_OF_BOUNDS_OR_EMPTY", result["rows"][0]["failures"])

    def test_caption_only_crop_fails_visual_content_requirement(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_dir = root / "sources"
            source_dir.mkdir()
            pdf = source_dir / "one.pdf"
            make_pdf(pdf)
            manifest = write_manifest(root, pdf, region=(20, 145, 280, 180))
            result = audit_source_crop_manifest(source_dir, manifest)
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("EMPTY_CROP_CONTENT", result["rows"][0]["failures"])

    def test_missing_source_page_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_dir = root / "sources"
            source_dir.mkdir()
            pdf = source_dir / "one.pdf"
            make_pdf(pdf)
            manifest = write_manifest(root, pdf, page=2)
            result = audit_source_crop_manifest(source_dir, manifest)
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("SOURCE_PAGE_OUT_OF_RANGE", result["rows"][0]["failures"])


if __name__ == "__main__":
    unittest.main()
