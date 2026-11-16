#!/usr/bin/env python3
"""Audit native PPTX object provenance against a source FigureSpec."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE


SUPPORTED_TYPES = {
    "image", "text", "rect", "trapezoid", "line", "polyline",
    "polygon", "ellipse", "grid", "stack_grid", "sensor", "graph",
}


def audit_figure_spec_pptx(spec_path: Path, pptx_path: Path,
                           slide_index: int = 0) -> dict:
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    deck = Presentation(str(pptx_path))
    if slide_index < 0 or slide_index >= len(deck.slides):
        raise ValueError(f"SLIDE_INDEX_OUT_OF_RANGE:{slide_index}")
    elements = spec.get("elements", [])
    ids = [str(item.get("id", "")) for item in elements]
    if any(not value for value in ids):
        raise ValueError("FIGURE_SPEC_ELEMENT_ID_REQUIRED")
    duplicates = sorted(value for value, count in Counter(ids).items() if count > 1)
    if duplicates:
        raise ValueError(f"FIGURE_SPEC_ELEMENT_ID_DUPLICATE:{','.join(duplicates)}")

    slide = deck.slides[slide_index]
    shapes = list(slide.shapes)
    names = [shape.name for shape in shapes]
    object_map = {}
    missing_ids = []
    for element in elements:
        element_id = str(element["id"])
        marker = f"__{element_id}__"
        matched = [shape for shape in shapes if marker in shape.name]
        if not matched:
            missing_ids.append(element_id)
        object_map[element_id] = {
            "semantic_id": element.get("semantic_id"),
            "semantic_role": element.get("semantic_role"),
            "source_type": element.get("type"),
            "native_shape_names": [shape.name for shape in matched],
            "native_shape_count": len(matched),
        }

    unsupported = sorted({
        str(element.get("type"))
        for element in elements
        if element.get("type") not in SUPPORTED_TYPES
    })
    semantic_counts = defaultdict(int)
    for element in elements:
        semantic_id = element.get("semantic_id")
        if not semantic_id:
            continue
        semantic_counts[str(semantic_id)] += object_map[str(element["id"])]["native_shape_count"]

    inventory = {
        "native_text_shapes": sum(
            bool(getattr(shape, "has_text_frame", False)) and bool(shape.text.strip())
            for shape in shapes
        ),
        "native_shape_objects": sum(
            shape.shape_type != MSO_SHAPE_TYPE.PICTURE for shape in shapes
        ),
        "native_connectors": sum(
            shape.shape_type == MSO_SHAPE_TYPE.LINE for shape in shapes
        ),
        "native_charts": sum(
            shape.shape_type == MSO_SHAPE_TYPE.CHART for shape in shapes
        ),
        "picture_objects": sum(
            shape.shape_type == MSO_SHAPE_TYPE.PICTURE for shape in shapes
        ),
    }
    expected_count = len(elements)
    covered_count = expected_count - len(missing_ids)
    return {
        "status": "pass" if not missing_ids and not unsupported else "fail",
        "slide_index": slide_index,
        "source_element_count": expected_count,
        "source_element_covered_count": covered_count,
        "source_element_coverage": round(
            covered_count / expected_count if expected_count else 1.0, 6
        ),
        "missing_source_element_ids": missing_ids,
        "unsupported_figure_spec_types": unsupported,
        "semantic_object_counts": dict(sorted(semantic_counts.items())),
        "object_inventory": inventory,
        "object_map": object_map,
        "native_shape_names": names,
        "read_only": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("figure_spec", type=Path)
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--slide-index", type=int, default=0)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = audit_figure_spec_pptx(args.figure_spec, args.pptx, args.slide_index)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
