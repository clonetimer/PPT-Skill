# Ten-paper blind-test improvement backlog (2026-11-13)

> Status: planned, except **P0-00 evidence freeze committed**. This is the engineering follow-up to the user's genuine 10-paper trial, **not a claim that the improvements have been implemented**.
>
> Frozen source/first-pass metadata: [`tests/fixtures/blind10_first_pass_frozen_2026-11-13.json`](../tests/fixtures/blind10_first_pass_frozen_2026-11-13.json). Source PDFs and author imagery are user-provided; they are **not** redistributed in this public repository.

## Baseline and acceptance contract

- Source: **10 papers, one representative methods/architecture figure per paper**, not every figure in the papers. Locked implementation SHA: `47f034548aa05d617ad12bfec86efee70d5d2bd8`.
- Model-assisted **one-time FigureSpec construction**: editable PPTX 10/10, LibreOffice exports 10/10, OOXML preflight 10/10; **strict scientific/visual first-pass acceptance 0/10**, mean expert-style *model-assessed* rubric 18.2/24. Independent domain-human assessment is not complete.
- Rubric frozen for this cohort: six 0–4 dimensions (science, topology, visual, readability, editability, technical). Science **4/4**, each other dimension **at least 3/4**, sum **at least 21/24**, no critical relationship/numeric/data errors. **Do not relax to 18/24**.
- Failure concentration: visual 2/4 on every case; readability 2/4 on every case; science 3/4 on five cases; topological 3/4 on nine. Two FigureSpecs have text intersections (wind 2; GIN 5); HarnessMM has one out-of-bounds item.
- The source/candidate SSIM-style screening scores of 0.0092–0.0683 signal major layout differences, **not** calibrated perceptual-fidelity or domain-science scores. Comparing re-laid-out FigureSpecs against source crops must not be described as an exact-layout quality proof.
- Secondary **direct PDF import**, separate from FigureSpec reconstruction: four blank candidates (wind, GIN, HarnessMM, IIoT), one import beyond 120-second testing budget (Agent Distillation), five generated with notable text collisions / bounds; some source-faithful renders reached 0.7467–0.9051 global similarity but did not pass the strict acceptance gate.
- Input anomalies are observable: wind/GIN/HarnessMM/IIoT crop PDFs have `fill-image` paint events but **zero image blocks** in `page.get_text("dict")`; GIN has 367 regular vector drawings alongside its missing image block. Empty result must not be classified simply as “raster only”.
- **Data contamination rule:** These ten papers may be used for debugging/regression from now on. They **cannot** be used as a new blind hold-out for claims of improved first-shot generalization. Freeze a different untouched set before any later claimed success rate.

## Ranked backlog

| ID | Priority | Problem → Deliverable | Impact | Dependencies |
|---|---|---|---|---|
| **P0-00** | P0 · completed | Freeze provenance, scores, first-pass artifact hashes and immutable rubric in public metadata only | Protects valid comparison | none |
| **P0-01** | P0 · next | Crop-aware extraction of image XRefs, transforms, paint order and clipping; no blank-slide “success” | 4/10 direct imports blank | P0-00 |
| **P0-02** | P0 | Dense PDF resource budget / graceful abort / bounded segment conversion | 1/10 direct imports timeout | P0-00 |
| **P0-03** | P0 | Source-aware text geometry, glyph/fallback integrity and overlap repair with provenance | up to 55 overlaps in imported output | P0-01 |
| **P0-04** | P0 | Fail-closed zero-content/partial/hybrid validity and per-route QA statuses | prevents false first-pass passes | P0-01, P0-02 |
| **P1-01** | P1 | Extract source panel geometry / order / visual grammar into source-layout evidence before FigureSpec drafting | 10/10 visual=2 | P0-04 |
| **P1-02** | P1 | Evidence-based `vector/mixed/raster` route selection, non-flattening hybrid composition | vector fidelity plus local images | P0-01, P1-01 |
| **P1-03** | P1 | Native orthogonal/curved connectors, junctions and graph enclosures with source routing fidelity | PoG, EvoOntology, HarnessMM | P1-01 |
| **P1-04** | P1 | Network/experiment panels: data/tensor lanes, gated dual-stream, multi-panel insets, legends and image-with-vector annotations | PINN, GIN, UCFNet | P1-01 |
| **P1-05** | P1 | Typography and two-size profiles: publication at source figure dimensions vs projection-ready multi-slide derivative | 10/10 readability=2 | P0-03, P1-01 |
| **P2-01** | P2 | **Non-destructive** second-pass local repair engine, immutable first-pass output, object-level diff | correction-rate metric | P0-03, P1-02 |
| **P2-02** | P2 | Freeze new independent-papers holdout, six-axis blinded evaluation, Office 2016 host, measured improvement vs baseline | trustworthy first-pass rate | all P0, key P1 |

## Task-level implementation contracts

