# P1-01D Implementation Plan

**Goal:** Generate a source-grounded composition manifest for reviewed figure regions, preserving source object identity and editability boundaries.

**Reuse:** Existing PyMuPDF SourceLayout inventory, human review validator, P1-01C route file, and `pdf_figure_import.convert_pdf_page`. Do not create a second importer.

## Task 1 — Contract and pure object classification

- [ ] Define input provenance contract and route-file hash verification.
- [ ] Normalize SourceLayout objects into one unique figure-level inventory.
- [ ] Classify each object as image, vector, text, or unsupported.
- [ ] Assign each object to exactly one accepted panel/region only when containment is unambiguous.
- [ ] Record boundary-crossing and multi-region objects once in a shared-object registry.
- [ ] Preserve source paint order; text without paint order receives a stable secondary reading order.

## Task 2 — Route-specific composition units

- [ ] Build one figure-level composition record and per-reviewed-unit records.
- [ ] For native-vector, native-text, mixed, and picture-only routes, emit explicit object treatment and editability expectation.
- [ ] For unsupported/manual routes, emit blockers and no executable sequence.
- [ ] Preserve mixed objects separately; never flatten an entire region because it contains an image.
- [ ] Reject any route marked manual_review_required or unsupported_source.

## Task 3 — Fail-closed CLI and tests

- [ ] Add `tools/source_region_composer.py`.
- [ ] Add unit tests for all route classes, duplicate IDs, object order, shared boundary objects, stale hashes, and stale-output removal.
- [ ] Add tests to the standard Linux CI workflow.
- [ ] Run the full CI and Office 2016 PowerShell syntax checks.

## Task 4 — Documentation and integration boundary

- [ ] Document the manifest command and its advisory-only status.
- [ ] Record that the current PDF importer already preserves mixed native/image paint order.
- [ ] Keep actual PPTX provenance annotation and output comparison as P1-01D2, avoiding an unverified broad importer refactor.
- [ ] Do not promote blind-test results or close PR #10 before real-paper and Office 2016 validation.
