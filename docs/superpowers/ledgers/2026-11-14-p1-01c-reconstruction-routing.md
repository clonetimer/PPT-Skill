# P1-01C Execution Ledger

**Branch:** `feat/mmgraph-agent-figure-fidelity-20261113`  
**PR:** [#10](https://github.com/clonetimer/PPT-Skill/pull/10)

## Implemented

- Defined six advisory route classes: native vector, native text, mixed native/picture, source-picture-only, unsupported, and manual-review-required.
- Added deterministic source-object accounting using PDF bounding boxes, object IDs, paint order, and a 0.90 containment threshold.
- Added per-accepted-panel and per-accepted-region routing, plus a whole-figure overview route.
- Added hash-locked human review validation and fail-closed output behavior.
- Kept route execution disabled; no FigureSpec or scientific topology is modified.
- Extended human review so visual-region and label-anchored visual-region candidates may be accepted or split by a named human reviewer. Raw OCR markers remain ineligible.

## Verification

- Added tests for picture-only, mixed, native-vector, native-text, empty, ambiguous-boundary, stale-review, and duplicate image inventory cases.
- Added visual-candidate human acceptance and geometric split tests.
- Added both test modules to the standard Linux CI workflow.
- CI status is tracked at [GitHub Actions](https://github.com/clonetimer/PPT-Skill/actions).

## Remaining release gates

- Run the latest P1-01C Linux CI to PASS after the route fixture corrections.
- Complete a real ten-paper replay with human-verified panel routes and report precision/recall separately.
- Compare route recommendations against actual reproduction outcomes.
- Keep PR #10 Draft until the evidence-based routing is independently reviewed and the real PowerPoint 2016 host round-trip is complete.

No strict blind-test score change is claimed. The frozen first-pass baseline remains 0/10.
