#!/usr/bin/env python3
"""Audit hash-locked PDF figure crop candidates against page bounds and caption anchors."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import fitz


def audit_source_crop_manifest(source_dir: Path, manifest_path: Path) -> dict:
    source_dir = Path(source_dir)
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = []
    failures = []

    for source in manifest.get("sources", []):
        figure_id = source.get("figure_id", "<missing-figure-id>")
        row = {"figure_id": figure_id, "status": "PASS", "failures": []}
        pdf = source_dir / source["filename"]
        if not pdf.is_file():
            row["failures"].append("SOURCE_FILE_MISSING")
        else:
            actual_sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
            row["source_sha256"] = actual_sha
            if actual_sha != source.get("sha256"):
                row["failures"].append("SOURCE_HASH_MISMATCH")
            try:
                page_index = int(source["page_1based"]) - 1
                with fitz.open(pdf) as document:
                    if page_index < 0 or page_index >= len(document):
                        row["failures"].append("SOURCE_PAGE_OUT_OF_RANGE")
                    else:
                        page = document[page_index]
                        page_rect = fitz.Rect(page.rect)
                        region = fitz.Rect(source["region_pt"])
                        clipped = region & page_rect
                        row["page"] = {
                            "index_1based": page_index + 1,
                            "width_pt": round(page_rect.width, 3),
                            "height_pt": round(page_rect.height, 3),
                        }
                        row["region_pt"] = [round(float(v), 3) for v in region]
                        if (region.width <= 0 or region.height <= 0 or
                            clipped.is_empty or
                            any(abs(a-b) > .01 for a, b in zip(region, clipped))):
                            row["failures"].append("REGION_OUT_OF_BOUNDS_OR_EMPTY")
                        else:
                            caption = str(source.get("caption_text", "")).strip()
                            if not caption:
                                row["failures"].append("CAPTION_ANCHOR_MISSING")
                            else:
                                hits = page.search_for(caption)
                                contained = [hit for hit in hits if region.contains(hit)]
                                if not contained:
                                    row["failures"].append("CAPTION_OUTSIDE_CROP")
                                else:
                                    selected = min(contained, key=lambda hit: (hit.y0, hit.x0))
                                    row["caption"] = {
                                        "anchor": caption,
                                        "match_count": len(contained),
                                        "bbox_pt": [round(float(v), 3) for v in selected],
                                    }

                            image_paints = 0
                            for kind, coords in page.get_bboxlog():
                                if kind == "fill-image" and fitz.Rect(coords).intersects(region):
                                    image_paints += 1
                            image_xrefs = [
                                info for info in page.get_image_info(xrefs=True)
                                if fitz.Rect(info["bbox"]).intersects(region)
                            ]
                            drawings = [
                                item for item in page.get_drawings(extended=True)
                                if item.get("type") not in ("clip", "group")
                                and fitz.Rect(item.get("rect", page_rect)).intersects(region)
                            ]
                            text_spans = []
                            for block in page.get_text("dict")["blocks"]:
                                if block.get("type") != 0:
                                    continue
                                for line in block.get("lines", []):
                                    for span in line.get("spans", []):
                                        if fitz.Rect(span["bbox"]).intersects(region):
                                            text_spans.append(span)
                            row["source_content"] = {
                                "image_paint_events": image_paints,
                                "image_xref_occurrences": len(image_xrefs),
                                "drawing_records": len(drawings),
                                "text_spans": len(text_spans),
                                "has_visual_content": bool(image_paints or drawings or text_spans),
                            }
                            if not row["source_content"]["has_visual_content"]:
                                row["failures"].append("EMPTY_CROP_CONTENT")
            except (KeyError, TypeError, ValueError, RuntimeError) as exc:
                row["failures"].append(f"CROP_AUDIT_ERROR:{type(exc).__name__}:{exc}")

        if row["failures"]:
            row["status"] = "FAIL"
            failures.append({"figure_id": figure_id, "failures": row["failures"]})
        rows.append(row)

    expected = len(manifest.get("sources", []))
    passed = sum(row["status"] == "PASS" for row in rows)
    return {
        "benchmark_id": manifest.get("benchmark_id"),
        "cohort_role": manifest.get("cohort_role"),
        "status": "PASS" if expected > 0 and passed == expected else "FAIL",
        "source_count": expected,
        "passed": passed,
        "failed": expected - passed,
        "failures": failures,
        "rows": rows,
        "scope": "Source hash, page/crop bounds, caption containment and observable crop content; not scientific figure approval",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit_source_crop_manifest(args.source_dir, args.manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "source_count": result["source_count"],
        "passed": result["passed"],
        "failed": result["failed"],
        "output": str(args.output),
    }, ensure_ascii=False))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
