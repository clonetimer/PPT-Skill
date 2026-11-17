#!/usr/bin/env python3
"""Audit the frozen ten-paper source PDFs before post-P0 reproduction.

The source PDFs remain private and are never copied into the repository. This
utility verifies their SHA-256, selected page/crop bounds, and caption anchor.
It can optionally render a contact sheet for human confirmation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize(value: str) -> str:
    return " ".join(value.lower().split())


def audit_one(source_dir: Path, source: dict) -> tuple[dict, Image.Image | None]:
    path = source_dir / source["filename"]
    result = {
        "figure_id": source["figure_id"],
        "filename": source["filename"],
        "expected_sha256": source["sha256"],
        "page_1based": source["page_1based"],
        "region_pt": source["region_pt"],
        "caption_text": source["caption_text"],
        "file_exists": path.is_file(),
        "sha256_match": False,
        "crop_within_page": False,
        "caption_anchor_found": False,
    }
    if not path.is_file():
        result["status"] = "BLOCKED_MISSING_SOURCE"
        return result, None

    observed = sha256(path)
    result["observed_sha256"] = observed
    result["sha256_match"] = observed == source["sha256"]

    with fitz.open(path) as document:
        page_index = source["page_1based"] - 1
        result["page_count"] = document.page_count
        if page_index < 0 or page_index >= document.page_count:
            result["status"] = "FAIL_PAGE_OUT_OF_RANGE"
            return result, None
        page = document[page_index]
        region = fitz.Rect(source["region_pt"])
        result["page_size_pt"] = [round(page.rect.width, 3), round(page.rect.height, 3)]
        result["crop_within_page"] = (
            region.width > 0 and region.height > 0 and page.rect.contains(region)
        )
        crop_text = page.get_text("text", clip=region)
        result["caption_anchor_found"] = (
            normalize(source["caption_text"]) in normalize(crop_text)
        )
        result["crop_text_excerpt"] = crop_text[:500].replace("\n", " ")
        image = None
        if result["crop_within_page"]:
            pixmap = page.get_pixmap(
                matrix=fitz.Matrix(1.8, 1.8), clip=region, alpha=False
            )
            image = Image.frombytes(
                "RGB", [pixmap.width, pixmap.height], pixmap.samples
            )

    result["status"] = (
        "PASS"
        if result["sha256_match"]
        and result["crop_within_page"]
        and result["caption_anchor_found"]
        else "FAIL_SOURCE_IDENTITY_OR_CROP"
    )
    return result, image


def write_contact_sheet(items: list[tuple[str, Image.Image]], output: Path) -> None:
    columns, cell_w, cell_h = 2, 800, 500
    rows = (len(items) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * cell_w, rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    try:
        title_font = ImageFont.truetype("DejaVuSans.ttf", 18)
    except OSError:
        title_font = ImageFont.load_default()

    for index, (label, source_image) in enumerate(items):
        x, y = (index % columns) * cell_w, (index // columns) * cell_h
        draw.text((x + 14, y + 10), label, fill="black", font=title_font)
        preview = source_image.copy()
        preview.thumbnail((cell_w - 28, cell_h - 62))
        sheet.paste(preview, (x + 14, y + 48))
        draw.rectangle((x, y, x + cell_w - 1, y + cell_h - 1), outline="gray")
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--csv", type=Path)
    parser.add_argument("--contact-sheet", type=Path)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    sources = manifest["sources"]
    results, previews = [], []
    for source in sources:
        result, preview = audit_one(args.source_dir, source)
        results.append(result)
        if preview is not None:
            previews.append((source["figure_id"], preview))

    passed = sum(item["status"] == "PASS" for item in results)
    report = {
        "schema_version": "1.0.0",
        "benchmark_id": manifest.get("benchmark_id"),
        "cohort_role": manifest.get("cohort_role"),
        "source_count": len(results),
        "passed_count": passed,
        "failed_or_blocked_count": len(results) - passed,
        "status": "PASS" if passed == len(results) else "FAIL",
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        fields = [
            "figure_id", "filename", "status", "sha256_match",
            "page_1based", "crop_within_page", "caption_anchor_found",
        ]
        with args.csv.open("w", newline="", encoding="utf-8-sig") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows({key: row.get(key) for key in fields} for row in results)

    if args.contact_sheet:
        write_contact_sheet(previews, args.contact_sheet)

    print(f"{report['status']}: {passed}/{len(results)} source PDFs passed preflight")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
