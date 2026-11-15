# P1-01C Implementation Plan

**Goal:** Build an auditable, advisory reconstruction router for human-accepted panels and regions.

**Architecture:** Keep route logic pure and deterministic in `source_reconstruction_router.py`. It consumes SourceLayout and the validated human review output, intersects native PDF objects with accepted bounds, and emits route recommendations with evidence and `execution_authorized=false`. It does not modify FigureSpec or invoke a reconstruction executor.

## Task 1 — Extend review compatibility for visual regions

- [ ] Allow a visual region or label-anchored visual region to be human-accepted as a panel.
- [ ] Allow visual regions to be split into geometric child regions only.
- [ ] Preserve raw OCR marker and alignment-group restrictions.
- [ ] Add regression tests for human-only acceptance, assistant rejection, raw OCR rejection, and 1.0.0 compatibility.

## Task 2 — Implement evidence accounting and route selection

- [ ] Add pure geometry intersection/ratio helpers.
- [ ] Classify image-only, vector-only, text-only, mixed, empty, and boundary-ambiguous regions.
- [ ] Keep panel and geometric-region route scopes distinct.
- [ ] Record all source object IDs, source order, counts, overlap ratios, and decision reasons.
- [ ] Reject stale source layout/review hashes before writing output.

## Task 3 — Tests and CI

- [ ] Add route unit tests and hash-integrity tests.
- [ ] Add the new tests to the standard model-free CI suite.
- [ ] Run the full Linux and Windows syntax workflows.

## Task 4 — Documentation and evidence

- [ ] Document route classes, limitations, and CLI.
- [ ] Record CI results in the P1-01C ledger and PR #10.
- [ ] Keep P1-01C Draft until real paper replay and human scientific review are complete.
