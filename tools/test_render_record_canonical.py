#!/usr/bin/env python3
"""Verify canonical render hashes ignore packaging noise but catch payload edits."""
from __future__ import annotations

import tempfile
import unittest
import zipfile
import json
import copy
from pathlib import Path

from record_scientific_render import ROOT, canonical_pptx_digest, canonical_source_digest, canonical_svg_digest
from validate_render_record import validate_pipeline_sources

TEMP_ROOT = ROOT / ".testtmp"
TEMP_ROOT.mkdir(exist_ok=True)


class CanonicalRenderTests(unittest.TestCase):
    def test_stale_pipeline_source_fails(self):
        record = json.loads((ROOT / "dist/render_record_v76.json").read_text(encoding="utf-8"))
        validate_pipeline_sources(record)
        changed = copy.deepcopy(record)
        changed["pipeline_sources_canonical_sha256"]["tools/render_figure_spec.py"] = "0" * 64
        with self.assertRaises(AssertionError):
            validate_pipeline_sources(changed)

    def test_source_hash_ignores_line_endings(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as folder:
            first, second = (Path(folder) / name for name in ("a.py", "b.py"))
            first.write_bytes(b"alpha\nbeta\n")
            second.write_bytes(b"alpha\r\nbeta\r\n")
            self.assertEqual(canonical_source_digest(first), canonical_source_digest(second))

    def test_pptx_zip_order_and_timestamp_do_not_change_hash(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as folder:
            assert Path(folder).resolve().is_relative_to(ROOT.resolve())
            first, second, changed = (Path(folder) / name for name in ("a.pptx", "b.pptx", "c.pptx"))
            with zipfile.ZipFile(first, "w") as archive:
                archive.writestr("ppt/slides/slide1.xml", "<slide><text>n=50</text></slide>")
                archive.writestr("ppt/presentation.xml", "<presentation/>")
            with zipfile.ZipFile(second, "w") as archive:
                archive.writestr("ppt/presentation.xml", "<presentation/>")
                archive.writestr("ppt/slides/slide1.xml", "<slide><text>n=50</text></slide>")
            with zipfile.ZipFile(changed, "w") as archive:
                archive.writestr("ppt/presentation.xml", "<presentation/>")
                archive.writestr("ppt/slides/slide1.xml", "<slide><text>n=49</text></slide>")
            self.assertEqual(canonical_pptx_digest(first), canonical_pptx_digest(second))
            self.assertNotEqual(canonical_pptx_digest(first), canonical_pptx_digest(changed))

    def test_svg_attribute_order_is_ignored_but_geometry_is_not(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as folder:
            assert Path(folder).resolve().is_relative_to(ROOT.resolve())
            first, second, changed = (Path(folder) / name for name in ("a.svg", "b.svg", "c.svg"))
            first.write_text('<svg><rect x="1" y="2"/></svg>', encoding="utf-8")
            second.write_text('<svg><rect y="2" x="1"/></svg>', encoding="utf-8")
            changed.write_text('<svg><rect y="2" x="3"/></svg>', encoding="utf-8")
            self.assertEqual(canonical_svg_digest(first), canonical_svg_digest(second))
            self.assertNotEqual(canonical_svg_digest(first), canonical_svg_digest(changed))


if __name__ == "__main__":
    unittest.main()
