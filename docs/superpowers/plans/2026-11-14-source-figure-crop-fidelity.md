# Source-figure crop fidelity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make a selected source PDF figure crop the single geometric basis for native import and quality audits.

**Architecture:** Centralize PDF crop validation/application in a small helper, thread the same optional `figure_region` through the importer and source auditors, then connect the production pipeline and source comparison. Keep the source PDF immutable and original provenance.

**Tech Stack:** Python 3.12, PyMuPDF, python-pptx, Pillow, unittest.

**Spec:** `docs/superpowers/specs/2026-11-14-source-figure-crop-fidelity-design.md`

## Global Constraints

- Preserve immutable first-pass ten-paper baseline, 0/10 strict acceptance.
- No false native-editability or science/visual/Office 2016 acceptance claims.
- One optional `figure_region` in original selected-page PDF points; no fallback to full page on invalid input.
- Original source files remain untouched and are not committed to the public repository.

## Review Focus

- A vector and text entirely outside the crop must not appear on the slide or in label audit.
- A crossing shape or image must be clipped and remain within new slide bounds.
- A heavily populated full page with a simple crop must not hit drawable count budget for invisible paths.
- Bad crop coordinates or rotated pages must fail rather than silently generate a full page.
- Old preview diff files must not survive a later run that does not produce a comparison.

---

### Task 1: Common crop contract and editable PDF import

**Files:**
- Create: `tools/source_figure_crop.py`
- Modify: `tools/pdf_figure_import.py`
- Test: `tools/test_pdf_figure_import.py`

**Interfaces:**
- Produces `apply_figure_region(page: fitz.Page, figure_region: tuple[float,float,float,float] | None) -> list[float] | None`.
- Extends `convert_pdf_page(..., figure_region=None) -> dict`, reporting crop and cropped slide dimensions.

- [x] Step 1: Add real PDF tests with off-crop vectors/text/image, crossing strokes and invalid crop; assert editable objects and selected slide bounds. A separate dense-outside test proves visible-only resource preflight.
- [x] Step 2: Run `python -m unittest tools/test_pdf_figure_import.py -v` and record the expected failing tests.
- [x] Step 3: Implement validated in-memory crop; filter invisible drawing records for resource preflight while retaining source clipping and paint order.
- [x] Step 4: Re-run importer tests and confirm all pass.

### Task 2: Audits and pipeline use the same crop

**Files:**
- Modify: `tools/figure_first_pass_gate.py`, `tools/audit_imported_pdf_figure.py`, `tools/audit_text_geometry.py`, `tools/reproduce_research_figure.py`
- Test: `tools/test_reproduction_pipeline.py`, `tools/test_figure_first_pass_gate.py`
- Document: `docs/BLINDTEST_10PAPER_IMPROVEMENT_BACKLOG_2026-11-13.md`

**Interfaces:**
- Extends `source_profile(..., figure_region=None)`, `audit_figure(..., figure_region=None)`, `audit_text_geometry(..., figure_region=None)`, and `compare_rendered_pages(..., source_region=None)`.
- Existing `run_pipeline(..., figure_region=None)` passes region to all import-route consumers and preserves original-page manifest fields.

- [x] Step 1: Add end-to-end off-crop integration and true pixel-region comparison tests; add stale-diff cleanup regression.
- [x] Step 2: Run `PYTHONPATH=tools python -m unittest tools/test_reproduction_pipeline.py tools/test_figure_first_pass_gate.py -v` and confirm expected failure.
- [x] Step 3: Connect region through source preflight, import, structural/text audits, render comparison and manifest; clear stale diff.
- [x] Step 4: Re-run target tests, then full discovery (`PYTHONPATH=tools`, existing `.testtmp` directory). 265 tests passed; final repository validations and commit follow.
