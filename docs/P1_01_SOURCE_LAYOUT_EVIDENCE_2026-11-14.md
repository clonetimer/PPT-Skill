# P1-01 source-first layout evidence extraction — 2026-11-14

## Implemented scope

The first P1-01 increment adds `tools/extract_source_layout.py`, the versioned contract `specs/source_figure_layout.schema.json`, and source-layout evidence in the unified `tools/reproduce_research_figure.py` pipeline.

The extractor records:

- source PDF SHA-256, selected page dimensions/aspect ratio and explicit crop rectangle;
- source-observed vector drawing bounding boxes and normalized positions;
- source text spans, recovered glyph-quad bounds, original font family, font size, direction and color;
- stroke widths, dash patterns, fill/stroke/text palette counts and font-size tiers;
- clipping scissor regions and independent image XRef/block occurrences with SHA-256 and crop/panel candidate;
- generic stroke-segment candidates with endpoints and source order; these are not asserted to be graph edges.

## Conservative inference boundary

Panel detection is **evidence-led**:
- an explicit single-letter panel marker such as `(a)` or `(b)` becomes a panel candidate;
- a large source rectangle containing that marker is accepted as its boundary with high confidence;
- a marker without an enclosing rectangle is retained as a low-confidence label-only candidate;
- no explicit markers means `NO_EXPLICIT_PANEL_MARKERS` and an empty panel list. The extractor does not divide a figure into invented panels just because several large rectangles exist.

Graph semantics are also conservative:
- line segments are recorded as `edge_candidates`;
- every candidate has `directedness: undetermined` and low confidence by default;
- a line's drawing order or geometric orientation alone is not proof of arrow direction, data flow, causality or a scientific edge;
- connector candidates must be checked against arrowheads, legends, the paper caption and source-derived topology before being promoted to FigureSpec `semantic_edges`.

The source image is not embedded into the public layout JSON; image entries contain XRef, visible bounds, source-order and content hash. Original author images and paper PDFs remain private user material.

## Pipeline integration

Every `reproduce_research_figure.py` run now attempts source-layout extraction **before** generating the candidate and writes:

- `source_layout.json`
- `source_preflight.json`
- `delivery_manifest.json` with the source-layout path, SHA-256, panel status/count, layout-element count, edge-candidate count and image count.

Select a page and crop explicitly:

~~~bash
python tools/reproduce_research_figure.py source.pdf \
  --output dist/figure-recovery --mode import --page 2 \
  --region 40 60 980 720 --render-host auto
~~~

Standalone extraction:

~~~bash
python tools/extract_source_layout.py source.pdf \
  --page 2 --region 40 60 980 720 \
  --output dist/source_layout.json
~~~

Page numbers in CLI are 1-based; PDF-point coordinates use the selected page's top-left origin. The Python API accepts zero-based page index.

## Tests and evidence

- 8 source-layout extraction tests cover explicit panel markers, no-marker conservative behavior, normalized coordinates, unknown edge direction, crop selection, font/stroke tiers, image provenance and JSON Schema validation.
- 10 end-to-end reproduction-pipeline tests include source-layout manifest integration.
- [Latest full CI #193 PASS](https://github.com/clonetimer/PPT-Skill/actions/runs/43553392378), commit `10c66d1c`, includes 8/8 source-layout tests and 10/10 pipeline tests plus the existing full validation workflow.
- Earlier failures #182–#192 were retained as red/green debugging evidence; they were caused by test expectation issues, zero-height PDF line bounds, and a missing test import. The latest passing run contains the corrected code and tests.

## Remaining P1-01 work

This is an initial evidence extractor, not yet a complete automatic panel parser:
- detect nested and unlabeled panel arrangements using stronger evidence than large rectangles alone;
- improve arrowhead/connector direction evidence without promoting uncertain lines to semantic edges;
- infer repeated module alignment/spacing and panel relationships with explicit confidence;
- replay the frozen ten-paper development cohort and compare panel/layout/style evidence to source crops; the cohort remains regression data, not a new blind holdout;
- feed accepted SourceLayout records into FigureSpec drafting and route selection instead of leaving them as a sidecar.

The frozen ten-paper strict first-pass success remains 0/10. P1-01 adds source evidence and prevents arbitrary layout assumptions; it has not yet demonstrated an increase in strict blind-test acceptance.
