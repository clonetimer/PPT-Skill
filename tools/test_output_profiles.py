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
        validate_publication_target({"journal_name": "Example Journal", "author_guide_url": "https://example.org/guide",
                                     "final_width_mm": 180, "final_height_mm": 120, "allowed_formats": ["PDF"],
                                     "minimum_text_pt": 7, "raster_resolution_dpi": 300}, PROFILE)


if __name__ == "__main__":
    unittest.main()
