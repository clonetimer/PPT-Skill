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

## Source-first layout evidence

Before drafting or adapting a FigureSpec from an unfamiliar paper, extract a
source-observed layout record:

~~~bash
python tools/extract_source_layout.py source.pdf --page 1 \
  --region 40 60 980 720 --output out/source_layout.json
~~~

Before the ten-paper development replay, validate the frozen source hashes,
crop bounds and caption anchors:

~~~bash
python tools/audit_source_crop_manifest.py \
  --source-dir ./ten_papers \
  --manifest tests/fixtures/blind10_source_regions_2026-11-14.json \
  --output qa/source_crop_manifest_audit.json
~~~

The hash-locked replay refuses to proceed when this crop audit fails. The
manifest records caption anchors so a crop that cuts off the figure caption or
selects the wrong UCFNet figure cannot silently enter the regression run.

The record contains explicit panel-label candidates, source rectangle
enclosures, repeated rectangle alignment groups, interstitial bands, and
low-ink gutter candidates detected inside dominant raster figures. It also
records relative coordinates, source text/font anchors, stroke/fill palette,
clipping regions, image/XRef hashes and stroke-segment candidates. Unlabeled
regions and raster gutters are **review-only candidates**, not confirmed
panels. The extractor does not infer directed graph edges from line geometry
alone; relations remain unverified until source arrowheads, legends and
captions are checked.

To create a review file and explicitly accept/reject candidate regions:

~~~bash
python tools/source_layout_review.py template out/source_layout.json \
  --output out/source_layout_review.json
# Edit decisions, reviewer.name, rationale and evidence_locator in the JSON.
python tools/source_layout_review.py validate out/source_layout.json \
  out/source_layout_review.json --output out/source_layout_review_audit.json
~~~

Only a human reviewer can accept a panel or layout region. A source enclosure
can also be split at a reviewed horizontal/vertical PDF-point coordinate
(`decision: split_region`), producing **two geometric regions, not two automatic
scientific panels**. Raster gutters can be accepted only as layout regions.
Invalid reviews discard *all* acceptances, including otherwise-valid entries.

After validation, compile human-approved geometry into a versioned constraints
artifact; no uncertain source edge or raster gutter is promoted to a scientific
relation:

~~~bash
python tools/source_layout_constraints.py out/source_layout.json \
  out/source_layout_review.json --output out/source_layout_constraints.json
~~~

Use an explicit source-constraint-ID to FigureSpec-element-ID bindings JSON
with both source file hashes, then apply reviewed x/y/w/h bounds to a **new**
FigureSpec; all other scientific nodes, labels and semantic edges are retained:

~~~bash
python tools/apply_reviewed_geometry.py figure_specs/original.json \
  out/source_layout_constraints.json out/layout_bindings.json \
  --output out/figure_reviewed_geometry.json
~~~

The unified FigureSpec pipeline also accepts `--source-layout-bindings` and
records the revised FigureSpec and geometry audit hashes. See the
[reviewed geometry workflow](docs/P1_01_REVIEWED_GEOMETRY_BINDINGS_2026-11-14.md)
for invariants and evidence limits.

The unified reproduction pipeline accepts `--source-layout-review`, verifies the source
and SourceLayout hashes, and records accepted facts in its manifest. Invalid
or stale review files fail closed. A route recommendation (`native_only`,
`mixed_native_picture`, `source_picture_only`) is advisory and does not
override the actual importer report or the release gate. See [source layout evidence schema](specs/source_figure_layout.schema.json)
and [P1-01 implementation notes](docs/P1_01_SOURCE_LAYOUT_EVIDENCE_2026-11-14.md).

For a frozen ten-paper development cohort, replay source-layout extraction
with hash verification (the PDFs remain local and are not committed):

~~~bash
python tools/benchmark_source_layout.py \
  --source-dir ./ten_papers \
  --manifest tests/fixtures/blind10_source_regions_2026-11-14.json \
  --output-dir ./qa/source_layout_blind10
~~~

The runner stops on any source SHA mismatch and validates every emitted
SourceLayout JSON against the versioned schema. See the
[ten-paper crop inventory and panel-detection findings](docs/P1_01_TEN_PAPER_SOURCE_LAYOUT_REPLAY_2026-11-14.md).

