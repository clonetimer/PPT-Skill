#!/usr/bin/env python3
"""Compare an approved Image2 target with a rendered PPTX slide preview."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _dhash(gray: Image.Image) -> int:
    pixels = np.asarray(gray.resize((9, 8), Image.Resampling.LANCZOS), dtype=np.int16)
    bits = pixels[:, 1:] > pixels[:, :-1]
    value = 0
    for bit in bits.flat:
        value = (value << 1) | int(bit)
    return value


def compare_images(target_path: Path, preview_path: Path) -> dict:
    with Image.open(target_path) as image:
        target = image.convert("RGB")
    with Image.open(preview_path) as image:
        preview = image.convert("RGB")
    target_size = target.size
    preview_size = preview.size
    target_ratio = target.width / target.height
    preview_ratio = preview.width / preview.height
    if abs(target_ratio - preview_ratio) > 0.005:
        raise ValueError("PREVIEW_ASPECT_RATIO_MISMATCH")
    if preview.size != target.size:
        preview = preview.resize(target.size, Image.Resampling.LANCZOS)

    target_gray = np.asarray(target.convert("L"), dtype=np.float64)
    preview_gray = np.asarray(preview.convert("L"), dtype=np.float64)
    mean_target = float(target_gray.mean())
    mean_preview = float(preview_gray.mean())
    var_target = float(target_gray.var())
    var_preview = float(preview_gray.var())
    covariance = float(((target_gray - mean_target) * (preview_gray - mean_preview)).mean())
    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2
    denominator = (mean_target ** 2 + mean_preview ** 2 + c1) * (var_target + var_preview + c2)
    global_ssim = (
        ((2 * mean_target * mean_preview + c1) * (2 * covariance + c2)) / denominator
        if denominator else 1.0
    )
    mae = float(np.abs(
        np.asarray(target, dtype=np.float64) - np.asarray(preview, dtype=np.float64)
    ).mean() / 255.0)
    dhash_distance = (_dhash(target.convert("L")) ^ _dhash(preview.convert("L"))).bit_count()
    return {
        "target_image_sha256": sha256_file(target_path),
        "rendered_preview_sha256": sha256_file(preview_path),
        "target_size_px": list(target_size),
        "rendered_preview_size_px": list(preview_size),
        "comparison_size_px": list(target_size),
        "preview_resized_for_comparison": preview_size != target_size,
        "metrics": {
            "global_ssim": round(max(0.0, min(1.0, global_ssim)), 6),
            "mean_absolute_error": round(mae, 6),
            "dhash_hamming_distance": int(dhash_distance)
        },
        "method": (
            "Global grayscale SSIM (single whole-image window), normalized RGB MAE, "
            "and 64-bit difference hash. These are triage metrics; they do not replace "
            "regional inspection or human visual acceptance."
        )
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_image", type=Path)
    parser.add_argument("rendered_preview", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = compare_images(args.target_image, args.rendered_preview)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(f"PASS image comparison: {args.output}")


if __name__ == "__main__":
    main()
