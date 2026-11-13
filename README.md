# Academic Defense PPT Skill

## Unified research-figure production entrypoint

For a source-author vector PDF, run the full evidence-linked workflow:

~~~bash
python tools/reproduce_research_figure.py source.pdf --output dist/figure-recovery --mode import --render-host auto
~~~

If you already have a manually verified FigureSpec, use --mode figurespec
and --figure-spec path/to/figure.json. The two routes have DIFFERENT evidence
classes; importing source paths does not create a semantic FigureSpec.
The output includes editable PPTX, source preflight, quality report, OOXML
preflight, rendering comparison where available, and a manifest with SHA-256
and outstanding review gates. See
[workflow and real Windows PowerPoint 2016 round-trip](docs/SCIENTIFIC_FIGURE_REPRODUCTION_WORKFLOW_VNEXT.md).

For the MMGraph-Agent F2 dense radar charts, source-grounded Table 3 numeric
geometry is separately audited across 18 axes and nine method curves using
[the F2 radar audit](docs/MMGRAPH_F2_NUMERIC_AUDIT_2026-11-13.md).
The source-faithful PPTX and a Table-3-corrected alternative are distinct
files. Never silently replace author-rendered scientific values.

Three NEW synthetic cross-family PDFs (multi-panel, complex hypergraph,
statistics) are exercised by tools/test_unseen_figure_families.py in CI;
they are not evidence of first-shot success on independent real papers.

## Evidence-first new-figure recovery (first-pass gate)

For an **unseen author-supplied vector PDF**, prefer the new quality-gated
entrypoint over a bare object-count check:

```bash
python tools/figure_first_pass_gate.py source.pdf \
  --pptx out/source_editable.pptx \
  --report out/first_pass.json --auto-export \
  --preview out/source_vs_candidate_vs_diff.png
```

This preflights mathematical Unicode/font issues, clipping and very thick
strokes, raster-only diagrams, dense figure panels and tiny labels. Canonical
four-Bezier ellipses are imported as native editable PowerPoint ovals rather
than fragile sampled freeforms. After PDF export it reports both whole-figure
and spatial-tile similarity, and identifies concrete regions for review.
Statuses are `TECHNICAL_PASS`, `NEEDS_REVIEW` and `FAIL` — none certify
scientific correctness or Office 2016 runtime compatibility. When no PDF
exporter is available, visual acceptance is explicitly pending.

See [first-pass quality gate and frozen held-out evaluation](docs/FIRST_PASS_FIGURE_FIDELITY_GATE.md).
Run `python tools/test_figure_first_pass_gate.py` for automated regression
coverage; held-out synthetic tests are not a measured independent-paper
first-attempt success rate.

## Author-PDF figure recovery (experimental)

`tools/pdf_figure_import.py` imports an author-provided **vector PDF figure** into
one PowerPoint slide. It preserves page dimensions, individual editable paths,
connectors, visible label text and separately placed photographs/icons. Unlike
placing a full-page screenshot on a slide, its output can be edited object by
object. PDF compound paths are kept together so letterforms and icon cutouts do
not become solid rectangles. Fill and stroke opacity, PDF soft hyphens and
inline images are handled explicitly.

For example, with a PDF you have permission to modify:

```bash
python -m pip install PyMuPDF python-pptx Pillow
python tools/pdf_figure_import.py path/to/Figure.pdf path/to/Figure_editable.pptx \
  --report path/to/Figure_import.json
python tools/audit_imported_pdf_figure.py path/to/Figure.pdf \
  path/to/Figure_editable.pptx --report path/to/Figure_audit.json
```

The audit checks exact source labels, picture count, editability ratio and
full-figure-image flattening. Run its regression tests using
`python tools/test_pdf_figure_import.py` and
`python tools/test_audit_imported_pdf_figure.py` (tests also need `reportlab`).
**A passing audit is structural, not pixel-accurate proof.** Complex PDF
mathematical fonts, native PowerPoint font substitutions, gradient/raster
effects, unusual stroke widths and final-size readability still require a
side-by-side preview in the target PowerPoint version. The importer normalizes
known Windows font aliases (for example `ComicSansMS` → `Comic Sans MS`) and
maps opaque PDF font-resource identifiers to Arial instead of leaking an
unavailable internal name into PowerPoint.

Run the conservative Office 2016 OOXML preflight on a candidate deck:

```bash
python tools/audit_office2016_compat.py path/to/Figure_editable.pptx --json office2016_preflight.json
python tools/test_office2016_compat.py
```

This preflight flags SVG/WebP/video/3D media, OLE/ActiveX parts and external
non-hyperlink relationships, and reports font families that may be substituted.
It is **not** an Office 2016 runtime certification: open, save and export the
deck in the target PowerPoint 2016 installation before claiming compatibility.
Original author PDFs, paper figures, embedded photos and project-specific PPTX
reconstructions are not redistributed in this public repository; check original
permissions before sharing them.

Independent-paper generalization is also covered by the
[Mamba and Swin figure trials](docs/GENERALIZATION_TRIALS_2026-11-13.md). CI
renders both from FigureSpecs and checks source-derived topology before
auditing their native PowerPoint objects.

## V7.6 development — Evidence-linked scientific figures