The unified `reproduce_research_figure.py` entrypoint also emits
`source_layout.json` before generating the candidate, records its hash and
panel/element counts in `delivery_manifest.json`, and accepts a 1-based
`--page` plus optional PDF-point `--region`. For **PDF import**, the same
selected region is also applied to editable native objects, clipped source
images, text/structure audits and pixel-based source comparison. It is not
merely a source-layout sidecar. Use the original selected page's PDF points:

~~~bash
python tools/reproduce_research_figure.py source.pdf \
  --output out/figure-recovery --mode import --page 3 \
  --region 60 90 550 355 --render-host auto
~~~

The resulting slide has the crop's aspect ratio and dimensions. Invalid or
rotated-page crop requests fail closed. For editable imports, source glyphs
partly cut by the crop, stroke-width-only fringes and rotated/skewed image
objects cannot yet be reconstructed faithfully; these cases return an
explicit unsupported-source diagnostic. Enlarge the source crop or rebuild
the affected source element with a reviewed FigureSpec. `source_layout.json` remains an
evidence artifact, not a semantic FigureSpec or an automatic claim that a
line is directed.

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

For a source-visible PDF import, the gate now also runs a source-aware text
geometry and glyph audit. You can inspect it independently:

```bash
python tools/audit_text_geometry.py source.pdf out/source_editable.pptx \
  --report out/text_geometry.json
```

It distinguishes overlaps already present in the PDF from collisions newly
introduced by PPTX text-box geometry, reports inherited crop-edge text
separately from new overflow, verifies source/candidate text and font mapping,
and flags math/control glyphs that cannot be safely mapped. This audit is
read-only and is included in `figure_first_pass_gate.evaluate()`. See
[the P0-03 implementation and source-crop evidence](docs/P0_TEXT_GEOMETRY_AND_GLYPH_AUDIT_2026-11-13.md).

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


### Evidence-based reconstruction routing (P1-01C)

After human review, generate an advisory route audit for each accepted panel/region:

```powershell
python tools/source_reconstruction_router.py .\qa\source_layout.json .\qa\review.json --output .\qa\reconstruction_routes.json
```

The router distinguishes native vector, native text, mixed native/picture, source-picture-only, unsupported, and manual-review-required regions. It records object IDs and boundary overlap. It never executes a route or edits a FigureSpec; `execution_authorized` is always false.


### Structure-aware composition manifest (P1-01D)

After P1-01C has produced an advisory route file, build a source-object composition plan:

```powershell
python tools/source_region_composer.py .\qa\source_layout.json .\qa\review.json .\qa\reconstruction_routes.json --output .\qa\source_composition_manifest.json
```

The manifest keeps vector paths, editable text spans, and raster images separate, preserves source paint order, and identifies objects crossing multiple reviewed regions. It is a planning/audit artifact only; it does not execute reconstruction or modify a FigureSpec. The existing `pdf_figure_import.py` remains the PDF-to-PPTX importer.


### Imported PPTX provenance audit (P1-01D2)

After importing the PDF with the existing native importer, annotate each imported shape with its stable SourceLayout object ID and audit it against the composition manifest:

```powershell
python tools/pdf_figure_import.py .\paper.pdf .\qa\imported_figure.pptx --page 4 --report .\qa\import_report.json
python tools/audit_source_composition_pptx.py .\qa\source_composition_manifest.json .\qa\imported_figure.pptx --output .\qa\source_composition_pptx_audit.json
```

The audit checks object presence, uniqueness, expected object class, and source paint order. A pass does not establish visual fidelity, scientific correctness, or actual Office 2016 rendering.


### Multi-dimensional reconstruction metrics (P1-02)

Evaluate an imported PPTX against its composition manifest without collapsing editability, text fidelity, geometry, visual similarity, and scientific review into one score:

```powershell
python tools/reconstruction_quality_metrics.py .\qa\source_composition_manifest.json .\qa\imported_figure.pptx --output .\qa\reconstruction_quality_metrics.json
```

The report includes object recall, missing/duplicate IDs, object class, source order/Kendall tau, text CER, and geometry IoU when the coordinate transform is comparable. Cropped or unknown transforms are marked `NOT_COMPARABLE`. Scientific correctness and Office 2016 host rendering remain independent review gates.
