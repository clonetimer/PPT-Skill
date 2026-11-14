"""Manual real-weight smoke test for the optional PaddleOCR backend."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

import fitz

from extract_source_layout import extract_source_layout


def make_smoke_pdf(path: Path) -> None:
    document = fitz.open()
    page = document.new_page(width=420, height=300)
    page.draw_rect(fitz.Rect(18, 20, 198, 270), color=(0.12, 0.28, 0.48), fill=(0.93, 0.96, 0.99), width=1.5)
    page.draw_rect(fitz.Rect(222, 20, 402, 270), color=(0.55, 0.28, 0.08), fill=(0.99, 0.95, 0.91), width=1.5)
    page.insert_text((28, 42), "(a)", fontsize=12)
    page.insert_text((232, 42), "(b)", fontsize=12)
    page.insert_text((48, 110), "Encoder", fontsize=13)
    page.insert_text((252, 110), "Decoder", fontsize=13)
    page.draw_line((90, 140), (330, 140), color=(0.1, 0.1, 0.1), width=1.5)
    page.insert_text((160, 165), "feature flow", fontsize=10)
    document.save(path)
    document.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("dist/vision_backend_smoke.json"))
    parser.add_argument("--dpi", type=int, default=120)
    parser.add_argument("--max-side", type=int, default=1600)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="ppt-skill-paddleocr-smoke-") as folder:
        source = Path(folder) / "synthetic_figure.pdf"
        make_smoke_pdf(source)
        layout = extract_source_layout(
            source,
            page_index=0,
            figure_region=(0.0, 0.0, 420.0, 300.0),
            vision_backend="paddleocr",
            vision_dpi=args.dpi,
            vision_max_side=args.max_side,
        )

    evidence = layout["visual_evidence"]
    assert evidence["backend"] == "paddleocr", evidence
    assert evidence["status"] == "COMPLETED", evidence
    assert evidence["paddleocr_version"], evidence
    assert evidence["raster_size_px"] and min(evidence["raster_size_px"]) > 0, evidence
    for field in (
        "visual_region_candidates",
        "ocr_panel_markers",
        "panel_hypotheses",
        "visual_alignment_groups",
        "source_object_ownership",
    ):
        assert isinstance(layout["panel_detection"][field], list), field

    args.output.write_text(json.dumps(layout, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "paddleocr_version": evidence["paddleocr_version"],
        "layout_model": evidence["layout_model"],
        "ocr_detection_model": evidence["ocr_detection_model"],
        "ocr_recognition_model": evidence["ocr_recognition_model"],
        "raster_size_px": evidence["raster_size_px"],
        "visual_region_candidates": len(layout["panel_detection"]["visual_region_candidates"]),
        "ocr_panel_markers": len(layout["panel_detection"]["ocr_panel_markers"]),
        "panel_hypotheses": len(layout["panel_detection"]["panel_hypotheses"]),
        "output": str(args.output),
    }, indent=2))


if __name__ == "__main__":
    main()