The current workflow links FigureSpec elements to evidence, checks C01's critical drawn arrows against its declared relationships, and builds six Iris charts, Wine scatter and distribution plots, and one image-and-quantification panel from public source assets. The chart contract declares axis domains, zero policy and reasons for truncated ranges. SVG and editable PPTX come from the same FigureSpec; PowerPoint-exported PDFs are included as inspected previews. See [the research-figure upgrade plan](docs/SCIENTIFIC_FIGURE_GAP_AND_UPGRADE_PLAN_2026.md) for scope and remaining gates.

```bash
python tools/build_quantitative_examples.py
python tools/build_wine_scatter.py
python tools/build_image_quant_example.py
python tools/validate_scientific_ir.py
python tools/validate_quantitative_examples.py
python tools/validate_wine_scatter.py
python tools/validate_image_quant_example.py
```

The Iris charts use the public [UCI Iris dataset](https://archive.ics.uci.edu/dataset/53/iris) (CC BY 4.0, DOI 10.24432/C56C76). The second dataset is [UCI Wine](https://archive.ics.uci.edu/dataset/109/wine) (CC BY 4.0, DOI 10.24432/C5PC7J); its selected chemical measurements have no physical units reported by the source, and the chart says so on both axes. The image example uses the [CC0 scikit-image cell sample](https://scikit-image.org/docs/stable/api/skimage.data.html#skimage.data.cell), with documented 0.107 µm pixel spacing. The single-image pixel histogram is descriptive and does not imply biological replication or cell segmentation.

The 15-task benchmark contract is in `specs/research_figure_benchmark_v76.json`; all tasks have automated fixtures, including a three-slide defense deck, a publication-size figure and two Wine chemistry plots from a second public dataset. Its hard release gates require independent scientific and final-size review before a stable release. The [V7.6 completion audit](docs/SCIENTIFIC_FIGURE_V76_COMPLETION_AUDIT.md) maps the plan's acceptance criteria to current evidence and missing manual checks. `dist/render_record_v76.json` records source/output hashes, tool versions, observed embedded PDF font names and the remaining manual checks. Grayscale and approximate color-vision previews support visual inspection; independent review remains open.

`specs/output_profiles_v76.json` separates presentation QA from publication prerequisites. Fourteen FigureSpecs use the presentation profile. The [Q03 Nature-size example](docs/Q03_NATURE_PUBLICATION_CAPTION.md) re-lays out the same data and bootstrap summaries at 183 × 100 mm, with editable vector PDF and embedded Arial fonts. It is a production-size demonstrator; editorial and independent domain review remain pending.

The committed render record is checked with `python tools/validate_render_record.py`; it compares canonical SVG XML and PPTX package payloads after a CI rebuild, and verifies the committed PowerPoint PDF/preview hashes. `python tools/validate_render_semantics.py` checks scientific labels across SVG, PPTX and PDF. `python tools/validate_legacy_label_parity.py` compares all five migrated figures with their pre-V7.6 committed FigureSpec/SVG labels and the three historical C01 PPTX files, allowing only the documented publisher-source correction for the two SEANet redraws; B01/F07 historical PPTX files were not committed, so their current PPTX labels are compared with the old FigureSpec. This check needs full Git history. CI verifies the Windows PowerPoint export record and does not regenerate it on Linux.

## V7.5 — Academic presentation planning

The Skill now begins with a DeckSpec and ordered SlideSpecs. It records audience, time budget, claims, evidence, page roles, layout choices and speaker notes before figure production. FigureSpec topology and SourceStyleSpec visual anchors stay independent of the deck layout. See `docs/DECK_PLANNING_V75.md` and `specs/deck_spec_v75.example.json`.

The package remains a development baseline pending independent scientific and final-size review.

## C01 — Reproducible composite defense slide
A one-slide 16:9 layout restores the supplied V7.2 composition: two related figure panels stacked in the left column and a concise reading guide on the right. The lower diagnosis path is purpose-built for the narrow panel rather than uniformly shrinking a full-width figure.

Current deliverables (legacy V7.4 filenames retained):
- Editable PPTX: `dist/C01_composite_defense_slide_v74.pptx`
- PDF preview: `dist/C01_composite_defense_slide_v74_preview.pdf`
- Canonical spec: `figure_specs/c01/C01_composite_defense_slide.json`
- Editable SVG: `examples/C01_composite_defense_slide_v74.svg`

The V7.3/V7.4 filenames and FigureSpec `version` fields identify the layout lineage; the active scientific evidence contract is `schema_version: 7.6.0-dev` and includes the C01 source correction below.

Rebuild with `python tools/build_c01_v74.py` and validate with `python tools/validate_c01_v74.py`. The current development build has 241 native PowerPoint shapes and 46 text boxes. Automated checks found zero text-box intersections, out-of-bounds objects, picture objects and inherited theme shadows. `tools/export_c01_preview.ps1` exports the composite PDF/PNG and all three deck PNGs with Windows PowerPoint 16.0. The [C01 source correction](docs/C01_V76_SOURCE_CORRECTION.md) and [direct literature comparison](docs/C01_LITERATURE_COMPARISON_2026-11-07.md) record the source-visible routes, repaired FBG explanation and remaining evidence boundary; independent domain/final-size review remains pending.

## C01 — Two-slide detail version
The two-panel C01 method is also available as two separate source-aligned slides:
1. FBG construction: sensor signals → OCF/notch filter → band-pass filtering → B1/B2/B3/Bq subgraphs → connected total graph.
2. SEANet diagnosis: Input → GCN → pooling → GCN → pooling → SR → summation → Dense → fault class. EA feeds the first GCN; the first pooling also branches to a second SR that reaches the summation.

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
