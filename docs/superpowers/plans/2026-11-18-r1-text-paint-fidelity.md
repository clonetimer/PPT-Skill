# R1 Text Paint Fidelity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Independent evidence collection and bounded component implementation are delegated; the root integrates and reviews the final branch. The user's prior authorization covers execution without another approval pause.

**Goal:** Correct source paint ordering, missing text occurrences and incorrectly merged runs in the existing native importer, then update the complete ten-figure R1 delivery.

**Architecture:** A shared trace-first collector supplies explicit text events and source sequence numbers. The importer interleaves all native objects, while audits independently inspect actual shape order and verified source-outline geometry. Limited source glyph contours preserve UCF fill/stroke operators without changing ordinary editable text.

**Tech Stack:** Existing Python, PyMuPDF, python-pptx/DrawingML, fontTools, source SVG and LibreOffice export.

**Spec:** `docs/superpowers/specs/2026-11-18-r1-text-paint-design.md`

## Global Constraints

- Preserve frozen v1/v2 and raw failed evidence; no per-case user approval is required.
- Preserve every supported visible text occurrence; no set deduplication or global ligature normalization.
- Unsupported/ambiguous source paint fails explicitly; missing `.notdef` semantics stay unresolved.
- Private source/derivative assets stay outside public Git. No new blind-test or Office runtime claim.

## Review Focus

- Same Unicode/origin painted repeatedly around an occluding vector or image must retain every occurrence and source order.
- Dictionary-only extraction can omit a visible trace; coverage must start from source paints.
- Synthetic spaces, ligature continuations, anisotropic size and rotated baselines must not silently move or drop glyphs.
- Fill/stroke pairing must preserve both paints; unsupported curved glyph contours must fail rather than become ordinary fill text.
- Forged metadata or reordered actual shapes must not make paint-order audits pass.

## Task 1: Shared source events and limited outlines

**Files:** Create `tools/pdf_text_events.py`, `tools/test_pdf_text_events.py`, `tools/pdf_text_outlines.py`, `tools/test_pdf_text_outlines.py`.

**Evidence-driven addition:** Create `tools/pdf_drawing_events.py` and its focused tests to reconcile vector occurrences with bboxlog after a real UCF replay exposed empty-path sequence drift. Keep original drawing IDs and reject a merged fill/stroke record that spans another paint.

**Interfaces:** `collect_text_events(page, *, strict_crop_edges=False)` returns sorted `TextPaintEvent` records and stats. Records contain `source_id`, `seqno`, `source_seqnos`, `span`, `line`, `paint_type`, `chars`, `evidence`. `recover_text_outlines(page, event)` returns verified fill-path dictionaries (`paths`, `fill`, `opacity`, `source_seqnos`, `provenance`) or raises an explicit unsupported error.

- [x] Observe failing real-PDF tests for duplicate paints, trace-only visible A, vertical CSV, geometric gaps and fill/stroke preservation.
- [x] Implement bounded event collection with explicit crop/hidden/Unicode exceptions and finite source evidence.
- [x] Implement verified straight-contour source glyph recovery, including distinct fill and stroke colors; reject curves/ambiguous matches.
- [x] Run the focused suites and scan the six real source PDFs for concrete unsupported cases.

## Task 2: Importer and source audit integration

**Files:** Modify `tools/pdf_figure_import.py`, `tools/audit_text_geometry.py`, `tools/audit_imported_pdf_figure.py`; create `tools/test_pdf_text_paint_import.py` and audit regressions; add suites to existing CI workflows.

**Interfaces:** `_add_text_event(slide, page, event)` returns all emitted shapes. Ordinary text keeps `event.source_id`; outline shapes use `source_id + '__outline_' + index`. All carry source paint provenance, while audits verify actual native content and shape order against the source.

- [x] Run the importer red tests against the unchanged baseline.
- [x] Emit trace-derived runs, add verified native outlines where required, then order text/vector/picture shapes by their actual source paint sequence.
- [x] Update audits to use source events, inspect actual `spTree` order, validate outline geometry and reject old falsely passing candidates.
- [x] Run affected old/new suites, source-mutation negatives, compilation and whitespace checks. Keep failures by name; do not repeat known unrelated archive setup failures without a concrete reason.

## Task 3: Real figures, public code and complete delivery

**Files:** Update `docs/DEVELOPMENT_EXPERIENCE_2026-11-18.md`; keep real replay and versioned delivery outside the public worktree.

- [x] Freshly regenerate/render affected EvoOntology, SkillSmith and UCFNet candidates; inspect source/old/new local and full-figure comparisons.
- [x] Preserve source images, scientific content and established native repairs; record any text-object grouping changes and retained limitations.
- [ ] Independently review component failures and final native-object evidence, then push with the expected remote parent and verify exact-head CI.
- [ ] Rebuild the complete ten-figure package, verify all file/render bindings and unchanged-case hashes, save and deliver the batch.
