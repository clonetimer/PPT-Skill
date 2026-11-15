#!/usr/bin/env python3
"""Build an Image2 prompt from a locked DeckSpec slide without leaking speaker notes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_slide(deck_spec_path: Path, slide_id: str) -> tuple[dict, dict]:
    deck = json.loads(Path(deck_spec_path).read_text(encoding="utf-8"))
    matches = [slide for slide in deck["slides"] if slide["id"] == slide_id]
    if len(matches) != 1:
        raise ValueError(f"SLIDE_ID_NOT_UNIQUE_OR_MISSING:{slide_id}")
    return deck, matches[0]


def build_prompt(deck: dict, slide: dict, reference_paths: list[str] | None = None) -> str:
    """Return a deterministic prompt; only DeckSpec on-slide strings are renderable copy."""
    references = reference_paths or []
    lines = [
        "Create exactly one finished 16:9 academic presentation slide image.",
        "Output a full-bleed 1920 × 1080 image. Do not show a monitor, laptop, desk, app frame, watermark, border, collage, or multiple slides.",
        "",
        "## Slide context",
        f"Topic: {deck['deck']['topic']}",
        f"Audience: {deck['deck']['audience']}",
        f"Slide ID: {slide['id']}",
        f"Slide role: {slide['role']}",
        f"Main claim: {slide['claim']}",
        "",
        "## Exact visible text (copy verbatim; do not translate, paraphrase, omit, or invent)",
    ]
    lines.extend(f"{index}. {json.dumps(value, ensure_ascii=False)}"
                 for index, value in enumerate(slide["on_slide"], 1))
    lines.extend([
        "",
        "## Evidence and scientific constraints",
    ])
    lines.extend(
        f"- Source: {item['source']} | evidence status: {item['status']}"
        for item in slide["evidence"]
    )
    lines.extend([
        "- Preserve all source-supported quantities, units, labels, formulas, arrow directions, and relationships.",
        "- Do not invent experimental results, numerical values, citations, mechanisms, or causal links.",
        "- Keep unverified or schematic elements explicitly identified as schematic.",
        "",
        "## Visual direction",
        f"Page role: {slide['layout']}",
        f"Style reference: {deck['deck'].get('style_ref', 'Use a restrained academic visual system')}",
        "- Create a clear title hierarchy, one dominant visual message, and an intentional reading path.",
        "- Use a clean grid, consistent alignment, generous whitespace, restrained color, and strong projection-scale contrast.",
        "- Prefer separable geometry: text regions, rectangles, circles, lines, arrows, chart marks, and simple icons.",
        "- Avoid dense textures, complex 3D effects, microtext, excessive decoration, and full-slide raster backgrounds.",
        "- If the content cannot fit legibly, simplify the composition or split the slide; never shrink labels to micro-size.",
        "",
        "## Reconstruction constraints",
        "- The image will be rebuilt as native editable PowerPoint text, shapes, connectors, and charts.",
        "- Keep text visually distinct from illustrations; do not turn labels into decorative texture.",
        "- Do not add explanatory copy beyond the exact visible text list unless the source material itself requires a short label.",
        "- Use supplied reference images only for the specified visual role; they do not override the scientific content lock.",
    ])
    if references:
        lines.append("")
        lines.append("## Supplied visual references")
        lines.extend(f"- {value}" for value in references)
        lines.append("Use these references for visual guidance only; do not copy unsupported content.")
    lines.extend([
        "",
        "## Presenter-only context (not visible on the slide)",
        "The following notes are for understanding the narrative only. Do not render them as slide text:",
        "[Presenter notes intentionally withheld from the image prompt. Use the source references and exact visible text above.]",
        "",
        "Return only the finished slide image."
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("deck_spec", type=Path)
    parser.add_argument("slide_id")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reference", action="append", default=[],
                        help="Human-readable path/name of a supplied visual reference; repeatable.")
    args = parser.parse_args()
    deck, slide = load_slide(args.deck_spec, args.slide_id)
    prompt = build_prompt(deck, slide, args.reference)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(prompt, encoding="utf-8")
    print(f"PASS Image2 prompt: slide={slide['id']} output={args.output}")


if __name__ == "__main__":
    main()
