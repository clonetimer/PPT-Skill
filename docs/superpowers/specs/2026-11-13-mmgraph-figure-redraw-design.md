# MMGraph-Agent Figure Fidelity Redraw Design

## Intent

Reproduce the three supplied NeurIPS 2026 MMGraph-Agent figures as PowerPoint documents whose scientific labels, connectors, charts, and vector illustration objects remain editable. Evaluate layout fidelity separately from scientific fidelity and editing affordances. Preserve the original publication layout in the primary output; a projector-friendly adaptation is a separate product and must not silently replace this redraw.

## Grounded sources

- Luo et al., *MMGraph-Agent: Agentic Multimodal RAG via Cache-Inspired Multimodal Knowledge HyperGraphs*, arXiv:2611.10657v1.
- The author-posted arXiv TeX source includes separate `F1.pdf`, `F2.pdf`, and `F3.pdf`. These, rather than the compressed screenshots, are the source of geometry and text.
- F1: challenge/solution comparison, includes standalone raster icon assets.
- F2: composite results graphic, includes dataset thumbnails and logos; do not invent or recompute radar/bar values.
- F3: A/B/C method architecture; has vector drawing and text, with no PDF image objects.

## Approaches and decision

1. **Manual FigureSpec redraw.** Maximum semantic control and most editable structures, but slow and error-prone for thousands of source marks; accepted as a targeted refinement phase.
2. **Embed each source PDF as a picture.** High visual similarity but fails independent editability. Rejected.
3. **Source-native vector import plus semantic QA.** Parse each original page's drawing paths, text spans, and separate raster illustrations. Convert paths and text into independent native PowerPoint objects; retain only bona fide photographs/icons as individual picture objects. Then audit source labels, visible routes, source-vs-output appearance, and Office compatibility. **Selected** for the first implementation and all three candidates.

## Constraints

- No full-figure raster pictures; scientific labels, lines, hyperedges, charts, and boxes are individually editable objects.
- Keep original aspect ratio and figure composition. Do not impose the repository's generic card style or simplifications.
- Trace figure identity and source SHA-256. Do not bundle or publish the author's original source PDFs and embedded copyrighted thumbnails in the public repository.
- Output has no invented scientific relationships or data. An imported radar trace is a collection of editable vector marks, **not** an editable data-backed chart unless the source table is independently verified.
- Preserve vector object z-order and color/opacity wherever feasible. Record unsupported PDF features and any visible discrepancies.
- Validate PowerPoint package integrity, object counts, labels, geometry, and source image object boundaries. Local PDF/PNG comparison is required where a PowerPoint renderer is available. Do not claim a Windows Office 2016 visual test without one.

## Deliverables

- Reusable `tools/pdf_figure_import.py` CLI and test fixtures generated in memory, with a documented optional `PyMuPDF` dependency.
- Three source-aspect-ratio, editable PPTX redraw candidates and SVG/PNG source comparisons, stored as task artifacts rather than automatically checked into a public repository.
- A source-grounded audit for each candidate: labels/paths, native vs raster object counts, discrepancies, and render/Office evidence state.
- Integration instructions and regression checks in PPT-Skill; no declaration of 100% pixel equivalence until independently evidenced.

## Acceptance

Scientific relationships and numerals are source-derived, no full-page raster objects, source dimension/aspect ratio preserved, tests pass, PPTX opens as a valid package, and actual rendered comparison has no critical missing panel. Final score under the existing six-dimension rubric is explicitly distinguished from automated checks and requires independent domain and final-size review.