### P0-01 — Native crop-aware image and mixed-vector importer
**Files:** `tools/pdf_figure_import.py`; new `tools/pdf_source_assets.py`; new `tools/test_pdf_crop_assets.py`.

- **Consume:** a PDF, 1-based selected source page, selected clip rectangle and its original image XRefs/occurrence transforms. Preserve source paint-order `seqno`.
- **Produce:** independently editable picture objects **only for genuine source images**, native freeforms/labels for existing vector/text records, and an explicit `source_assets.json` trace of XRef, crop, clipping and object disposition.
- **Test first:** build deterministic cropped vector + image PDF; verify that `get_text("dict")` can lack the image while `get_images(full=True)`/`get_image_rects(xref, transform=True)` recover the asset; check no duplicate images, correct rotation/crop and source order. Privately replay wind/GIN/HarnessMM/IIoT locked files.
- **Definition of done:** the four previously blank cases become **nonempty with declared content**, or intentionally fail with `UNSUPPORTED_SOURCE` and a complete diagnostic; **never** silently return a blank slide as PASS. A full-image PPTX remains `RASTER_SOURCE_ONLY`, not `NATIVE_EDITABLE_RECONSTRUCTION`. GIN's known 367 drawings must not be discarded.

### P0-02 — Dense-vector budget and recoverable import
**Files:** `tools/pdf_figure_import.py`; `tools/figure_first_pass_gate.py`; new `tools/test_pdf_import_budgets.py`.
- **Interface:** `convert_pdf_page(..., max_drawings: int, max_vertices: int, max_seconds: float)` with audited, explicit defaults and event counts. The limits reject or subdivide clearly; no partial candidate may be mislabelled successful.
- **Test first:** synthetic high-path-count PDF, a single extreme Bezier, source long-run Agent Distillation case. Assert bounded execution and `RESOURCE_LIMIT` manifest; allow deterministic resume/partitioning without changing z-order.
- **Done:** long-run source is processed within a documented budget **or** exits with stable, machine-actionable failure instead of arbitrary 120-second trial timeout.

### P0-03 — Geometry and mathematical text reliability
**Files:** `tools/pdf_figure_import.py`, `tools/audit_pptx.py`; new `tools/audit_text_geometry.py` and `tools/test_pdf_text_geometry.py`.
- **Test first:** rotated tiny labels, source overlapping annotations, math glyphs (Greek/sub/superscript), fallback fonts, crop-edge labels; verify line/color reads never mutate unrelated OOXML shape attributes.
- **Done:** exclude intentional/source-overlapping glyph boxes from hard collision counts; zero **new unintentional** label intersections and no text clipped at page edges in target five completed import cases. Keep before/after bbox and font substitution evidence; do not fix readability by silently shrinking fonts.

### P0-04 — Strict route-aware release gate
**Files:** `tools/reproduce_research_figure.py`, `tools/figure_first_pass_gate.py`; new `tools/test_reproduction_release_gate.py`.
- **Statuses:** `STRUCTURE_FAIL`, `UNSUPPORTED_SOURCE`, `RESOURCE_LIMIT`, `NEEDS_SCIENTIFIC_REVIEW`, `NEEDS_VISUAL_REVIEW`, `TECHNICAL_PASS`; `FULL_ACCEPTED` requires recorded independent scientific assessment and Office host evidence if requested.
- **Test first:** empty PPTX, one full-page raster, cropped source with absent image block, missing math figure, no export host, synthetic high-similarity but wrong-edge FigureSpec. **Every incomplete case must fail closed.**
- **Done:** generated/exported/valid ZIP counts never count as fidelity passes. Keep source-visible vs FigureSpec-science-reinterpretation scoring separate.

### P1-01 — Source-first panel/layout/style IR
**Files:** new `tools/extract_source_layout.py` and `specs/source_figure_layout.schema.json`; extend `specs/figure_spec_v76.schema.json`.
- **Interface:** `extract_source_layout(source_page, figure_region) -> SourceLayout` with panel boundaries and order, relative module coordinates, text anchors, source color/stroke/dash/fill/font tiers, image/crop metadata, directed/undirected edge evidence and confidence markers.
- **Tests:** preserve source relative positions across non-16:9 figure aspect ratios; assert separate topological and visual contracts. Do not fabricate hidden nodes or turn a complex graph into a generic row of cards.
- **Done:** 10-paper regression shows verified panel boundaries and source-specific palettes/geometry; any unrecognized topology is `UNVERIFIED`, not invented.

### P1-02 — Composition policy: vector / mixed / raster
**Files:** new `tools/select_figure_route.py`; `tools/reproduce_research_figure.py`.
- **Tests:** source-rich vector remains native; photos and micrographs remain local picture objects with a source hash; labels and directional links around them remain independently editable; raster-only cannot claim full native editability.
- **Done:** route/evidence map per panel, no whole-slide bitmap misrepresented as editable, no disappearing experimental thumbnails, no semantic overpainting.

