# P1-01 ten-paper source-layout diagnostic replay — 2026-11-14

## Scope and evidence class

This is a **development-cohort source-page diagnostic**, not a new blind test and not a scientific/visual acceptance score. It uses the ten user-supplied PDFs, the frozen source SHA-256 values and the manually selected source pages from `tests/fixtures/blind10_first_pass_frozen_2026-11-13.json`.

The crop candidates are frozen in `tests/fixtures/blind10_source_regions_2026-11-14.json`. Each record now includes:
- source SHA-256 and 1-based page number;
- figure crop in PDF points;
- a distinctive source caption anchor.

All ten source hashes were checked locally. All ten crop rectangles are within their source pages, and each caption anchor has at least one complete text match inside its selected crop. The crop audit is now executable with:

~~~bash
python tools/audit_source_crop_manifest.py \
  --source-dir ./ten_papers \
  --manifest tests/fixtures/blind10_source_regions_2026-11-14.json \
  --output qa/source_crop_manifest_audit.json
~~~

The hash-locked replay refuses to proceed if the crop audit fails:

~~~bash
python tools/benchmark_source_layout.py \
  --source-dir ./ten_papers \
  --manifest tests/fixtures/blind10_source_regions_2026-11-14.json \
  --output-dir ./qa/source_layout_blind10
~~~

These are **manual crop candidates**, not inferred semantic ground truth. A human still confirms that each selected figure is the intended figure before downstream FigureSpec reconstruction.

## Corrected crop-selection findings

Two substantive selection errors were found during visual review of the original pages:

1. **PINN Tool Wear:** the previous crop ended at page y=480 and cut off the lower part of Figure 4, including the loss terms, convergence decision and legend. It now extends to y=666, enclosing the full three-panel figure and its caption.
2. **UCFNet:** the previous crop selected Figure 1 (multi-modal domain-generalization working conditions), although the target is the paper's architecture figure. It now selects **Figure 2, “Architecture of the proposed UCFNet”**, at page region [70, 565, 535, 775].

The other eight crops were extended where necessary to include their selected figure captions. The source crop fixture records the caption anchor for all ten.

## Crop-level source inventory

Counts below come from the current source-layout extraction logic over the corrected crop candidates. Drawing records and stroke segments are raw PDF primitives, **not semantic nodes or graph edges**. Image assets are recovered image paint occurrences, not unique scientific components.

| Figure | Page / crop [x0,y0,x1,y1] pt | Drawing records | Text spans | Image assets | Stroke-segment candidates | Large rectangles | Confirmed panels |
|---|---|---:|---:|---:|---:|---:|---:|
| Wind Turbine | 3 / [303.2,66.7,557.8,364] | 0 | 2 | 1 | 0 | 0 | 0 |
| PINN Tool Wear | 6 / [25,35,475,666] | 774 | 16 | 31 | 4,983 | 5 | 0 |
| Attention-guided GIN | 6 / [123.3,55.5,472.2,542] | 367 | 31 | 1 | 0 | 0 | 0 |
| Agent Distillation | 4 / [120.9,65.7,556.2,326] | 831 | 57 | 4 | 124,245 | 1 | 0 |
| EvoOntology | 3 / [53,55,558,306] | 327 | 271 | 74 | 737 | 4 | 0 |
| HarnessMM | 2 / [54,54,558,373] | 0 | 10 | 1 | 0 | 0 | 0 |
| IIoT Digital Twin | 5 / [45.5,55.4,549.8,373] | 0 | 2 | 1 | 0 | 0 | 0 |
| Paths-over-Graph | 4 / [60,90,550,355] | 338 | 90 | 7 | 2,998 | 1 | 0 |
| SkillSmith | 4 / [108,72,503.8,316] | 212 | 118 | 0 | 1,512 | 1 | 0 |
| UCFNet Figure 2 | 4 / [70,565,535,775] | 192 | 110 | 3 | 13,167 | 0 | 0 |

Source layout/style profiles also retain font-family counts and font-size tiers, palette counts, stroke-width tiers and clipping regions. Those measurements are preserved in each per-figure JSON output rather than reduced to one universal visual template.

### What the inventory changes

- Three crops are image-backed with no PDF vector drawing records: Wind Turbine, HarnessMM and IIoT. They should use an image-preserving route unless a separate source provides editable internals.
- Six crops contain both image assets and vector drawing records: PINN, Attention-guided GIN, Agent Distillation, EvoOntology, Paths-over-Graph and UCFNet. Their source images must not flatten or replace the independently recoverable vectors/text.
- SkillSmith is a vector/text source with no image assets in the selected crop.
- **GIN is not classified as image-only:** the corrected extraction sees 367 drawing records alongside one image asset. Those drawing records still need visual/semantic review before being treated as useful scientific objects.
- Distilling's 124,245 stroke segments include glyph outlines, chart marks and decorative paths. They are not 124,245 scientific relations; directedness remains undetermined.
- All ten crops currently have zero confirmed panels from PDF text markers enclosed by source rectangles. This does not mean the visible diagrams have no subpanels. PINN's (a)/(b)/(c) markers are image content; the UCFNet Figure 2 architecture is a single architecture figure with internal streams, not three separately labeled panels.

## Panel and relation inference boundary

Panel detection is intentionally conservative:
- only punctuated labels such as `(a)`, `b)` or `c.` are considered text markers;
- a marker becomes a confirmed panel only when an enclosing source rectangle contains it;
- a marker without a source boundary is recorded as unresolved;
- image-contained labels and unlabeled repeated panels remain candidates for the next clustering stage.

Graph semantics are also conservative:
- PDF line fragments are recorded as `stroke_segment_candidates`;
- each segment starts with `directedness: undetermined`;
- geometry, paint order and line direction alone do not prove arrow direction, data flow, causality or a scientific edge;
- a relation can be promoted only after checking arrowheads, legends, caption and source-derived topology.

## Reproducibility and CI

- Source PDFs remain private user material and are not committed to the repository.
- The fixture verifies the ten original SHA-256 values before extraction.
- The crop auditor checks source hash, page range, crop bounds, caption containment and non-caption visual content.
- The benchmark validates each emitted SourceLayout JSON against `specs/source_figure_layout.schema.json`, then writes per-figure JSON and JSON/CSV summaries.
- [CI #225 PASS](https://github.com/clonetimer/PPT-Skill/actions/runs/43555988938), including the source-layout extraction, crop-manifest and benchmark regression suites.
- The frozen ten-paper strict first-pass result remains **0/10**. This source-layout replay does not measure a fidelity improvement and the ten papers remain development regression data, not a new blind holdout.

## Next P1-01 increment

1. Cluster image and vector primitives into **unlabeled panel candidates**, using whitespace, repeated alignment, enclosure and image bounds with confidence scores.
2. Infer repeated-module alignment, relative spacing and hierarchy without promoting a visual grouping to a scientific relationship.
3. Compare candidate boundaries with the ten manually inspected crop sheets; record false merges/splits.
4. Add a review state that allows a human to accept, split or reject candidate panel boundaries.
5. Feed only accepted SourceLayout facts into FigureSpec drafting and vector/mixed/image route selection.

No automatic panel boundary or semantic edge is to be fabricated to make the extraction look complete.
