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


    @patch("run_blind10_post_p0.run_pipeline")
    @patch("run_blind10_post_p0.audit_one")
    def test_one_pipeline_exception_does_not_abort_remaining_cases(self, audit_mock, pipeline_mock):
        audit_mock.side_effect = [
            ({"figure_id": source["figure_id"], "status": "PASS"}, None)
            for source in self.sources
        ]

        def fake_pipeline(source_pdf, destination, **kwargs):
            if source_pdf.name == "source_00.pdf":
                raise RuntimeError("synthetic importer failure")
            destination.mkdir(parents=True)
            (destination / "delivery_manifest.json").write_text("{}", encoding="utf-8")
            return {
                "status": "TECHNICAL_REVIEW",
                "full_release_accepted": False,
                "blockers": [],
                "pending_approvals": ["human_visual_review"],
            }

        pipeline_mock.side_effect = fake_pipeline
        result = run_cohort(self.source_dir, self.manifest, self.output)
        self.assertEqual(pipeline_mock.call_count, 10)
        self.assertEqual(result["pipeline_status_counts"]["PIPELINE_EXCEPTION"], 1)
        self.assertEqual(result["pipeline_status_counts"]["TECHNICAL_REVIEW"], 9)
        self.assertIn("synthetic importer failure", result["runs"][0]["blockers"][0])

    @patch("run_blind10_post_p0.run_pipeline")
    @patch("run_blind10_post_p0.audit_one")
    def test_source_picture_only_policy_is_explicit(self, audit_mock, pipeline_mock):
        image_only = [
            "01_wind_turbine_causal_framework",
            "03_attention_guided_gin_multitask",
            "06_harnessmm_overview",
            "07_iiot_mult_agent_digital_twin",
        ]
        for index, figure_id in enumerate(image_only):
            self.sources[index]["figure_id"] = figure_id
        self.manifest.write_text(json.dumps({
            "benchmark_id": "blind10-test",
            "cohort_role": "DEVELOPMENT_REGRESSION_ONLY",
            "sources": self.sources,
        }), encoding="utf-8")
        audit_mock.side_effect = [
            ({"figure_id": source["figure_id"], "status": "PASS"}, None)
            for source in self.sources
        ]

        def fake_pipeline(source_pdf, destination, **kwargs):
            destination.mkdir(parents=True)
            (destination / "delivery_manifest.json").write_text("{}", encoding="utf-8")
            return {"status": "TECHNICAL_REVIEW", "blockers": [], "pending_approvals": []}

        pipeline_mock.side_effect = fake_pipeline
        result = run_cohort(self.source_dir, self.manifest, self.output)
        native_requirements = [
            call.kwargs["require_native"] for call in pipeline_mock.call_args_list
        ]
        self.assertEqual(native_requirements[:4], [False] * 4)
        self.assertEqual(native_requirements[4:], [True] * 6)
        self.assertEqual(
            [run["route"] for run in result["runs"][:4]],
            ["SOURCE_PICTURE_ONLY_ALLOWED"] * 4,
        )
        self.assertIsNone(result["strict_reproduction_pass_rate"])


if __name__ == "__main__":
    unittest.main()
