#!/usr/bin/env python3
"""Build an Image2 prompt from a locked DeckSpec slide and its source topology."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from image_first_source_contract import load_source_figure_contract


def load_slide(deck_spec_path: Path, slide_id: str) -> tuple[dict, dict]:
    deck = json.loads(Path(deck_spec_path).read_text(encoding="utf-8"))
    matches = [slide for slide in deck["slides"] if slide["id"] == slide_id]
    if len(matches) != 1:
        raise ValueError(f"SLIDE_ID_NOT_UNIQUE_OR_MISSING:{slide_id}")
    return deck, matches[0]


def _geometry_instructions(contract: dict) -> list[str]:
    lines = []
    frequency = contract.get("frequency_axis", {})
    if frequency.get("direction") == "vertical_downward":
        lines.append("Frequency axis: draw a vertical arrow pointing downward at the right edge; do not turn it into a horizontal left-to-right axis.")
    total = contract.get("total_graph", {})
    if total:
        lines.append(
            f"Total graph: show {total.get('band_layer_count')} aligned band layers and "
            f"{total.get('inter_band_link_count')} dashed inter-band links as schematic structure."
        )
    input_graph = contract.get("input_graph", {})
    if input_graph:
        lines.append(
            f"Input graph icon: show {input_graph.get('node_count')} nodes in "
            f"{input_graph.get('band_row_count')} rows, with "
            f"{input_graph.get('within_band_edge_count')} within-band edges and "
            f"{input_graph.get('inter_band_link_count')} dashed inter-band links."
        )
    outputs = contract.get("class_outputs", {})
    if outputs:
        lines.append(
            f"Class outputs: show {outputs.get('count')} {outputs.get('shape')} markers; "
            f"highlight only output {outputs.get('highlighted_index')} using "
            f"{outputs.get('highlight_color')}."
        )
    readouts = contract.get("readout_blocks", {})
    if readouts:
        lines.append(
            f"Readout blocks: show {readouts.get('count')} blocks, both labelled "
            f"'{readouts.get('author_lab_visible_label')}'."
        )
    return lines


def build_prompt(deck: dict, slide: dict, reference_paths: list[str] | None = None,
                 source_figure: dict | None = None) -> str:
    """Return a deterministic prompt; only locked on-slide strings are presentation copy."""
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
        "## Exact visible text (copy verbatim; do not translate, paraphrase, omit, or invent)"
    ]
    lines.extend(f"{index}. {json.dumps(value, ensure_ascii=False)}"
                 for index, value in enumerate(slide["on_slide"], 1))
    lines.extend(["", "## Evidence and scientific constraints"])
    lines.extend(
        f"- Source: {item['source']} | evidence status: {item['status']}"
        for item in slide["evidence"]
    )
    lines.extend([
        "- Preserve all source-supported quantities, units, labels, formulas, arrow directions, and relationships.",
        "- Do not invent experimental results, numerical values, citations, mechanisms, or causal links.",
        "- Keep unverified or schematic elements explicitly identified as schematic."
    ])

    if source_figure:
        lines.extend([
            "",
            "## Locked source-figure contract (hard scientific constraints)",
            f"Source FigureSpec: {source_figure['figure_id']} v{source_figure['figure_version']}",
            "The source figure and topology hashes are recorded in the workflow manifest.",
            "### Source text labels and annotations"
        ])
        lines.extend(
            f"- {json.dumps(value, ensure_ascii=False)}"
            for value in source_figure["source_text"]
        )
        lines.append("### Critical semantic labels")
        lines.extend(
            f"- {key}: {json.dumps(value, ensure_ascii=False)}"
            for key, value in source_figure["critical_labels"].items()
        )
        lines.append("### Critical directed relationships (preserve arrow direction)")
        lines.extend(
            f"- {edge[0]} → {edge[1]}"
            for edge in source_figure["critical_edges"]
        )
        if source_figure["required_nodes"]:
            lines.append("### Required semantic nodes")
            lines.extend(f"- {node}" for node in source_figure["required_nodes"])
        geometry = _geometry_instructions(source_figure["geometry_contract"])
        if geometry:
            lines.append("### Source-specific geometry requirements")
            lines.extend(f"- {item}" for item in geometry)
        if source_figure["readout_label_discrepancy"]:
            lines.extend([
                "### Explicit evidence boundary",
                source_figure["readout_label_discrepancy"],
                "Preserve the author-lab visible labels and disclose the discrepancy; do not silently harmonize the terms."
            ])
        lines.append("Do not simplify away a critical node, route, branch, frequency direction, or class-output marker to make the slide look cleaner.")

    lines.extend([
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
        "- Do not add explanatory copy beyond the exact visible text list and source-figure labels.",
        "- Use supplied reference images only for the specified visual role; they do not override the scientific content lock."
    ])
    if references:
        lines.extend(["", "## Supplied visual references"])
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
    parser.add_argument("--reference", action="append", default=[])
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    deck, slide = load_slide(args.deck_spec, args.slide_id)
    source_figure = load_source_figure_contract(root, slide)
    prompt = build_prompt(deck, slide, args.reference, source_figure)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(prompt, encoding="utf-8")
    print(f"PASS Image2 prompt: slide={slide['id']} output={args.output}")


if __name__ == "__main__":
    main()
