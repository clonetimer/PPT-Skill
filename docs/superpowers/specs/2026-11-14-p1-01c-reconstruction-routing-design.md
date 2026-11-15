# P1-01C Evidence-Based Reconstruction Routing

**Status:** Implementation increment in Draft PR #10  
**Date:** 2026-11-14

## Objective

Select a reconstruction strategy for each human-accepted source panel or geometric region, and for the full figure when no panel-level review facts exist. The router must explain its recommendation using source PDF objects and must never silently rasterize or vectorize content.

## Inputs

- SourceLayout 1.0.0 or 1.1.0 JSON, hash-locked to the source PDF.
- Human review JSON validated through `validate_source_layout_review`.
- Native source object inventory: vector drawing records, text spans, and image assets.
- Optional visual evidence and source-object ownership records, which are supporting evidence only.

## Route classes

1. `native_vector`: editable vector primitives dominate the reviewed region and there is no raster image content.
2. `native_text`: native text is present without raster images or vector drawing primitives; preserve typography and text geometry.
3. `mixed_native_picture`: raster image content coexists with editable vector primitives and/or text spans.
4. `source_picture_only`: the region is represented by raster image assets without native text/vector content.
5. `unsupported_source`: no recoverable source object intersects the region.
6. `manual_review_required`: geometry/object ownership is ambiguous, region evidence is invalid, or the observed source composition is insufficient to choose safely.

## Evidence accounting

For each reviewed region:
- Count source image assets by intersection with the reviewed bounds.
- Count vector drawing primitives by intersection with the bounds.
- Count native text spans by intersection with the bounds.
- Record the object IDs, source order, and overlap ratio.
- Do not count a source object twice within a single route record.
- Objects that cross a reviewed boundary are listed as ambiguous and trigger `manual_review_required`; they are not forced into either adjacent panel.

Thresholds:
- Object overlap ratio is intersection area divided by source-object area.
- An object is inside a region only when overlap ratio >= 0.90.
- An object with positive overlap below 0.90 is boundary-crossing/ambiguous.
- A route can be automatically recommended only when every intersecting object is either fully inside or demonstrably outside the reviewed bounds.
- This is a route recommendation, not an execution authorization.

## Human review and safety

- Only review decisions validated by `validate_source_layout_review` may create panel/region route records.
- Raw OCR markers, model detections, alignment groups, and raster gutters are not accepted route subjects.
- A panel route requires a human-accepted panel. An accepted geometric region receives a region route, not a scientific-panel route.
- No route may alter FigureSpec geometry, scientific nodes, connectors, labels, or topology.
- No route may claim a raster image is editable or that a vector primitive is scientifically meaningful.
- The output is advisory. A later reconstruction executor must have a separate allowlist, budget, and fidelity gate.

## Output

A JSON audit contains source hashes, route scope, recommendation, counts, object IDs, boundary-crossing objects, reasons, and the explicit `execution_authorized: false` flag. Any invalid review or stale hash fails closed and produces no route file.

## Verification

- Unit tests for each route class, object boundary handling, text-only regions, mixed regions, empty regions, and stale/invalid review.
- Human-review tests ensuring visual panel candidates are accepted only by a named human reviewer with rationale and evidence locator.
- Full CI plus existing PDF import, FigureSpec, Office portability, and release-gate suites.
- No blind-test score change is allowed in this increment.
