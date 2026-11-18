# R1 source image clip implementation plan

> **For agentic workers:** Use superpowers:executing-plans for implementation and a fresh independent review. The user authorized continuous execution without interim approval requests.

**Goal:** Make the existing native PDF import preserve supported source image clip paths without private post-processing.

**Architecture:** A focused source SVG clip module produces transparent per-occurrence local image assets. The shared image collector invokes it before page cropping, and the native importer records the provenance. Existing generation and audit entrypoints remain in use.

**Tech Stack:** Python, PyMuPDF, python-pptx, Pillow, lxml, fontTools, ReportLab.

**Spec:** `docs/superpowers/specs/2026-11-18-r1-source-image-clips-design.md`

## Global constraints

- Keep the ten-paper sources and derivative figures private; public tests use synthetic PDFs.
- Do not overwrite first-pass or delivered candidates.
- Do not rasterize diagram vectors/text or promote model review to human approval.
- At least 576 dpi clip rendering, retaining higher source pixel density; 16 million pixels per image and 64 million per page maximum.
- Current remote baseline is `eed6c8d46f5fd3b240aa2080126f181f510dd608`; local archive snapshot SHA is different.

## Review focus

- An image repeated at the same location can have distinct clips; identity must preserve occurrence order.
- A source soft mask and a partially cropped source image must not lose alpha or be cropped twice.
- A curved or even-odd clip may keep the same bounds while removing visible pixels.
- Unrecognized transforms or compositing must fail visibly, not silently unmask pixels.
- Resource checks must happen before allocation, including cumulative work.

## Task 1: source-aware local clip preservation

Files: create `tools/pdf_image_clips.py` and `tools/test_pdf_image_clips.py`; modify `tools/pdf_source_assets.py` and `tools/pdf_figure_import.py` only where necessary.

- [ ] Add synthetic real-PDF tests for same-bounds circle clipping, repeated uses, source alpha plus partial crop, native neighbor preservation, and explicit unsupported/budget outcomes; observe the missing-clip failures.
- [ ] Implement `preserve_image_clips(page, events, source_pngs)` in the focused module, returning updated image events and structured diagnostics; preserve raw image pixels before page cropping.
- [ ] Extend image event/manifest provenance without changing existing imported native shape content.
- [ ] Run the new tests and the existing crop/import/audit suites; compare actual isolated image pixels to source rendering.

## Task 2: integrate and prove the real-paper improvement

Files: update `README.md`, `.github/workflows/validate-assets.yml`, `docs/DEVELOPMENT_EXPERIENCE_2026-11-18.md`, and the prior completed batch checklist.

- [ ] Document dependencies, behavior, supported boundaries and one existing-entrypoint command; include synthetic clip regressions in CI.
- [ ] Reimport PINN, EvoOntology and UCFNet to new private outputs; compare clip images/native-object retention with frozen delivered baselines and render actual results.
- [ ] Have an independent reviewer examine source correspondence, compositing and failure behavior; fix any material findings with regression tests.
- [ ] Record verified lessons, commit only public code/docs/synthetic tests, update PR20, and verify CI at its new exact head.
- [ ] Deliver the reusable code/result evidence and any necessary updated private regeneration instructions without claiming new blind acceptance.
