# P1-02 Reliability Increment Ledger — 2026-11-14

- Fixed source text evidence propagation from SourceLayout through the composition manifest so CER is computed against the actual source text.
- Added raster source hash, XRef, PDF transform, and pixel-dimension provenance to imported image shapes.
- Added raster identity/dimension/transform comparisons and mismatch tests.
- Changed source preflight to recover images from PDF paint events/XRefs instead of relying only on text-dictionary image blocks.
- Added a high-severity unresolved-visible-image risk to prevent incomplete import from passing silently.
- Integrated P1-01C routes, P1-01D composition manifest, PPTX provenance audit, and P1-02 quality metrics into the one-command import pipeline when a valid human review is supplied.
- Added an end-to-end pipeline regression test for the reviewed import path.
- No rubric changes; strict frozen ten-paper first-pass baseline remains 0/10. No new blind success rate is claimed.
