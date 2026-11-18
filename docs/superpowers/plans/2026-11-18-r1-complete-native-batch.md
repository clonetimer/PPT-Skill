# R1 complete native batch implementation plan

> For agentic workers: execute the user-authorized batch without interim acceptance requests. Use parallel isolated output directories and an integrated review.

**Goal:** Produce a source-grounded native editable candidate for each of the frozen ten figures with fresh rendering; record verified lessons in the repository.

**Architecture:** Reuse six existing vector imports. Rebuild four image-backed figures as semantic PowerPoint objects. Keep originals and earlier candidates unchanged; new versions carry source hashes, crop provenance, object inventories and explicit review limits.

**Tech Stack:** Existing PPT-Skill Python/PyMuPDF/python-pptx toolchain; LibreOffice rendering; XML and image audits.

**Spec:** User R1 ten-paper delivery requirement and tests/fixtures/blind10_source_regions_2026-11-14.json. Native diagrams follow supplied sources, without invented labels, edges or scientific results.

## Global constraints

- Frozen first-pass results and original source bytes are immutable. These ten are development regression data.
- Source PDFs, figure crops and private delivery assets stay outside the public repository.
- Automated/model checks are separate from external scientific review and actual PowerPoint 2016 testing.
- Each candidate renders in a fresh isolated directory and has its own artifact digest.

## Review focus

- Crop-visible image occurrences including repetitions must be retained; unrelated page images do not count.
- No whole-figure image may masquerade as native reconstruction.
- Missing glyphs require source evidence or narrow exact preservation, never a guessed operator.
- Check named nodes, labels and relationships against the original, independently of the authoring code.
- Inspect actual previews, bounds and editability, beyond file existence.

## Tasks

- [x] Restore exact ten source hashes, current branch docs and existing evidence.
- [x] Reconstruct Wind Turbine and attention-guided GIN as native diagrams in private output directories.
- [x] Reconstruct HarnessMM and IIoT as native diagrams in private output directories.
- [x] Reproduce crop-image audit failure with synthetic tests, implement correction and verify Agent and PoG.
- [x] Investigate EvoOntology missing glyph from original font/visual evidence and preserve the observed outline without inventing semantics.
- [x] Fresh-render all ten; inspect labels, topology and appearance; repair observed defects.
- [ ] Package ten editable figures, source comparisons, authoring files and honest status manifest.
- [ ] Run required checks; commit generic fixes, synthetic tests and lessons; verify CI at the exact new head.
- [ ] Persist and deliver the integrated batch with remaining external-review boundaries disclosed.
