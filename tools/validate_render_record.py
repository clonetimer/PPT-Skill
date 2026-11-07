#!/usr/bin/env python3
"""Check the committed Windows export attestation without rewriting it on CI."""
from __future__ import annotations

import json

from record_scientific_render import ROOT, IDS, canonical_spec_digest, digest


def main():
    record = json.loads((ROOT / "dist/render_record_v76.json").read_text(encoding="utf-8"))
    exporter = json.loads((ROOT / "dist/export_quantitative_metadata_v76.json").read_text(encoding="utf-8-sig"))
    assert record["schema_version"] == "7.6.0-dev"
    assert record["tool_versions"]["pdf_exporter"] == exporter
    assert exporter["exporter"] == "Microsoft PowerPoint" and exporter["version"]
    assert set(exporter["figure_ids"]) == set(IDS)
    for relpath, expected in record["source_assets_sha256"].items():
        assert digest(ROOT / relpath) == expected, relpath
    assert len(record["figures"]) == len(IDS)
    for figure in record["figures"]:
        figure_id = figure["figure_id"]
        assert figure_id in IDS
        spec = ROOT / figure["figure_spec"]
        assert canonical_spec_digest(spec) == figure["input_canonical_sha256"], figure_id
        for kind in ("pdf", "preview.png"):
            assert digest(ROOT / f"dist/{figure_id}.{kind}") == figure["outputs_sha256"][kind], (figure_id, kind)
        assert figure["qa"]["automated"] == "pass"
        assert figure["qa"]["manual_final_size"] == "pending_independent_review"
    assert record["font_substitution"] == "not_measured"
    print(f"PASS committed render record: {len(IDS)} Windows-exported figures; manual review pending")


if __name__ == "__main__":
    main()
