# V7 Baseline — Known Visual and Engineering Issues

**Status: prototype only; not accepted as the target visual quality.** This file records defects visible in the V7 prototype so follow-up work can be measured against them.

## A01 — black-and-white academic framework
- Too dense for a defense slide: panel titles, paths, and annotations compete for attention.
- Dashed section boundaries are overused and visually dominate the content.
- Long horizontal/vertical connectors cross section boundaries and create ambiguous reading order.
- Some labels are too small relative to the 16:9 slide, while several boxes are oversized for their text.
- The redraw preserves selected semantic stages but is not a faithful layout reconstruction of the source page.

## A02 — reciprocal-rank fusion detail
- Ranking inputs and connectors crowd the fusion hub; line routing needs a clearer hierarchy.
- Secondary explanatory text is too small and visually weak compared with the main stages.
- Forward diagnosis, backward evidence validation, and final reciprocal-rank fusion need clearer separation.
- This is a content-detail diagram, not a verified reproduction of a specific published figure.

## B01 — engineering FDIR flow
- The four top-level stages are too evenly distributed and too generic; widths should reflect content and control responsibility.
- Connector labels sit too close to arrows; the feedback route is visually detached from state-management logic.
- NORMAL / RECONFIG / DEGRADED / SAFE states do not yet express transition conditions and guard semantics clearly enough.
- The bottom explanatory sentence is too low-contrast and too small for projection.
- It borrows the reference palette but is not yet a high-fidelity reproduction of the user's source slide.

## C01 — FBG-SEANet paper figure
- Sensor icons substitute for source imagery and change the visual character of the original graphical abstract.
- Frequency-band subgraphs and the total graph are schematic; exact node counts, edge patterns, and relative proportions are not claimed to match the source.
- The lower diagnosis pipeline is too generic and horizontally compressed. Branch routing, pooling representations, IR/readout details, and fusion placement need closer source-image comparison.
- Do not present this as a final high-fidelity paper-figure reproduction.

## D01 — style-profile overview
- Sample swatches are too small to communicate the actual figure grammar.
- Text hierarchy is weak; the cards themselves are too close to the generic-card style V7 is intended to avoid.
- This is a developer overview, not a final defense-slide design example.

## Production-engine gaps
- The repository has an SVG example generator and a PowerPoint audit script, but does **not yet** have one canonical FigureSpec that deterministically generates both SVG and PPTX.
- PowerPoint prototypes were assembled separately from the standalone SVG examples. Their visual equivalence is not guaranteed.
- Font substitution and line/arrow geometry have not been tested across Windows PowerPoint, LibreOffice, and macOS PowerPoint.
- Current audits do not detect text collisions, connector crossings, optical balance, or source-image similarity.
- A fixed minimum font-size rule is insufficient. Use a source-matched typographic scale plus a projection-readability check.
- SVG text depends on installed fonts; fallback can change glyph widths and line wrapping.

## Required V7.1 acceptance gates
1. A01: remove unnecessary dashed containers; rebuild reading order as a clear hierarchy; reduce cross-panel connectors; use a source-matched type scale.
2. A02: route connectors orthogonally without crossings; separate the three ranking paths; enlarge secondary explanations or move them to notes.
3. B01: encode transition guards and feedback semantics; position connector labels consistently; improve contrast and spacing.
4. C01: compare against the author-published graphic at the same aspect ratio; preserve source imagery only where essential and appropriate; match panel geometry and branch structure.
5. D01: replace generic cards with actual miniature examples of each visual grammar.
6. Implement a single FigureSpec source for SVG and PPTX; compare rendered outputs automatically.
7. Run cross-renderer tests and visual QA at presentation size.

## Baseline policy
V7.0 is a traceable baseline, not a visually accepted release. Do not mark it accepted. Improvements should be made in follow-up commits and measured against this issue list.
