# P1-02 First-Pass Reliability Improvements — 2026-11-14

## Changes implemented

### 1. Source text evidence now reaches the metric layer

The P1-01D composition manifest now carries each accepted text span's source text, font family, size, flags, color, and direction. This fixes an evidence gap where the metric layer previously saw an editable text object but lacked the source string needed to calculate CER.

### 2. Raster identity is checked, not just picture count

SourceLayout now records raster pixel dimensions alongside the source asset hash, PDF XRef, and transform. The PPTX importer stores the corresponding recovered asset hash, XRef, transform, and pixel dimensions in shape provenance metadata. P1-02 compares these independently and reports:
- source asset hash match/mismatch;
- pixel dimension match/mismatch;
- PDF transform match/mismatch;
- explicit `NOT_COMPARABLE` when source evidence is incomplete.

A picture count alone can no longer conceal substitution, re-encoding mismatch, or changed source placement metadata.

### 3. Preflight sees PDF image paint events, not only text-dictionary blocks

Some PDFs expose visible `fill-image` paint events and XRefs while `page.get_text("dict")` contains no image blocks. The first-pass gate now uses the same `collect_image_events` recovery path as the importer. It distinguishes:
- recovered source images;
- image-only figures;
- visible image events that could not be recovered.

Unresolved visible image events are high-severity preflight risks, preventing a partial/blank candidate from being mistaken for a safe native import.

### 4. One-command pipeline integration

When a valid human SourceLayout review is supplied to `reproduce_research_figure.py --mode import`, the pipeline now creates the advisory route file and composition manifest, then audits the actual PPTX and emits the multi-dimensional quality report. A blocked composition manifest is retained as a blocker and is not silently bypassed.

## Verification

- Added regression tests for text evidence propagation, raster hash/dimensions/transform, raster mutation, and image-paint-event recovery when text-dictionary image blocks are absent.
- Added an end-to-end pipeline test that creates a human review, runs the import pipeline, and checks that route, composition, PPTX audit, and quality metric reports are emitted.
- Latest full Linux validation and Windows PowerShell syntax status is tracked in [GitHub Actions](https://github.com/clonetimer/PPT-Skill/actions).
- Real PP-DocLayoutV3/PP-OCRv6 inference smoke is tracked as a separate job and is not conflated with the full validation job.

## Pass-rate claim boundary

These changes address known causes of false acceptance and missing diagnostics. They do **not** establish an improved first-pass success rate by themselves. The frozen ten-paper development set remains 0/10 under the strict first-pass rubric and cannot be reused as a blind holdout. A new, untouched paper cohort must be frozen before reporting a new success rate.
