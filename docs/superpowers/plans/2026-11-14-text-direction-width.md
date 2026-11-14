# Text Direction and Width Implementation Plan

> Execute inline using superpowers:executing-plans; no subagent tool is available.

**Goal:** Correct text reflection, condensed-font alias loss and host-driven reflow without reducing font sizes.
**Architecture:** Small changes to the existing importer and read-only audit, with the existing PDF comparison retained.
**Tech Stack:** Python, PyMuPDF, python-pptx; LibreOffice for local render evidence.
**Spec:** ../specs/2026-11-14-text-direction-width-design.md

## Global constraints
Preserve text, anchors, size and object counts. Keep PR Draft. No user PDFs or fonts in Git. Keep all scientific/visual thresholds and frozen 0/10 baseline unchanged.

## Review focus
Negative/vertical angles; AABB-equivalent reflection; Arial Narrow vs regular Arial; host autofit; physical page ratio vs raster rounding. Missing target-host fonts and development replays cannot prove blind/Office acceptance.

### Task 1 — Direction, width and host layout
- [x] Write failing direction/alias/autofit and mutation tests.
- [x] Verify RED against unchanged baseline.
- [x] Apply minimal importer and read-only audit fixes.
- [x] Run text/importer focused tests.

### Task 2 — Physical aspect comparison
- [x] Reproduce pixel-rounding false rejection and wrong-aspect false acceptance.
- [x] Compare physical dimensions before pixel resampling with unchanged tolerance.
- [x] Verify first-pass gate tests.

### Task 3 — Evidence and integration
- [x] Render frozen synthetic probes before/after and inspect actual directions and line reflow.
- [x] Replay two hash-matched development papers; record unchanged visual scores.
- [x] Run local discovery; record six errors from fixtures absent in the CI review archive, rather than claiming a clean full suite.
- [ ] Publish the scoped patch and verify complete repository CI for the new commit.

No plan step authorizes merging PR #10 or granting scientific/Office approval.
