#!/usr/bin/env python3
"""Record the locally exported research figures and their actual renderer."""
from __future__ import annotations

import hashlib
import json
import platform
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import PIL
import pptx
import pypdf
from pypdf import PdfReader

from audit_pptx import audit
from scientific_ir import ROOT

IDS = ["Q01_iris_scatter", "Q02_iris_strip", "Q03_iris_mean_ci", "Q03_iris_mean_ci_nature",
       "Q04_iris_confusion", "Q05_iris_ablation", "Q06_iris_trend_interval", "Q07_wine_scatter", "I01_cell_image_quant"]


def digest(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_spec_digest(path: Path):
    value = json.loads(path.read_text(encoding="utf-8"))
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def canonical_svg_digest(path: Path):
    return hashlib.sha256(ET.canonicalize(path.read_text(encoding="utf-8")).encode("utf-8")).hexdigest()


def canonical_pptx_digest(path: Path):
    """Hash ZIP member names and payloads, ignoring container timestamps/order."""
    digest = hashlib.sha256()
    with zipfile.ZipFile(path) as archive:
        names = sorted(archive.namelist())
        assert len(names) == len(set(names)), path
        for name in names:
            payload = archive.read(name)
            for value in (name.encode("utf-8"), payload):
                digest.update(len(value).to_bytes(8, "big"))
                digest.update(value)
    return digest.hexdigest()


def pdf_font_audit(path: Path, expected_family: str):
    """Read actual embedded PDF fonts; subset prefixes are exporter-generated."""
    observed = set()
    embedded = True
    for page in PdfReader(path).pages:
        for reference in page["/Resources"]["/Font"].values():
            font = reference.get_object()
            name = str(font["/BaseFont"]).lstrip("/")
            observed.add(re.sub(r"^[A-Z]{6}\+", "", name))
            if font.get("/Subtype") == "/Type0":
                descendants = font.get("/DescendantFonts", [])
                assert descendants, (path, name)
                descriptor = descendants[0].get_object().get("/FontDescriptor")
            else:
                descriptor = font.get("/FontDescriptor")
            embedded &= bool(descriptor and any(
                descriptor.get_object().get(key) for key in ("/FontFile", "/FontFile2", "/FontFile3")))
    assert observed, path
    return {"expected_family": expected_family, "observed_fonts": sorted(observed),
            "embedded": embedded,
            "substitution_detected": not all(name.startswith(expected_family) for name in observed)}


def main():
    exporter = json.loads((ROOT / "dist/export_quantitative_metadata_v76.json").read_text(encoding="utf-8-sig"))
    assert exporter["exporter"] == "Microsoft PowerPoint"
    assert set(exporter["figure_ids"]) == set(IDS)
    records = []
    for figure_id in IDS:
        folder = "image" if figure_id.startswith("I") else "quant"
        spec = ROOT / f"figure_specs/{folder}/{figure_id}.json"
        outputs = {kind: ROOT / f"{base}/{figure_id}.{kind}"
                   for kind, base in (("svg", "examples"), ("pptx", "dist"),
                                      ("pdf", "dist"), ("preview.png", "dist"))}
        assert spec.is_file() and all(path.is_file() for path in outputs.values())
        qa = audit(outputs["pptx"])
        assert not qa["theme_first_effect_has_shadow"]
        assert all(s["out_of_bounds"] == s["text_box_overlaps"] == 0 for s in qa["slides"])
        assert all(s["non_svg_picture_objects"] == (1 if figure_id.startswith("I") else 0)
                   for s in qa["slides"])
        font_audit = pdf_font_audit(outputs["pdf"], json.loads(spec.read_text(encoding="utf-8"))["style"]["font"])
        assert font_audit["embedded"] and not font_audit["substitution_detected"], figure_id
        records.append({"figure_id": figure_id, "figure_spec": str(spec.relative_to(ROOT)).replace("\\", "/"),
                        "input_sha256": digest(spec),
                        "input_canonical_sha256": canonical_spec_digest(spec),
                        "outputs_sha256": {kind: digest(path) for kind, path in outputs.items()},
                        "outputs_canonical_sha256": {
                            "svg": canonical_svg_digest(outputs["svg"]),
                            "pptx": canonical_pptx_digest(outputs["pptx"])},
                        "qa": {"automated": "pass", "pdf_fonts": font_audit,
                               "manual_final_size": "pending_independent_review"}})
    record = {
        "schema_version": "7.6.0-dev", "build_commands": ["python tools/build_quantitative_examples.py",
            "python tools/build_publication_example.py", "python tools/build_image_quant_example.py",
            "pwsh tools/export_quantitative_pdf.ps1"],
        "tool_versions": {"python": platform.python_version(), "python_pptx": pptx.__version__,
                          "pillow": PIL.__version__, "pypdf": pypdf.__version__, "pdf_exporter": exporter},
        "platform": platform.platform(),
        "source_assets_sha256": {"data/iris_uci.csv": digest(ROOT / "data/iris_uci.csv"),
                                 "data/wine_uci.data": digest(ROOT / "data/wine_uci.data"),
                                 "data/cell_scikit_image_v026.png": digest(ROOT / "data/cell_scikit_image_v026.png")},
        "figures": records,
    }
    destination = ROOT / "dist/render_record_v76.json"
    destination.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS render record: {len(records)} figures; manual final-size review pending")


if __name__ == "__main__":
    main()
