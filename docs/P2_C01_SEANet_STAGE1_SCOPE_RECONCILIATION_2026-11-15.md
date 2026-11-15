# C01-SEANet Stage 1 review — scope reconciliation and repair decision (2026-11-15)

## Frozen review record

The submitted Stage 1 supplement is retained as-is. Its corrected score is **12/24 (50.0%), FAIL**, replacing the earlier 17/24 PASS. The reviewed initial PPTX SHA-256 is `1fe3fd1c42b6ab5cec60485724b3d710325be78c60b5d671c6fd27f83bd01b85`.

The record is an AI technical review (`C01-AI-REVIEW-01`, GPT-6), not a human domain-expert attestation. It is useful for defect triage and blind-order evidence, but it does not satisfy the independent human final-acceptance gate.

## Scope reconciliation

The Stage 1 package correctly named the visible lower panel “Graph-level fault diagnosis framework”, but its protocol did not explicitly state that C01-SEANet is a **standalone excerpt of the lower SEANet panel**. This omission made the review scope ambiguous.

The repository's task contract separates three deliverables:

- `C01_FBG`: frequency-band graph construction (sensor signals, OCF/notch filtering, band subgraphs and total graph).
- `C01_SEANet`: graph-level diagnosis (input graph, GCN/pooling, EA and readout branches, summation and Dense classification).
- `C01_composite`: the combined two-panel method overview and cross-panel information flow.

Therefore the absence of the upper FBG-construction panel is **not, by itself, a defect in the C01-SEANet lower-panel deliverable**. Do not merge the FBG panel into the SEANet figure; that would duplicate the separately scoped C01-FBG deliverable. The SEANet figure must, however, disclose that it is an excerpt and point to the companion C01-FBG figure. The composite figure remains responsible for showing the complete two-panel connection.

This scope decision is grounded in `specs/research_figure_benchmark_v76.json`, `figure_specs/c01/C01_FBG_construction.json`, `figure_specs/c01/C01_SEANet_graph_level.json`, `figure_specs/c01/C01_composite_defense_slide.json`, and `docs/C01_V76_SOURCE_CORRECTION.md`.


## Stage 1 full-figure criterion and component boundary

The original Stage 1 review's corrective criteria explicitly require both `Graph Construction (Time-Frequency Graph)` and `Graph-level fault diagnosis framework` on one canvas, with the `Total graph` connection into the lower panel. A lower-panel excerpt can be reviewed as a component, but **cannot pass as a complete redraw of the original two-panel graphical abstract**.

The repository separates the work into three linked deliverables:
- `C01_FBG`: the upper frequency-band construction panel;
- `C01_SEANet`: the lower graph-level diagnosis panel excerpt;
- `C01_composite`: the complete two-panel redraw, including the Total graph → SEANet input connection.

Accordingly, the v7.4 SEANet artifact now states explicitly that it is **not the full graphical abstract**, identifies `C01_FBG_construction` as its companion component, and points to `C01_composite` as the complete two-panel view. The 12/24 Stage 1 FAIL remains unchanged. The full-figure corrective criterion must be evaluated against `C01_composite`, not by silently treating the lower-panel excerpt as a complete figure.

## Confirmed repair targets that remain in scope

1. **Input total-graph representation** — replace the single small flat network with a stacked multi-subgraph visual consistent with the source's stacked graph input. Keep node coordinates explicitly schematic; do not claim a numerical adjacency matrix.
2. **Pooling geometry** — replace both generic trapezoids with the source-like quadrilaterals whose left/right sides are vertical and whose top/bottom edges are slanted.
3. **Classification output** — restore five independent vertically stacked output squares, with the second square highlighted orange.
4. **Scope and provenance disclosure** — state that this is the SEANet graph-level panel excerpt and that FBG construction is presented separately in C01-FBG; retain the paper citation and DOI.
5. **Accessibility** — add non-empty, meaningful alternative text to all objects and a whole-panel description; preserve a logical reading order.

The original Stage 1 score and flags are not retroactively edited. In particular, the submitted `critical_scientific_error=true` and `undisclosed_image_processing=true` remain part of the historical record; a later reviewer must reassess them against the clarified task scope and repaired output rather than silently rewriting Stage 1.


## Round 02 contract correction

The first complete CI pass exposed a label-contract regression: the draft v7.4 repair had changed the source-critical output label from `fault class` to `Graph (fault) classification`. The standalone topology contract explicitly requires `fault class`; visual clarification must not silently rewrite a source-critical label. The label is restored, and the standalone topology validator is now called directly by `validate_c01_seanet_v74.py`, so this class of regression is caught by the focused repair test before the broader FigureSpec suite.

The subsequent repair test also caught an object-ID collision in the five-square output stack. The final v7.4 spec now reserves:
- `el_0058` for the invisible semantic grouping boundary carrying `semantic_id=class_output`;
- `el_0059` through `el_0063` for the five visible, independently editable squares;
- `el_0064` for the source citation and DOI.

The five squares remain separate native PowerPoint shapes; the semantic grouping boundary only supplies the source topology's `Dense → class_output` endpoint. The citation is retained as a separate editable text object. These ID assignments are covered by the v7.4 validator and object-level diff.

## Repair-round and acceptance policy

- Preserve the original first-pass PPTX and the already executed alignment-only round as immutable evidence.
- Execute the next structural repair as a new immutable round; save its PPTX, object-level diff, regression audit, render evidence, and SHA-256.
- Run automated structure, text, bounds, overlap, accessibility, and Office OOXML checks after the edit.
- Keep PowerPoint 2016 host verification separate from LibreOffice rendering.
- Final delivery PASS still requires an independent human reviewer. The submitted AI review is not counted as a human final review.

## Decision

**Proceed with the source-grounded local repair of C01-SEANet as a component excerpt; do not misrepresent it as the complete graphical abstract.** The two-panel completeness requirement is assigned to C01_composite, which must be independently reviewed together with its upper FBG panel and Total graph → SEANet input connection. The Stage 1 12/24 FAIL remains frozen; a new blind final-review packet must declare these separate scopes.


## 2026-11-15 source-label clarification

The accessible author-lab graphical abstract appears to label both readout blocks IR layer, while the public abstract uses sensitivity-aware readout (SR). The discrepancy is unresolved. The current source-reconciled standalone and composite preserve the visible IR label and disclose the abstract terminology; they do not claim a final terminology correction. The publisher high-resolution graphical abstract was not directly accessed.
