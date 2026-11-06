# Academic Defense PPT Skill

## V7.5 draft — Academic presentation planning

The Skill now begins with a DeckSpec and ordered SlideSpecs. It records audience, time budget, claims, evidence, page roles, layout choices and speaker notes before figure production. FigureSpec topology and SourceStyleSpec visual anchors stay independent of the deck layout. See `docs/DECK_PLANNING_V75.md` and `specs/deck_spec_v75.example.json`.

This branch is a draft prototype and is not a stable baseline.

## V7.4 — Reproducible composite defense slide
A one-slide 16:9 layout restores the supplied V7.2 composition: two related figure panels stacked in the left column and a concise reading guide on the right. The lower diagnosis path is purpose-built for the narrow panel rather than uniformly shrinking a full-width figure.

Local V7.4 deliverables:
- Editable PPTX: `dist/C01_composite_defense_slide_v74.pptx`
- PDF preview: `dist/C01_composite_defense_slide_v74_preview.pdf`
- Canonical spec: `figure_specs/c01/C01_composite_defense_slide.json`
- Editable SVG: `examples/C01_composite_defense_slide_v74.svg`

Rebuild with `python tools/build_c01_v74.py` and validate with `python tools/validate_c01_v74.py`. The reproducible build has 227 native PowerPoint shapes and 41 text boxes. Automated checks found zero text-box intersections, out-of-bounds objects, picture objects and inherited theme shadows. PDF and PNG were exported using Windows PowerPoint 16.0 and inspected.

## V7.3 — Two-slide detail version
The two-panel C01 method is also available as two separate source-aligned slides:
1. FBG construction: sensor signals → OCF/notch filter → B1/B2/B3/Bq subgraphs → total graph.
2. SEANet diagnosis: Input → GCN → pooling → GCN → pooling → SR; parallel Input → EA → SR; both converge at the summation node.

Build and validate the two-slide detail version:
```bash
python tools/build_c01_v73.py
python tools/validate_c01_v73.py
```

## Evidence boundaries
- The original publisher image is not redistributed.
- Sensor photographs are replaced with editable vector silhouettes.
- Graph coordinates/adjacency remain schematic; no numerical adjacency matrix is claimed.
- V7.4 matches the supplied baseline layout, not the publisher image pixel-for-pixel.
- Windows PowerPoint rendering was checked for the V7.4 composite; earlier V7.3 detail slides still need separate Windows rendering.

Paper: Lee et al., *Engineering Applications of Artificial Intelligence* 179 (2026), 115273. DOI: 10.1016/j.engappai.2026.115273.
Author page: https://hai.snu.ac.kr/bbs/board.php?bo_table=sub4_1_a&wr_id=251
