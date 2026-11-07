# Academic Defense PPT Skill

## V7.6 development — Evidence-linked scientific figures

The current workflow links FigureSpec elements to evidence, checks C01's critical drawn arrows against its declared relationships, and builds six data-driven charts plus one image-and-quantification panel from public source assets. SVG and editable PPTX come from the same FigureSpec; PowerPoint-exported PDFs are included as inspected previews. See [the research-figure upgrade plan](docs/SCIENTIFIC_FIGURE_GAP_AND_UPGRADE_PLAN_2026.md) for scope and remaining gates.

```bash
python tools/build_quantitative_examples.py
python tools/build_image_quant_example.py
python tools/validate_scientific_ir.py
python tools/validate_quantitative_examples.py
python tools/validate_image_quant_example.py
```

The Iris charts use the public [UCI Iris dataset](https://archive.ics.uci.edu/dataset/53/iris) (CC BY 4.0, DOI 10.24432/C56C76). The image example uses the [CC0 scikit-image cell sample](https://scikit-image.org/docs/stable/api/skimage.data.html#skimage.data.cell), with documented 0.107 µm pixel spacing. The single-image pixel histogram is descriptive and does not imply biological replication or cell segmentation.

The 13-task benchmark contract is in `specs/research_figure_benchmark_v76.json`; all tasks have automated fixtures, including a three-slide defense deck. Its hard release gates require independent scientific and final-size review before a stable release. `dist/render_record_v76.json` records source/output hashes, tool versions and the remaining manual checks. Grayscale and approximate color-vision previews support visual inspection; independent review remains open.

`specs/output_profiles_v76.json` separates presentation QA from publication prerequisites. The current ten FigureSpecs use the presentation profile. Publication output requires a selected journal, current author guide and final-size settings before rendering.

## V7.5 — Academic presentation planning

The Skill now begins with a DeckSpec and ordered SlideSpecs. It records audience, time budget, claims, evidence, page roles, layout choices and speaker notes before figure production. FigureSpec topology and SourceStyleSpec visual anchors stay independent of the deck layout. See `docs/DECK_PLANNING_V75.md` and `specs/deck_spec_v75.example.json`.

The package remains a development baseline pending independent scientific and final-size review.

## V7.4 — Reproducible composite defense slide
A one-slide 16:9 layout restores the supplied V7.2 composition: two related figure panels stacked in the left column and a concise reading guide on the right. The lower diagnosis path is purpose-built for the narrow panel rather than uniformly shrinking a full-width figure.

Local V7.4 deliverables:
- Editable PPTX: `dist/C01_composite_defense_slide_v74.pptx`
- PDF preview: `dist/C01_composite_defense_slide_v74_preview.pdf`
- Canonical spec: `figure_specs/c01/C01_composite_defense_slide.json`
- Editable SVG: `examples/C01_composite_defense_slide_v74.svg`

Rebuild with `python tools/build_c01_v74.py` and validate with `python tools/validate_c01_v74.py`. The current development build has 228 native PowerPoint shapes and 41 text boxes. Automated checks found zero text-box intersections, out-of-bounds objects, picture objects and inherited theme shadows. PDF and PNG were exported using Windows PowerPoint 16.0 and inspected.

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
