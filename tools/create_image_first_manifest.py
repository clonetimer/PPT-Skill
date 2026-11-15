#!/usr/bin/env python3
"""Create a per-slide Image2 prompt and V8 two-stage workflow manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from build_image2_slide_prompt import build_prompt, load_slide

ROOT = Path(__file__).resolve().parents[1]
CHECKS = (
    "scientific_content",
    "exact_text",
    "source_fidelity",
    "visual_hierarchy",
    "projection_readability",
    "reconstruction_feasibility",
)


def _relative(path: Path, root: Path) -> str:
    resolved = path.resolve()
    base = root.resolve()
    if not resolved.is_relative_to(base):
        raise ValueError(f"OUTPUT_OUTSIDE_REPOSITORY:{path}")
    return resolved.relative_to(base).as_posix()


def create_manifest(deck_spec_path: Path, slide_id: str, output_dir: Path,
                    root: Path = ROOT, workflow_id: str | None = None) -> tuple[Path, Path]:
    root = Path(root).resolve()
    deck_path = Path(deck_spec_path)
    if not deck_path.is_absolute():
        deck_path = root / deck_path
    deck_path = deck_path.resolve()
    if not deck_path.is_relative_to(root):
        raise ValueError("DECK_SPEC_OUTSIDE_REPOSITORY")
    deck, slide = load_slide(deck_path, slide_id)

    target_dir = Path(output_dir)
    if not target_dir.is_absolute():
        target_dir = root / target_dir
    target_dir = target_dir.resolve()
    prompt_path = target_dir / "image2_prompt.md"
    manifest_path = target_dir / "workflow.json"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)

    prompt_path.write_text(build_prompt(deck, slide), encoding="utf-8")
    prompt_hash = hashlib.sha256(prompt_path.read_bytes()).hexdigest()
    deck_ref = _relative(deck_path, root)
    prompt_ref = _relative(prompt_path, root)
    slug = workflow_id or re.sub(r"[^a-z0-9._-]+", "-", f"{deck['deck']['topic']}-{slide_id}".lower()).strip("-")

    manifest = {
        "schema_version": "8.0.0-dev",
        "workflow_id": slug,
        "mode": "image_first",
        "deck_spec_ref": deck_ref,
        "slide_id": slide["id"],
        "slide_index": next(index for index, item in enumerate(deck["slides"], 1)
                            if item["id"] == slide_id),
        "content_lock": {
            "claim": slide["claim"],
            "on_slide": slide["on_slide"],
            "speaker_notes": slide["speaker_notes"],
            "evidence": slide["evidence"],
            "visual_constraints": [
                "Preserve the DeckSpec claim and all exact on-slide strings.",
                "Do not promote unverified source details into visible scientific claims.",
                "Speaker notes are presenter-only and must not be rendered."
            ]
        },
        "stage_a": {
            "status": "planned",
            "generation": {
                "provider": "Image2",
                "model": "Image2",
                "aspect_ratio": "16:9",
                "width_px": 1920,
                "height_px": 1080,
                "iteration": 0,
                "seed": None
            },
            "prompt": {
                "template_ref": "prompts/image2_slide_prompt_template.md",
                "rendered_asset": {"path": prompt_ref, "sha256": prompt_hash}
            },
            "reference_assets": [],
            "target_image": None,
            "review": {
                "decision": "pending",
                "reviewer": None,
                "reviewed_at": None,
                "checks": {key: False for key in CHECKS},
                "issues": []
            }
        },
        "stage_b": {
            "status": "not_started",
            "target_image_sha256": None,
            "pptx": None,
            "rendered_preview": None,
            "object_inventory": None,
            "parity": None,
            "audit": None
        }
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
    return prompt_path, manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("deck_spec", type=Path)
    parser.add_argument("slide_id")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--workflow-id")
    args = parser.parse_args()
    prompt_path, manifest_path = create_manifest(
        args.deck_spec, args.slide_id, args.output_dir, workflow_id=args.workflow_id
    )
    print(f"PASS Image-first manifest: {manifest_path}")
    print(f"PASS Image2 prompt: {prompt_path}")


if __name__ == "__main__":
    main()
