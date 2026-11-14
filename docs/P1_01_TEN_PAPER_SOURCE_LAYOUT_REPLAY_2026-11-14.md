# P1-01 ten-paper source-layout diagnostic replay — 2026-11-14

## Scope and evidence class

This is a **development-cohort source-page diagnostic probe**, not a new blind test and not a scientific/visual acceptance score. It used the ten user-supplied PDFs, the frozen source SHA-256 values and the selected page numbers from `tests/fixtures/blind10_first_pass_frozen_2026-11-13.json`.

Manual crop candidates are frozen in `tests/fixtures/blind10_source_regions_2026-11-14.json`. They are based on source-page visual inspection and PDF image/vector extents; they still require human confirmation before being treated as definitive figure crops.

The preliminary probe used PyMuPDF page drawings, text spans, image XRef occurrences and rectangle boundaries. Counts below are raw source primitives inside each proposed crop, not semantic nodes/edges.

## Crop-level source inventory

| Figure | Page | Visible drawing records | Text spans | Image occurrences | Raw line segments | Large rectangle candidates | Confirmed panels | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Wind Turbine | 3 | 0 | 0 | 1 | 0 | 0 | 0 | Source is a single embedded image |
| PINN Tool Wear | 6 | 477 | 8 | 30 | 2,806 | 5 | 0 | Mixed image/vector, three visually distinct subpanels; panel labels are not exposed as PDF text spans |
| Attention-guided GIN | 6 | 0 | 0 | 1 | 0 | 0 | 0 | Source is a single embedded image |
| Agent Distillation | 4 | 827 | 53 | 15 | 124,242 | 1 | 0 | Dense mixed figure; requires resource-aware reconstruction |
| EvoOntology | 3 | 317 | 270 | 74 | 727 | 4 | 0 | Dense mixed vector/image composition |
| HarnessMM | 2 | 0 | 0 | 1 | 0 | 0 | 0 | Source is a single embedded image |
| IIoT Digital Twin | 5 | 0 | 0 | 1 | 0 | 0 | 0 | Selected top figure crop; off-crop page image excluded |
| Paths-over-Graph | 4 | 308 | 85 | 9 | 2,969 | 1 | 0 | Mixed vector/image graph architecture |
| SkillSmith | 4 | 196 | 114 | 0 | 1,492 | 1 | 0 | Vector-only architecture composition |
| UCFNet | 4 | 57 | 30 | 17 | 13,496 | 0 | 0 | Mixed architecture crop; one unbounded `(b)` marker remains unresolved |

The four image-only figures confirm why P0-01's `source_picture_only` classification matters: a correct visual recovery does not create editable internal nodes. PINN, Distilling, EvoOntology, PoG and UCFNet are mixed-content candidates; SkillSmith is a vector/text candidate.

**Raw line-segment counts are not semantic edge counts.** Distilling's 124,242 line segments include chart contours, glyph outlines and decorative paths; they cannot be interpreted as 124,242 scientific relations. The public schema therefore calls them `stroke_segment_candidates` and keeps directedness undetermined.

## Panel-detection result and corrective rule

The first diagnostic pass found that a loose one-letter regex could classify isolated math glyphs and page furniture as panel labels. The rule is now strict: only punctuated labels such as `(a)`, `b)` or `c.` are considered explicit markers. A marker becomes a **confirmed** panel only when an enclosing source rectangle contains it. A marker without such a boundary is recorded under `unresolved_markers`, not counted as a panel.

This deliberately yields zero confirmed panels in the current ten proposed crops. That does **not** mean the papers have no subpanels: PINN has visually distinct panels embedded in raster/image content, while UCFNet contains a low-confidence `(b)` marker without an enclosing PDF rectangle. P1-01's next increment is image-cluster and repeated-layout candidate detection, with confidence labels, rather than inventing boundaries.

## Reproducible local replay

The source files are not committed to the public repository. After placing the exact ten PDFs in a local directory, run:

~~~bash
python tools/benchmark_source_layout.py \
  --source-dir ./ten_papers \
  --manifest tests/fixtures/blind10_source_regions_2026-11-14.json \
  --output-dir ./qa/source_layout_blind10
~~~

The tool verifies all ten SHA-256 values before extraction, validates each output against `specs/source_figure_layout.schema.json`, and writes per-figure JSON plus JSON/CSV summaries. A hash mismatch stops the replay. This ten-paper set is now development regression data, not an untouched holdout.

## Current result and next work

- Source-layout extractor, schema and pipeline sidecar are implemented.
- Crop selection is recorded as `explicit_user_crop`; a full-page default is explicitly marked `full_page_default`.
- Panel markers without a source boundary remain unresolved.
- Generic PDF strokes are not promoted to semantic edges.
- The strict ten-paper first-pass score remains **0/10**; source-layout extraction alone does not prove an improvement in reproduction fidelity.

Next: cluster local image/vector elements into **unlabeled panel candidates**, infer repeated module alignment and relative spacing with confidence, then feed only reviewed SourceLayout facts into FigureSpec drafting and mixed/native route selection.
