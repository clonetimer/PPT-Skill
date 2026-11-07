#!/usr/bin/env python3
"""Compare migrated figures with the last pre-V7.6 committed source and renders."""
from __future__ import annotations

from collections import Counter
from io import BytesIO
import json
import subprocess
import xml.etree.ElementTree as ET

from pptx import Presentation

from validate_render_semantics import LEGACY, NS, ROOT, normalize

BASE = "7ea999d677a30db1bfcb9497a4d0c3d89403f350"  # Last pre-V7.6 commit.
APPROVED_C01_CORRECTIONS = {
    "C01_SEANet_graph_level": (
        ["Paper terminology: SR = sensitivity-aware readout. No additional classifier block is inserted beyond the source's summation node."],
        ["Publisher graphical abstract: EA feeds the first GCN; the first pooling branches to a second SR; both SR outputs merge before Dense classification.",
         "Dense", "fault class"]),
    "C01_composite_defense_slide": (
        ["diagnosis", "Fuse GCN/pooling and energy-assisted SR paths."],
        ["Dense", "class", "EA feeds first GCN; pooled features branch to two SR paths."]),
}


def historical(path: str) -> bytes | None:
    result = subprocess.run(["git", "show", f"{BASE}:{path}"], cwd=ROOT,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        assert b"does not exist" in result.stderr or b"exists on disk, but not in" in result.stderr, result.stderr
        return None
    return result.stdout


def labels_in_spec(blob: bytes) -> Counter[str]:
    spec = json.loads(blob)
    return Counter(normalize(e["text"]) for e in spec["elements"]
                   if e["type"] == "text" and e["text"].strip())


def labels_in_svg(blob: bytes) -> Counter[str]:
    root = ET.fromstring(blob)
    return Counter(normalize("".join(e.itertext())) for e in root.findall(f".//{NS}text")
                   if "".join(e.itertext()).strip())


def labels_in_pptx(blob: bytes) -> Counter[str]:
    deck = Presentation(BytesIO(blob))
    assert len(deck.slides) == 1
    return Counter(normalize(shape.text) for shape in deck.slides[0].shapes
                   if getattr(shape, "has_text_frame", False) and shape.text.strip())


def compare(name: str, kind: str, path: str, reader, baseline: Counter[str] | None = None) -> bool:
    blob = historical(path)
    before = reader(blob) if blob is not None else baseline
    assert before is not None, f"{name} {kind}: no historical artifact or source baseline"
    after = reader((ROOT / path).read_bytes())
    if before != after:
        missing = before - after
        added = after - before
        correction = APPROVED_C01_CORRECTIONS.get(name)
        allowed_missing, allowed_added = (Counter(map(normalize, labels)) for labels in correction) if correction else (Counter(), Counter())
        if missing != allowed_missing or added != allowed_added:
            raise AssertionError(f"{name} {kind}: missing={dict(missing)}, added={dict(added)}")
    return blob is not None


def main() -> None:
    for name, spec, svg, pptx, _ in LEGACY:
        compare(name, "FigureSpec", spec, labels_in_spec)
        compare(name, "SVG", svg, labels_in_svg)
        baseline = labels_in_spec(historical(spec))
        old_pptx = compare(name, "PPTX", pptx, labels_in_pptx, baseline=baseline)
        corrected = name in APPROVED_C01_CORRECTIONS
        print(f"PASS {name}: historical FigureSpec/SVG labels "
              + ("match documented C01 source correction; " if corrected else "preserved; ")
              + ("historical PPTX compared against the correction" if corrected else
                 "historical PPTX preserved" if old_pptx else
                 "current PPTX matches pre-migration FigureSpec (historical PPTX not committed)"))


if __name__ == "__main__":
    main()
