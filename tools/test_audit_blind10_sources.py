#!/usr/bin/env python3
"""Regression tests for the frozen Blind10 source admission audit."""
from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

import fitz

from audit_blind10_sources import audit_one


class Blind10SourceAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.pdf = self.root / "source.pdf"
        document = fitz.open()
        page = document.new_page(width=600, height=800)
        page.insert_text((80, 120), "Example architecture caption")
        document.save(self.pdf)
        document.close()
        self.digest = hashlib.sha256(self.pdf.read_bytes()).hexdigest()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def source(self, **overrides):
        value = {
            "figure_id": "fixture",
            "filename": "source.pdf",
            "sha256": self.digest,
            "page_1based": 1,
            "region_pt": [40, 40, 560, 200],
            "caption_text": "Example architecture caption",
        }
        value.update(overrides)
        return value

    def test_valid_source_hash_crop_and_caption_pass(self) -> None:
        result, preview = audit_one(self.root, self.source())
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["sha256_match"])
        self.assertTrue(result["crop_within_page"])
        self.assertTrue(result["caption_anchor_found"])
        self.assertIsNotNone(preview)

    def test_source_hash_mismatch_fails_closed(self) -> None:
        result, _ = audit_one(self.root, self.source(sha256="0" * 64))
        self.assertEqual(result["status"], "FAIL_SOURCE_IDENTITY_OR_CROP")
        self.assertFalse(result["sha256_match"])

    def test_caption_outside_crop_fails_closed(self) -> None:
        result, _ = audit_one(
            self.root,
            self.source(region_pt=[40, 300, 560, 700]),
        )
        self.assertEqual(result["status"], "FAIL_SOURCE_IDENTITY_OR_CROP")
        self.assertFalse(result["caption_anchor_found"])

    def test_crop_outside_page_fails_closed(self) -> None:
        result, preview = audit_one(
            self.root,
            self.source(region_pt=[40, 40, 700, 200]),
        )
        self.assertEqual(result["status"], "FAIL_SOURCE_IDENTITY_OR_CROP")
        self.assertFalse(result["crop_within_page"])
        self.assertIsNone(preview)

    def test_missing_source_is_blocked(self) -> None:
        result, preview = audit_one(
            self.root,
            self.source(filename="missing.pdf"),
        )
        self.assertEqual(result["status"], "BLOCKED_MISSING_SOURCE")
        self.assertIsNone(preview)

    def test_page_index_out_of_range_is_explicit(self) -> None:
        result, preview = audit_one(
            self.root,
            self.source(page_1based=2),
        )
        self.assertEqual(result["status"], "FAIL_PAGE_OUT_OF_RANGE")
        self.assertIsNone(preview)


if __name__ == "__main__":
    unittest.main()
