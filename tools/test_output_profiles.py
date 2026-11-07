#!/usr/bin/env python3
"""Publication output cannot be built from an unspecified journal target."""
from __future__ import annotations

import json
import unittest

from scientific_ir import ROOT
from validate_output_profiles import validate_publication_target


PROFILE = json.loads((ROOT / "specs/output_profiles_v76.json").read_text(encoding="utf-8"))["profiles"]["publication"]


class OutputProfileTests(unittest.TestCase):
    def test_missing_journal_target_fails(self):
        with self.assertRaises(AssertionError):
            validate_publication_target({}, PROFILE)

    def test_complete_target_passes(self):
        validate_publication_target({"journal_name": "Example Journal", "figure_class": "main_figure",
                                     "author_guide_url": "https://example.org/guide", "guide_checked_date": "2026-11-07",
                                     "final_width_mm": 180, "final_height_mm": 120, "maximum_height_mm": 160,
                                     "allowed_formats": ["PDF"], "preferred_submission_format": "PDF",
                                     "minimum_text_pt": 5, "maximum_text_pt": 7,
                                     "raster_resolution_dpi": 300}, PROFILE)

    def test_height_exceeding_target_fails(self):
        target = {"journal_name": "Example Journal", "figure_class": "main_figure",
                  "author_guide_url": "https://example.org/guide", "guide_checked_date": "2026-11-07",
                  "final_width_mm": 180, "final_height_mm": 180, "maximum_height_mm": 160,
                  "allowed_formats": ["PDF"], "preferred_submission_format": "PDF",
                  "minimum_text_pt": 5, "maximum_text_pt": 7, "raster_resolution_dpi": 300}
        with self.assertRaises(AssertionError):
            validate_publication_target(target, PROFILE)


if __name__ == "__main__":
    unittest.main()
