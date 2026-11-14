# P1-02 Implementation Plan

**Goal:** Implement separate, evidence-backed reconstruction metrics with explicit denominators and not-comparable states.

## Task 1 — Object and order metrics

- [ ] Build on the P1-01D2 provenance annotations and composition manifest.
- [ ] Calculate source object recall, unexpected object rate, duplicate count, class accuracy, exact source-order rate, and Kendall tau.
- [ ] Fail closed on missing or duplicate object IDs.
- [ ] Keep unsequenced text out of paint-order scoring.

## Task 2 — Text fidelity metrics

- [ ] Extract PPTX text by source object ID.
- [ ] Implement Unicode-normalized CER without dropping Greek/math symbols or punctuation.
- [ ] Report exact text match, missing/extra spans, and font metadata separately.
- [ ] Add mutation tests for substitutions, deletions, insertions, and glyph replacement.

## Task 3 — Geometry metrics

- [ ] Define and validate source-PDF-to-slide coordinate transforms.
- [ ] Initially enable IoU/center/size metrics only for full-page imports with known transforms.
- [ ] Mark cropped, rotated, or otherwise ambiguous transforms as NOT_COMPARABLE.
- [ ] Add nonzero-origin and non-integer-scale fixtures before enabling crop geometry scoring.

## Task 4 — Visual and raster evidence

- [ ] Reuse existing rendered-page comparison outputs.
- [ ] Add raster aspect-ratio/crop metadata checks.
- [ ] Keep renderer/DPI and not-comparable cases explicit.
- [ ] Do not infer scientific correctness from visual similarity.

## Task 5 — CI, documentation, and replay

- [ ] Add metrics tests to standard CI.
- [ ] Run full Linux and Windows syntax checks.
- [ ] Document separate technical/scientific/host statuses and metric denominators.
- [ ] Replay the ten-paper development set only as debugging evidence; do not alter the frozen 0/10 first-pass baseline.
