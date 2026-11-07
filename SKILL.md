---
name: academic-defense-ppt
version: 7.6.0-dev
description: >
  Plan and build source-grounded academic defense slides and editable research figures.
  Use for 科研答辩PPT、论文图重绘、科研绘图、学术汇报, academic defense slides,
  scientific figure redraws, or data-driven research charts. A publication-size
  output requires a named journal target and final-size review. Excludes generic
  marketing decks and scientific claims without traceable evidence.
---

# Academic Defense PPT Skill

Produce technically accurate, readable academic-defense presentations. Select visual grammar from the actual source; do not impose a universal card template.

## Principles
1. Scientific topology, terminology, equations and evidence boundaries take priority.
2. Prefer editable vector graphics and native PowerPoint text/shapes; use raster only for genuine photographs.
3. Preserve source composition, panel order, proportions, arrows, branches, operators and line grammar.
4. Do not invent layers, edges, node mappings, equations or downstream blocks unsupported by the source.
5. Split dense mechanisms before shrinking labels.
6. Shadows are off by default. Reproduce them only when visible in the selected source, using explicit source-specific shapes; never inherit the PowerPoint theme shadow.
7. Distinguish source-visible redraws, paper/code-grounded reconstructions and domain adaptations.

## Workflow

1. Identify the audience, scientific claim, source files, delivery medium and final size. For a journal figure, record its current author-guide URL and production limits before layout.
2. Write the DeckSpec/SlideSpecs for a talk and a FigureContract for each figure. Mark source-visible, paper-grounded, domain-adapted or data-driven evidence and list unresolved claims.
3. Build ScientificIR from the source: critical nodes and edges, equations, row-level data or image processing history. Stop if a required claim has no traceable support.
4. Choose a source-matched style and arrange the panels. Preserve scientific relationships when changing layout between presentation and publication profiles.
5. Render SVG and editable PPTX from the FigureSpec; export PDF on the recorded PowerPoint host. Keep the raw data/image and transformation record with the output.
6. Run the schema, scientific, geometry, accessibility, cross-format and render-record checks named below. Resolve every machine-detectable failure before review.
7. Inspect the actual projection or print size and obtain independent domain review with the 14-task benchmark. Treat any hard failure or missing review as a release stop; ship only a clearly labeled development example until the release gate passes.

## Scope

The presentation profile supports projected defense slides. The publication profile re-lays out the same science for a named journal's final dimensions; its automatic checks are a technical preflight. Evidence status describes how directly a source supports the figure, separately from the output profile. This skill does not certify journal acceptance or make unsupported statistical, biological or engineering claims.

## Profiles
- A: black-and-white academic framework, Times New Roman, thin strokes and restrained section boundaries.
- B: engineering system flow, Microsoft YaHei, muted pastel modules, feedback and state transitions.
- C: source-matched journal/network figure, paper-specific typography, graph nodes/edges, sensor waveforms, pooling geometry, readout and fusion layout.

## FigureSpec
Canonical source is JSON under `figure_specs/`. Render SVG and editable native PowerPoint from the same FigureSpec. C01 primitives include text, rect, trapezoid, line, polyline, ellipse, sensor and graph. F07 also uses grid and stack_grid.

Before drawing, write a FigureContract with one defensible claim, output mode, evidence status and unverified items. Every FigureSpec element must have a stable ID, semantic role and evidence reference. Validate against `specs/figure_spec_v76.schema.json` and run `python tools/validate_scientific_ir.py`. For C01, the declared critical relations must agree with the visible directed connectors; see `specs/c01_expected_topology_v76.json`.

For quantitative figures, define source file/hash, row unit, variable units, sample size, transformations, chart kind, numerical axis domains and zero policy, and the meaning of each statistic/interval before rendering. Declare every derived axis/group field with its unit, source columns and calculation rule; do not let a renderer invent predicted labels or summary measures. Disclose why a numerical axis excludes zero. Use `specs/iris_charts_v76.json` for scatter, distribution, point interval, confusion matrix, ablation and trend interval examples; run `python tools/build_quantitative_examples.py` and `python tools/validate_quantitative_examples.py`. Preserve row-level links for raw points and calculation links for summaries; check plotted coordinates and summary geometry against their source values. Separate coincident or closely spaced raw points with bounded display-only offsets, keep summary marks clear of them, and disclose offsets in the caption; never silently hide observations. A preview chart is not evidence for an unprovided statistical claim.

For image panels, retain raw image hash and license, calibration, crop/stitch/LUT/intensity history, scale bar calculation, linked quantification and text descriptions. The CC0 cell example is built with `python tools/build_image_quant_example.py` and checked with `python tools/validate_image_quant_example.py`. A raster picture is permitted only for a disclosed source image, never as a flattened substitute for editable axes and annotations.

