# MMGraph-Agent Figure Redraw Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate source-grounded, editable native-PowerPoint versions of MMGraph-Agent F1/F2/F3 without embedding an entire figure as one picture.

**Architecture:** Extract visible PDF marks with PyMuPDF, preserving order, bounds, colors and text; convert paths to editable PowerPoint freeform shapes and separate raster images to picture objects. Emit source/provenance and object-audit summaries. Keep source author PDFs out of the public repository.

**Tech Stack:** Python 3.12, PyMuPDF, python-pptx, Pillow, pytest/unittest-style script tests, OOXML package audit.

**Spec:** `docs/superpowers/specs/2026-11-13-mmgraph-figure-redraw-design.md`

## Global Constraints

- Never flatten a figure into one image; native labels and paths are required.
- No guessed chart figures or invented relations.
- Public GitHub may include generic import tools/tests/docs, not the original author PDF or extracted third-party imagery.
- Office 2016 visual compatibility remains unverified unless tested in that host.

## Review Focus

- Multi-subpath filled icon with holes: preserve visible region or report the gap in the audit.
- Long dashed border path: avoid thousands of separate primitive objects where a native dash shape is equivalent.
- PDF mathematical glyph: preserve text and font metadata; report substitutions and unrecognized Unicode.
- Image with soft mask: retain alpha and original placement as an independent image object.
- Dense chart arrows and microscopic labels: package-level validity must not be confused with readability at delivery size.

---

### Task 1: PDF-native import core

**Files:**
- Create: `tools/pdf_figure_import.py`
- Create: `tools/test_pdf_figure_import.py`

**Interfaces:**
- Consumes: `fitz.Document` page and output path.
- Produces: `convert_pdf_page(pdf_path: Path, pptx_path: Path, *, page_index: int = 0) -> dict`, summary keys `page_size_pt`, `native_shapes`, `text_shapes`, `picture_shapes`, `source_sha256`, `warnings`.

- [ ] **Step 1:** Write a failing synthetic-PDF test asserting a native editable rect, stroked line, text, bezier curve, and standalone raster image; assert page aspect ratio and extracted Unicode text.
- [ ] **Step 2:** Run `python tools/test_pdf_figure_import.py` and see the expected missing-import failure.
- [ ] **Step 3:** Implement PyMuPDF extraction and native PowerPoint conversion; preserve order, source coordinates, fill/stroke and soft-mask pictures. Limit unsupported content via auditable warnings.
- [ ] **Step 4:** Run importer tests and strict OOXML checks, then refactor without weakening the tests.
- [ ] **Step 5:** Commit converter and tests.

### Task 2: Source-specific audit and documentation

**Files:**
- Create: `tools/audit_imported_pdf_figure.py`
- Modify: `README.md` to document optional import pipeline and source/rights policy.

**Interfaces:**
- Consumes: source PDF, converted PPTX and importer JSON summary.
- Produces: report with original and candidate counts, source text comparison, page dimensions, full-figure raster prohibition, and feature warnings.

- [ ] **Step 1:** Add failing tests for swapped label, single full-page image, and dropped vector path.
- [ ] **Step 2:** Run tests to verify RED.
- [ ] **Step 3:** Implement audit, provenance and usage docs.
- [ ] **Step 4:** Run focused and baseline validators.
- [ ] **Step 5:** Commit audit/doc change.

### Task 3: Three source figures and visual QA

**Files:**
- Create locally (not public repo): `MMGraph_F1_editable.pptx`, `MMGraph_F2_editable.pptx`, `MMGraph_F3_editable.pptx`, JSON audit records, source PNG references and preview sheets.

**Interfaces:**
- Consumes: author TeX `F1.pdf`/`F2.pdf`/`F3.pdf` and Tasks 1–2.
- Produces: three independently editable candidate PowerPoint figures plus evidence states.

- [ ] **Step 1:** Convert F3 and compare source/candidate text, dimensions, visual paths; refine importer tests for observed issues.
- [ ] **Step 2:** Convert F1 and F2, retaining individual source photos/icons and ensuring no full-figure image.
- [ ] **Step 3:** Inspect SVG/PPTX/PDF/PNG outputs where supported; record image/line/text count, labels, missing text and compatibility constraints.
- [ ] **Step 4:** Verify package integrity and publish private deliverables, then create a GitHub PR for reusable code, not restricted original artwork.
