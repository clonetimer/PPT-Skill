import csv
import json
import unittest
from pathlib import Path

from export_quantitative_reproduction_audit import build
from scientific_ir import ROOT


class QuantitativeReproductionAuditTests(unittest.TestCase):
    def test_bootstrap_recomputation_and_source_row_traceability_are_exported(self):
        report = build()
        self.assertEqual(report["validation_status"], "PASS")
        self.assertEqual(report["Q03"]["resampling"]["resamples"], 2000)
        self.assertEqual(report["Q03"]["resampling"]["seed"], 76)
        self.assertEqual(len(report["Q03"]["groups"]), 3)
        self.assertEqual(report["Q06"]["resampling"]["resamples"], 2000)
        self.assertEqual(len(report["Q06"]["bins"]), 5)
        self.assertTrue(report["Q06"]["source_rows_partitioned_once"])
        self.assertTrue(report["Q03"]["publication_variant_matches_source_values"])
        path = ROOT / "dist/quantitative_point_traceability_v76.csv"
        with path.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), report["traceability"]["point_to_source_row_records"])
        self.assertEqual({row["chart_id"] for row in rows},
                         {"Q01_iris_scatter","Q02_iris_strip","Q03_iris_mean_ci",
                          "Q03_iris_mean_ci_nature","Q06_iris_trend_interval",
                          "Q07_wine_scatter","Q08_wine_strip"})
        q07 = [row for row in rows if row["chart_id"] == "Q07_wine_scatter"]
        q08 = [row for row in rows if row["chart_id"] == "Q08_wine_strip"]
        self.assertEqual(len(q07), 178)
        self.assertEqual(len(q08), 178)
        self.assertEqual({row["source_row"] for row in q07}, {row["source_row"] for row in q08})


if __name__ == "__main__":
    unittest.main()
