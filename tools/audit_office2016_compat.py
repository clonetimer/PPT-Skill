#!/usr/bin/env python3
"""Conservative OOXML preflight for PowerPoint 2016 portability.

This is a package/feature preflight only. It does not launch Microsoft PowerPoint
and must not be reported as an Office 2016 runtime certification.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET

P_NS = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
A_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"

# Common Windows/Office font families. Unknown families are warnings because
# Office can substitute fonts; they are not proof of an unsupported feature.
OFFICE_FONTS = {
    "Arial", "Arial Black", "Calibri", "Cambria", "Cambria Math",
    "Comic Sans MS", "Georgia", "Segoe UI", "Segoe UI Symbol",
    "Tahoma", "Times New Roman", "Trebuchet MS", "Verdana",
    "Microsoft YaHei", "Microsoft YaHei UI",
}
UNSUPPORTED_MEDIA = {
    ".svg", ".webp", ".mp4", ".m4v", ".mov", ".wmv", ".avi",
    ".glb", ".gltf", ".3mf", ".obj", ".fbx",
}


def audit_pptx(path: Path) -> dict:
    path = Path(path)
    failures: list[str] = []
    warnings: list[str] = []
    media_files: list[str] = []
    fonts: set[str] = set()
    external_non_hyperlinks: list[str] = []
    ole_or_controls: list[str] = []
    unsupported_media: list[str] = []

    zip_integrity = "FAIL"
    try:
        with zipfile.ZipFile(path) as package:
            names = package.namelist()
            bad_member = package.testzip()
            required = {
                "[Content_Types].xml",
                "ppt/presentation.xml",
                "ppt/_rels/presentation.xml.rels",
            }
            missing = sorted(required - set(names))
            zip_integrity = "PASS" if bad_member is None and not missing else "FAIL"
            if bad_member:
                failures.append(f"corrupt ZIP member: {bad_member}")
            if missing:
                failures.append(f"missing required package parts: {', '.join(missing)}")

            media_files = [n for n in names if n.startswith("ppt/media/")]
            unsupported_media = [
                n for n in media_files if Path(n).suffix.lower() in UNSUPPORTED_MEDIA
            ]
            if unsupported_media:
                failures.append(
                    "media not included in the conservative Office 2016 profile: "
                    + ", ".join(unsupported_media)
                )

            embedded = [
                n for n in names
                if n.startswith("ppt/embeddings/") or n.startswith("ppt/activeX/")
            ]
            if embedded:
                failures.append("embedded OLE/ActiveX parts present: " + ", ".join(embedded))

            for name in names:
                if not name.endswith(".xml") and not name.endswith(".rels"):
                    continue
                try:
                    data = package.read(name)
                    root = ET.fromstring(data)
                except (ET.ParseError, KeyError):
                    continue

                if name.startswith("ppt/slides/") or name.startswith("ppt/slideMasters/"):
                    for tag in (P_NS + "oleObj", P_NS + "control"):
                        if root.find(".//" + tag) is not None:
                            ole_or_controls.append(name)

                if name.endswith(".rels"):
                    for rel in root:
                        if rel.attrib.get("TargetMode") == "External":
                            rel_type = rel.attrib.get("Type", "")
                            if not rel_type.endswith("/hyperlink"):
                                external_non_hyperlinks.append(
                                    f"{name}: {rel.attrib.get('Target', '')}"
                                )

                if name.startswith("ppt/slides/") or name.startswith("ppt/slideMasters/"):
                    for node in root.iter(A_NS + "latin"):
                        family = node.attrib.get("typeface", "").strip()
                        if family and family not in ("+", "-", "+mj-lt", "+mn-lt"):
                            fonts.add(family)

    except (OSError, zipfile.BadZipFile) as exc:
        return {
            "status": "FAIL",
            "path": str(path),
            "failures": [f"cannot read PPTX package: {exc}"],
            "warnings": [],
        }

    if ole_or_controls:
        failures.append("OLE/ActiveX objects present in: " + ", ".join(sorted(set(ole_or_controls))))
    if external_non_hyperlinks:
        failures.append(
            "external non-hyperlink relationships present: "
            + ", ".join(sorted(set(external_non_hyperlinks)))
        )

    unknown_fonts = sorted(font for font in fonts if font not in OFFICE_FONTS)
    if unknown_fonts:
        warnings.append(
            "font families are not in the common Windows/Office set and may substitute: "
            + ", ".join(unknown_fonts)
        )

    return {
        "status": "PASS" if not failures else "FAIL",
        "path": str(path),
        "zip_integrity": zip_integrity,
        "media_extensions": sorted({Path(n).suffix.lower() for n in media_files}),
        "media_count": len(media_files),
        "fonts": sorted(fonts),
        "unknown_fonts": unknown_fonts,
        "unsupported_media": unsupported_media,
        "external_non_hyperlink_relationships": sorted(set(external_non_hyperlinks)),
        "ole_or_controls": sorted(set(ole_or_controls)),
        "failures": failures,
        "warnings": warnings,
        "scope": (
            "Conservative OOXML feature preflight only; Microsoft PowerPoint 2016 "
            "open/save/render testing is still required."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", type=Path, nargs="+")
    parser.add_argument("--json", type=Path, help="write a JSON report")
    args = parser.parse_args()
    reports = [audit_pptx(path) for path in args.pptx]
    payload = reports[0] if len(reports) == 1 else {"reports": reports}
    rendered = json.dumps(payload, indent=2, ensure_ascii=False)
    print(rendered)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered + "\n", encoding="utf-8")
    if any(report["status"] != "PASS" for report in reports):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
