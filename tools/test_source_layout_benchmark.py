"""Tests for hash-locked source-layout cohort replay."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import fitz

from benchmark_source_layout import run_benchmark


def make_pdf(path: Path):
    doc = fitz.open()
    page = doc.new_page(width=300, height=200)
    page.draw_rect(fitz.Rect(20, 30, 280, 180), color=(.2, .3, .4), width=1)
    page.draw_rect(fitz.Rect(40, 50, 260, 85), color=(.1, .2, .4), width=1)
    page.draw_rect(fitz.Rect(40, 115, 260, 155), color=(.4, .2, .1), width=1)
    page.insert_text((30, 50), "(a)", fontsize=12)
    page.draw_line((50, 100), (240, 100), color=(.2, .3, .4), width=1)
    page.insert_text((30, 165), "Source figure caption", fontsize=9)
    doc.save(path)
    doc.close()


class SourceLayoutBenchmarkTests(unittest.TestCase):
    def test_replay_verifies_hashes_and_emits_schema_valid_sidecars(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_dir = root / "sources"
            output_dir = root / "out"
            source_dir.mkdir()
            rows = []
            for name in ("one.pdf", "two.pdf"):
                pdf = source_dir / name
                make_pdf(pdf)
                rows.append({
                    "figure_id": name.removesuffix(".pdf"),
                    "filename": name,
                    "sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
                    "page_1based": 1,
                    "region_pt": [20, 30, 280, 180],
                    "caption_text": "Source figure caption",
                })
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                "benchmark_id": "synthetic-source-layout",
                "cohort_role": "test",
                "sources": rows,
            }), encoding="utf-8")
            result = run_benchmark(source_dir, manifest, output_dir)
            self.assertEqual(result["status"], "COMPLETED")
            self.assertEqual(result["source_count"], 2)
            self.assertEqual(result["outputs_schema_validated"], 2)
            self.assertGreater(result["rows"][0]["unlabeled_panel_candidates"], 0)
            self.assertEqual(result["rows"][0]["alignment_groups"], 1)
            self.assertEqual(result["rows"][0]["crop_audit_status"], "PASS")
            self.assertTrue((output_dir / "one_source_layout.json").exists())
            self.assertTrue((output_dir / "two_source_layout.json").exists())
            self.assertTrue((output_dir / "source_layout_benchmark_summary.csv").exists())

    def test_caption_outside_crop_aborts_before_layout_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_dir = root / "sources"
            output_dir = root / "out"
            source_dir.mkdir()
            pdf = source_dir / "one.pdf"
            make_pdf(pdf)
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                "benchmark_id": "caption-outside-crop",
                "cohort_role": "test",
                "sources": [{
                    "figure_id": "one", "filename": "one.pdf",
                    "sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
                    "page_1based": 1, "region_pt": [20, 30, 280, 130],
                    "caption_text": "Source figure caption",
                }],
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "SOURCE_CROP_MANIFEST_AUDIT_FAIL"):
                run_benchmark(source_dir, manifest, output_dir)
            self.assertFalse((output_dir / "one_source_layout.json").exists())

    def test_hash_mismatch_aborts_before_writing_candidate_sidecar(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_dir = root / "sources"
            output_dir = root / "out"
            source_dir.mkdir()
            pdf = source_dir / "one.pdf"
            make_pdf(pdf)
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                "benchmark_id": "hash-mismatch",
                "cohort_role": "test",
                "sources": [{
                    "figure_id": "one", "filename": "one.pdf",
                    "sha256": "0" * 64, "page_1based": 1,
                    "region_pt": [20, 30, 280, 180],
                    "caption_text": "Source figure caption",
                }],
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "SOURCE_HASH_MISMATCH"):
                run_benchmark(source_dir, manifest, output_dir)
            self.assertFalse((output_dir / "one_source_layout.json").exists())


if __name__ == "__main__":
    unittest.main()
