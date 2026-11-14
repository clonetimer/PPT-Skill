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
- an explicit punctuated panel marker such as `(a)` or `b)` becomes a confirmed panel only when an enclosing source rectangle contains it;
- a marker without an enclosing rectangle is retained under `unresolved_markers`, not counted as a confirmed panel;
- no explicit markers means `NO_EXPLICIT_PANEL_MARKERS` and an empty panel list; markers without boundaries mean `NO_CONFIRMED_PANEL_BOUNDARIES` or `PARTIAL_PANEL_BOUNDARIES`. The extractor does not divide a figure into invented panels just because several large rectangles exist.

Graph semantics are also conservative:
- raw PDF line fragments are recorded as `stroke_segment_candidates`, not graph edges;
- each segment has `directedness: undetermined` and low confidence by default;
- a line's drawing order or geometric orientation alone is not proof of arrow direction, data flow, causality or a scientific edge;
- a stroke segment may be promoted to a FigureSpec semantic relation only after checking arrowheads, legends, the paper caption and source-derived topology.

The source image is not embedded into the public layout JSON; image entries contain XRef, visible bounds, source-order and content hash. Original author images and paper PDFs remain private user material.

## Pipeline integration

Every `reproduce_research_figure.py` run now attempts source-layout extraction **before** generating the candidate and writes:

- `source_layout.json`
- `source_preflight.json`
- `delivery_manifest.json` with the source-layout path, SHA-256, panel status/count, layout-element count, stroke-segment-candidate count and image count.

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

- 12 source-layout extraction tests cover explicit panel markers, no-marker conservative behavior, normalized coordinates, unknown stroke direction, crop selection, font/stroke tiers, image provenance, JSON Schema validation and the one-based CLI.
- 5 crop-manifest audit tests cover source hashes, page/crop bounds, caption containment, non-caption figure content and zero-height strokes.
- 3 hash-locked benchmark tests cover successful sidecars, hash mismatch and caption-outside-crop rejection.
- [Latest full CI #225 PASS](https://github.com/clonetimer/PPT-Skill/actions/runs/43555988938), including all three source-layout suites and the existing full validation workflow.

## Remaining P1-01 work

This is an initial evidence extractor, not yet a complete automatic panel parser:
- detect nested and unlabeled panel arrangements using stronger evidence than large rectangles alone;
- improve arrowhead/connector direction evidence without promoting uncertain lines to semantic edges;
- infer repeated module alignment/spacing and panel relationships with explicit confidence;
- cluster unlabeled/nested image and vector regions into reviewable panel candidates with confidence;
- infer repeated-module alignment and relative spacing without promoting visual grouping into semantic topology;
- feed only human-accepted SourceLayout facts into FigureSpec drafting and vector/mixed/image route selection instead of leaving them as a sidecar.

The frozen ten-paper strict first-pass success remains 0/10. P1-01 adds source evidence and prevents arbitrary layout assumptions; it has not yet demonstrated an increase in strict blind-test acceptance.


## Ten-paper development-cohort diagnostic

The ten-paper development-cohort replay now uses corrected figure crops and caption anchors. The audit found three image-backed crops without vector drawing records (Wind Turbine, HarnessMM and IIoT), six mixed image/vector crops (including GIN's 367 drawing records), and one vector/text crop (SkillSmith). PINN's crop was extended to include all of Figure 4; UCFNet was corrected from Figure 1 to Figure 2. Distilling contains 124,245 raw stroke-segment candidates; these remain source primitives, not semantic edges.

The crop manifest is hash-locked and caption-verified by `tools/audit_source_crop_manifest.py`; `tools/benchmark_source_layout.py` now refuses to replay if the source hash, crop bounds or caption anchor fail. It validates every emitted JSON against the SourceLayout schema. See [ten-paper source-layout replay notes](P1_01_TEN_PAPER_SOURCE_LAYOUT_REPLAY_2026-11-14.md) and the [hash-locked crop fixture](../tests/fixtures/blind10_source_regions_2026-11-14.json). Original PDFs remain local. This is development-cohort evidence, not a fresh blind holdout or a strict reproduction pass-rate improvement.