Use `presentation` for projection QA and `publication` only after checking the target journal's current final-size and file-format rules. Both modes use the same scientific relationships and source data. Record actual PDF renderer and manual final-size inspection separately from automated checks. See `docs/SCIENTIFIC_FIGURE_GAP_AND_UPGRADE_PLAN_2026.md`.
Run `python tools/validate_output_profiles.py` to enforce the declared presentation size and minimum text floor. The 9.5 pt floor is a preflight threshold, not proof of projected readability. Publication builds require a journal-specific target contract; see `specs/output_profiles_v76.json`.
For a concrete publication example, run `python tools/build_publication_example.py` after the Iris build, then validate `python tools/validate_publication_example.py`. The Q03 Nature-size panel reuses the same source rows and bootstrap summaries while changing layout and type size; its caption is in `docs/Q03_NATURE_PUBLICATION_CAPTION.md`.
Before delivery, run `python tools/validate_render_record.py` and `python tools/validate_render_semantics.py`. The first checks canonical SVG/PPTX payloads, the committed Windows PowerPoint PDF export attestation and embedded PDF font names against the requested family; the second compares rendered scientific labels across SVG, editable PPTX and PDF. Font-name checks cannot establish every glyph's appearance, so inspect the final-size output as well. Regenerate the export record only on the actual export host after running `tools/export_quantitative_pdf.ps1`.

For release evaluation, run `python tools/validate_research_benchmark.py` and apply the anchored six-dimension rubric and all hard failures in `specs/research_figure_benchmark_v76.json`. Every dimension must meet the stated score floor; no average score overrides a critical relation/value error, unclear source status, undisclosed image processing or unreadable content. Automatic checks are a preflight; record independent domain review separately.
Before naming a build stable, prepare an unfilled review file with `python tools/validate_release_readiness.py --prepare review.json`. Assign each of the 14 tasks to an independent reviewer whose declared expertise covers that task's benchmark discipline. Reviewers first inspect sources and figures without the benchmark expectations or implementation notes, recording task-level initial scores and evidence. They then inspect the specs and known traps, reconcile differences, and record source checks, six evidence-backed final scores, final-size inspection and hard failures. Run `python tools/validate_release_readiness.py --review review.json`; any missing review, mismatched reviewer field, changed SVG/PPTX/PDF/preview hash or hard failure blocks release. The gate verifies the review record, not the actual order of inspection. The in-memory tests in `tools/test_release_readiness.py` are synthetic and do not count as an actual review.
For a portable handoff, run `python tools/prepare_scientific_review_bundle.py --output review_bundle.zip`. It places sources and figures in `blind_review/`, then specs, expected findings and known traps in `unblind_review/`; the second stage is self-contained for validation. File names and source documents may still disclose the project version. The bundle includes an unfilled JSON template and does not assert reviewer approval.

## Deck planning (V7.5 draft)
Before drawing, create a DeckSpec with audience, time budget, narrative order, delivery requirements and ordered SlideSpecs. Each SlideSpec needs one defensible claim, source evidence/status, page role, layout, on-slide text and speaker notes. Keep FigureSpec scientific topology independent of style and page layout. Derive a SourceStyleSpec from 5–7 evidenced visual anchors. Follow `docs/DECK_PLANNING_V75.md` and validate the example contract with `python tools/validate_deck_spec.py`.

## C01 source-matched pattern
FBG: sensor rows and waveforms → OCF/notch filter → B1/B2/B3/Bq subgraphs → total graph.
SEANet: Input → GCN → pooling → GCN → pooling → SR; parallel Input → EA module → SR; both feed the summation node.
The paper text defines SR as sensitivity-aware readout. Sensor photographs may be replaced with vector silhouettes when vector-first output is required; disclose this. Graph coordinates remain schematic unless a numerical adjacency matrix is available.

## Composite defense-slide layout
When the user wants the complete method on one slide, use the V7.4 layout:
- Two related figure panels stacked in the left column.
- Reading guide, evidence boundary and citation in the right column.
- Reflow dense modules for the narrow panel; do not uniformly scale a full-width diagram.
- Keep the two-slide V7.3 version as the detail/teaching alternative.

## QA
Verify topology and terminology against the paper/caption/official code. Render the complete deck to PDF. Check text overlaps, clipping, out-of-bounds objects, SVG validity, raster objects and theme shadows. Do not claim pixel identity without high-resolution source and direct overlay.

Current C01 composite QA: 228 native shapes; 41 text boxes; zero text-box intersections, out-of-bounds objects, raster pictures and theme shadows. The five critical upper-panel relations and nine lower-panel relations are checked against visible connectors. Windows PowerPoint 16.0 PDF/PNG export was inspected.
