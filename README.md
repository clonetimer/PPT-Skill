# Academic Defense PPT Skill

## V7.4.0 — Composite defense slide
A one-slide 16:9 layout restores the supplied V7.2 composition: two related figure panels stacked in the left column and a concise reading guide on the right. The lower diagnosis path is purpose-built for the narrow panel rather than uniformly shrinking a full-width figure.

Local V7.4 deliverables:
- Editable PPTX: `C01_composite_defense_slide_v74.pptx`
- PDF preview: `C01_composite_defense_slide_v74_preview.pdf`
- Canonical spec: `C01_composite_defense_slide.json`

V7.4 was locally audited: 320 native PowerPoint shapes, 31 text boxes, zero text-box intersections, zero out-of-bounds objects, zero picture objects, and no inherited theme shadow.

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
- Windows PowerPoint rendering remains a separate validation target.

Paper: Lee et al., *Engineering Applications of Artificial Intelligence* 179 (2026), 115273. DOI: 10.1016/j.engappai.2026.115273.
Author page: https://hai.snu.ac.kr/bbs/board.php?bo_table=sub4_1_a&wr_id=251
