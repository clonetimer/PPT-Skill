# GraphRAG single-slide skill trial

## Output and evidence

- Figure: `GR01_graphrag_flow`; 13.333 × 7.5 in presentation profile.
- Source and limits: `SOURCE.md`. This is a conceptual reconstruction from Microsoft GraphRAG documentation, not a pixel copy or a full implementation trace.
- FigureSpec contains one FigureContract, one hashed EvidenceRecord, 50 elements, and 11 declared scientific relations.
- Schema validation, scientific evidence validation, and visible-route geometry validation passed in `build.py`.
- PowerPoint exported the PPTX to PDF and a 1600 × 900 PNG preview. The preview was visually inspected.

## PPTX audit

- One slide, 61 native PowerPoint objects; 20 text boxes and 17 line objects.
- No picture objects, out-of-bounds objects, text-box intersections, or inherited theme shadow.
- Minimum font size: 10.5 pt (footer); diagram labels are 14.5 pt or larger.

## Interpretation

- Global and local branches are alternative query modes. The indexing artifacts are named in the index band and inside the relevant query boxes; the slide does not imply that both paths run for one question.
- Optional claim extraction and DRIFT search are outside this single-slide overview.
- No independent domain or actual-projection review was performed. This is a development test artifact, not a stable-release acceptance record.

## Critical review after comparison with the paper

The mechanical checks above do not establish publication-quality scientific communication. The 11 checked routes form separate indexing and query components: **no visible edge connects the indexed graph or community reports to the query-time consumers**. Global search compresses per-community responses and final reduction into one label; community hierarchy is named but not represented. Local search omits the visible ranking/filtering of entities, relationships, text units and community reports in the current implementation documentation. The figure is appropriate as an introductory presentation overview, but it should not be described as a paper-faithful method figure or a journal-ready illustration. See the original paper, Figure 1, at https://arxiv.org/pdf/2404.16130 and the Microsoft GraphRAG global/local search documentation linked in `SOURCE.md`.