### P1-03 — Source-style connectors and graph enclosures
**Files:** `tools/render_figure_spec.py`, `tools/ml_figure_components.py`, `specs/figure_spec_v76.schema.json`; new `tools/test_graph_connectors.py`.
- **Tests:** 90-degree elbow with directed arrowheads, crossing nonconnectors, labelled curved relation, multi-in/multi-out junction, curved hyperedge enclosure, preserve graph edge direction and label attach; negative wrong-arrow tests.
- **Done:** verified relationships of PoG/EvoOntology/HarnessMM preserved and visible; no substitute regular grid for nonregular source graph.

### P1-04 — Dense method/experiment figure elements
**Files:** `tools/ml_figure_components.py`, `tools/render_figure_spec.py`; new `tools/test_dense_method_panels.py`.
- **Tests:** three-panel PINN acquisition→features→physics network; GIN shared representation→dual heads; UCFNet vibration/AE → attention/gating → uncertainty fusion; source figures/photos as localized images, statistics/legends from explicit source data.
- **Done:** evidence-backed panel proportions and label density match each selected source; no fabricated dataset values, physics formula or tensor dimensions.

### P1-05 — Readability and output profile
**Files:** `profiles/STYLE_PROFILES_V7.json`; `tools/audit_pptx.py`; new `tools/audit_final_size_readability.py`.
- **Tests:** source-paper sizing with correct original figure ratio; projection variant uses additional pages when labels would be illegible, preserves same scientific relation contract. Native Office export checked independently.
- **Done:** human final-size review can score readability ≥3/4 without source-layout distortion or formula clipping. No universal journal-sized font threshold for presentation slides.

### P2-01 — Minimal patch corrector
**Files:** new `tools/repair_figure_candidate.py` and `tools/test_repair_object_diff.py`.
- **Interface:** input frozen first-pass plus audited local fixes → `_revision_01.pptx` and `shape_diff.json`; never modify first-pass SHA.
- **Tests:** shifting one overlapping label changes only allowed shape IDs; font/line-read operations are read-only; source numeric data is immutable unless a separate explicit correction report is supplied.
- **Done:** separate first-pass rate vs one-repair rate; repaired output must not be retroactively counted as initial success.

### P2-02 — Second, genuinely unseen holdout and host
**Files:** `tools/benchmark_unseen_figures.py`, independent grading fixtures, `windows/Test-PowerPoint2016RoundTrip.ps1`; evidence-only bundle under a private destination.
- **Tests:** freeze **new** unseen user-licensed images before code is trained against them; run same fixed algorithm, target PDF host, blind six-dimension reviewers; record initial SHA and one-iteration SHA separately.
- **Done:** publish `strict_initial_pass / frozen_new_cases`, `strict_revision_pass / frozen_new_cases`, median scores, failure categories and confidence intervals. Office 2016 COM output is separate from Linux OOXML preflight. Proposed milestone target: **at least 5/10 first-pass on a new independent 10-figure set**, not a claim about the existing cohort.

## Critical release order

**Gate A (P0):** P0-01 → P0-02 → P0-03 → P0-04. No blank PPTX accepted, no hidden timeout, no false editable labels. Each task uses failing test → focused fix → full CI → own review, then promotes the shared source importer.

**Gate B (P1):** P1-01 → P1-02 → P1-03/P1-04 parallel → P1-05. Preserve source specificity: no mandatory corporate-card template.

**Gate C (P2):** P2-01 → P2-02. Do not combine revision gains with first-pass gains, or 10-paper development regression with new blind generalization.

## Review and non-goals

- The existing `tests/fixtures/blind10_first_pass_frozen_2026-11-13.json` is immutable except explicit append-only corrections with explanation; never replace the original hashes/scorecard.
- Do not upload the ten PDF sources or derivative author figures to the public GitHub repository. Store user-owned source bytes privately; repository carries test code, metadata, reproducible synthetic fixtures and links.
- Do not regenerate 10 visually simplified boxes and declare “10/10” based solely on successful PPTX export. Do not lower the strict rubric from 21/24 to 18/24.
- Do not treat image-only fallback as a full editable reconstruction; editable text/shapes must remain selectable in PowerPoint.
- Do not treat OOXML/LibreOffice checks as actual Windows PowerPoint 2016 host acceptance.
- For real held-out papers, model-assessed scores must be clearly separated from independent domain-expert scores.

## Evidence and related work

- Local 2026-11-13 ten-paper report, `qa/scorecard.csv`, `qa/visual_comparison.json`, immutable first-pass PPTX and FigureSpecs.
- Existing `docs/FIRST_PASS_FIGURE_FIDELITY_GATE.md` and `docs/SCIENTIFIC_FIGURE_REPRODUCTION_WORKFLOW_VNEXT.md`.
- Publisher requirements for editable vector figure layers and source-specific figure panels vary by target output; see [Nature figure construction](https://research-figure-guide.nature.com/figures/building-and-exporting-figure-panels/). Journal final-size font recommendations are **not** PowerPoint projection settings.
