#!/usr/bin/env python3
"""Regression tests for deterministic C01 V4.3 Stage-A raster corrections."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from patch_c01_image_first_v4_3 import EXPECTED_SIZE, patch_image


class C01ImageFirstV43PatchTests(unittest.TestCase):
    def test_patch_metadata_and_stage_gates(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "synthetic_v42.png"
            output = root / "v43.png"
            Image.new("RGB", EXPECTED_SIZE, "white").save(source)
            audit = patch_image(source, output, verify_source=False)

            self.assertEqual(audit["status"], "PASS")
            self.assertEqual(audit["width_px"], 1920)
            self.assertEqual(audit["height_px"], 1080)
            self.assertEqual(audit["A1_total_graph"]["solid_within_row_edges"], 8)
            self.assertEqual(audit["A1_total_graph"]["representative_dashed_inter_band_connectors"], 1)
            self.assertEqual(audit["A1_total_graph"]["connector_route"], "B1_to_B2")
            self.assertIs(audit["A1_total_graph"]["direct_B3_to_BN_edge"], False)
            self.assertEqual(audit["A1_total_graph"]["non_attached_continuation_rails"], 2)
            self.assertEqual(audit["A2_cross_panel_route"]["route"],
                             "Total graph -> lower outer edge -> left gutter -> Input")
            self.assertIs(audit["A2_cross_panel_route"]["continuous"], True)
            self.assertIs(audit["A2_cross_panel_route"]["arrowhead_at_input"], True)
            self.assertEqual(audit["A3_input_graph"]["nodes"], 12)
            self.assertEqual(audit["A3_input_graph"]["solid_within_row_edges"], 8)
            self.assertEqual(audit["A3_input_graph"]["dashed_inter_row_connectors"], 3)
            self.assertIs(audit["B1_dense_output"]["detached_extra_arrow_removed"], True)
            self.assertEqual(audit["projection_readability"], "PENDING_PHYSICAL_TEST")
            self.assertEqual(audit["stage_b"], "LOCKED_NOT_STARTED")
            self.assertTrue(output.is_file())
            self.assertEqual(Image.open(output).size, EXPECTED_SIZE)

    def test_patch_rejects_wrong_source_hash_by_default(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "wrong_source.png"
            output = root / "out.png"
            Image.new("RGB", EXPECTED_SIZE, "white").save(source)
            with self.assertRaisesRegex(ValueError, "UNEXPECTED_V42_SOURCE_SHA256"):
                patch_image(source, output)


if __name__ == "__main__":
    unittest.main()
