import tempfile
import unittest
import zipfile
from pathlib import Path

import validate_research_benchmark
from package_15_final_candidates import build
from validate_research_benchmark import OUTPUTS, artifact_paths


class Package15FinalCandidatesTests(unittest.TestCase):
    def test_packages_all_15_tasks_and_both_q07_charts_with_hash_manifest(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            old_root = validate_research_benchmark.ROOT
            try:
                validate_research_benchmark.ROOT = root
                for task_id in OUTPUTS:
                    for relative in artifact_paths(task_id):
                        path = root / relative
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes((task_id + ":" + relative).encode("utf-8"))
                (root/"dist/quantitative_reproduction_audit_v76.json").write_text("{}")
                (root/"dist/quantitative_point_traceability_v76.csv").write_text("chart_id,source_row\\n")
                output = root / "dist" / "candidate.zip"
                result = build(output, root)
                self.assertEqual(result["status"], "PASS")
                self.assertEqual(result["population"], 15)
                self.assertGreater(result["q07_scatter_artifacts"], 0)
                self.assertGreater(result["q07_distribution_artifacts"], 0)
                with zipfile.ZipFile(output) as archive:
                    names = set(archive.namelist())
                    self.assertIn("02_最终候选版/Q07/01_散点/Q07_wine_scatter.pptx", names)
                    self.assertIn("02_最终候选版/Q07/02_分布/Q08_wine_strip.pptx", names)
                    self.assertIn("02_最终候选版/Q07/02_分布/Q08_wine_strip.svg", names)
                    self.assertIn("02_最终候选版/Q07/02_分布/Q08_wine_strip.pdf", names)
                    self.assertIn("SHA256_MANIFEST.json", names)
                    self.assertIn("03_审计证据/quantitative_reproduction_audit_v76.json", names)
                    self.assertIn("03_审计证据/quantitative_point_traceability_v76.csv", names)
            finally:
                validate_research_benchmark.ROOT = old_root

    def test_missing_q07_distribution_fails_instead_of_silent_partial_package(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            old_root = validate_research_benchmark.ROOT
            try:
                validate_research_benchmark.ROOT = root
                for task_id in OUTPUTS:
                    for relative in artifact_paths(task_id):
                        if relative == "dist/Q08_wine_strip.pptx":
                            continue
                        path = root / relative
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes(b"artifact")
                (root/"dist/quantitative_reproduction_audit_v76.json").write_text("{}")
                (root/"dist/quantitative_point_traceability_v76.csv").write_text("chart_id,source_row\\n")
                with self.assertRaisesRegex(FileNotFoundError, "FINAL_CANDIDATE_ARTIFACTS_MISSING"):
                    build(root / "dist" / "candidate.zip", root)
            finally:
                validate_research_benchmark.ROOT = old_root


if __name__ == "__main__":
    unittest.main()
