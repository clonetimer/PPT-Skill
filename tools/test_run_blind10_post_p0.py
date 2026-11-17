from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from run_blind10_post_p0 import run_cohort


class Blind10PostP0RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source_dir = self.root / "sources"
        self.source_dir.mkdir()
        self.manifest = self.root / "manifest.json"
        self.output = self.root / "out"
        self.sources = [
            {
                "figure_id": f"figure_{i:02d}",
                "filename": f"source_{i:02d}.pdf",
                "sha256": f"{i:064x}",
                "page_1based": 1,
                "region_pt": [10, 10, 100, 100],
                "caption_text": f"Caption {i}",
            }
            for i in range(10)
        ]
        self.manifest.write_text(json.dumps({
            "benchmark_id": "blind10-test",
            "cohort_role": "DEVELOPMENT_REGRESSION_ONLY",
            "sources": self.sources,
        }), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    @patch("run_blind10_post_p0.run_pipeline")
    @patch("run_blind10_post_p0.audit_one")
    def test_runs_all_ten_only_after_preflight_passes(self, audit_mock, pipeline_mock):
        audit_mock.side_effect = [
            ({"figure_id": source["figure_id"], "status": "PASS"}, None)
            for source in self.sources
        ]

        def fake_pipeline(source_pdf, destination, **kwargs):
            destination.mkdir(parents=True)
            manifest = destination / "delivery_manifest.json"
            manifest.write_text("{}", encoding="utf-8")
            return {
                "status": "FULL_ACCEPTED",
                "full_release_accepted": False,
                "blockers": ["human_review_pending"],
                "pending_approvals": ["visual_signoff"],
            }

        pipeline_mock.side_effect = fake_pipeline
        result = run_cohort(self.source_dir, self.manifest, self.output)
        self.assertEqual(result["source_preflight"], "PASS_10_OF_10")
        self.assertEqual(result["source_count"], 10)
        self.assertEqual(pipeline_mock.call_count, 10)
        self.assertEqual(result["pipeline_status_counts"], {"FULL_ACCEPTED": 10})
        self.assertEqual(result["strict_reproduction_pass_rate"], None)
        self.assertEqual(result["scientific_human_acceptance"], "NOT_PERFORMED")

    @patch("run_blind10_post_p0.run_pipeline")
    @patch("run_blind10_post_p0.audit_one")
    def test_preflight_failure_blocks_all_reproduction(self, audit_mock, pipeline_mock):
        audit_mock.return_value = ({"status": "FAIL_SOURCE_IDENTITY_OR_CROP"}, None)
        result = run_cohort(self.source_dir, self.manifest, self.output)
        self.assertEqual(result["status"], "BLOCKED_SOURCE_PREFLIGHT")
        pipeline_mock.assert_not_called()

    @patch("run_blind10_post_p0.audit_one")
    def test_nonempty_output_directory_is_never_overwritten(self, audit_mock):
        self.output.mkdir()
        (self.output / "keep.txt").write_text("immutable", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            run_cohort(self.source_dir, self.manifest, self.output)
        self.assertEqual((self.output / "keep.txt").read_text(encoding="utf-8"), "immutable")


if __name__ == "__main__":
    unittest.main()
