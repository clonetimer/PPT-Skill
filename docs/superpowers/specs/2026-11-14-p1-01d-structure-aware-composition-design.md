# P1-01D Structure-Aware Figure Composition

**Date:** 2026-11-14  
**Status:** Design baseline for implementation in Draft PR #10

## Objective

Turn the P1-01C advisory route output into a deterministic composition plan that preserves source object identity, source paint order, panel ownership, and editability boundaries. The first increment is a verified composition manifest and importer alignment audit, not automatic semantic redrawing.

## Existing capabilities to reuse

- `pdf_figure_import.convert_pdf_page` already reconstructs native PDF paths, text spans, and raster image paint events as editable PowerPoint shapes/pictures in original source paint order.
- `pdf_source_assets.collect_image_events` recovers image XRefs and their source transforms.
- `SourceLayout 1.1.0` already records text, vector, image, and visual candidate geometry.
- `source_layout_review.validate_source_layout_review` provides hash-locked human-approved panel/region bounds.
- `source_reconstruction_router.build_reconstruction_routes` provides per-region route recommendations and object overlap evidence.

Do not create a second PDF-to-PPTX importer. Reuse the existing importer as the native/mixed composition backend.

## P1-01D deliverable

Add `source_region_composer.py` which consumes:
1. SourceLayout JSON,
2. the matching human review JSON,
3. the P1-01C reconstruction route JSON.

It emits a hash-locked `source_composition_manifest.json` with:
- figure-level composition record;
- each human-accepted panel and geometric region as a distinct composition unit;
- source object inventory per unit, with object ID, source order, object class, overlap ratio, and intended treatment;
- shared/cross-boundary object registry, never duplicated into two panel units;
- route-specific editability expectations;
- warnings and unresolved blockers;
- a deterministic source-order execution sequence.

## Composition policies

### native_vector
- Preserve each source PDF vector primitive as a separate editable shape/path.
- Preserve original fill, stroke, opacity, dash, clipping, and source order.
- Do not infer scientific object identity from path geometry.
- If an unsupported PDF primitive is present, record a blocker rather than rasterizing the entire region.

### native_text
- Preserve native text spans as editable text boxes.
- Retain source text, font family, size, flags, color, orientation, and glyph bounds.
- Text extraction uncertainty, missing glyph mapping, or severe crop clipping is a blocker.

### mixed_native_picture
- Keep native vector/text and image assets as separate objects.
- Preserve the original paint order across all object types.
- Never flatten the entire region merely because a raster asset exists.
- Raster objects remain picture objects; vector/text remain editable.

### source_picture_only
- Preserve the source image crop at its original aspect ratio and resolution.
- Do not claim internal image content is editable.
- Crop and transform must be verified; skew/rotation requiring unsupported transform is a blocker.

### unsupported_source / manual_review_required
- Do not generate an executable composition sequence.
- Retain the diagnostic evidence and require human resolution.

## Object ownership and paint order

- Every source object is represented exactly once in the figure-level inventory.
- An object with overlap >= 0.90 and no crossing may be assigned to one reviewed unit.
- Objects crossing a reviewed boundary are registered as `shared_boundary_objects`; they are not copied to both panels.
- If an object intersects multiple accepted units and cannot be assigned uniquely, the manifest is blocked.
- Text spans with no PDF paint sequence remain in a stable secondary ordering by page reading geometry and object ID; they must not be falsely interleaved with paint-order indices.
- The figure-level sequence follows PDF source order. Panel-level lists are references to the same figure-level object IDs.

## Fidelity and editability contract

The manifest states expected object classes, not verified output results. A later importer audit must compare:
- expected vs actual editable vector shape counts;
- expected vs actual text shape counts;
- expected vs actual picture counts;
- source object order vs PPTX shape order;
- per-region bounds and aspect ratios;
- missing/duplicated/unsupported object IDs.

A native/mixed route cannot pass if source vector/text objects were flattened into a picture. A picture-only route cannot pass if the picture is distorted or replaced with a fabricated vector approximation.

## Safety

- This stage does not alter FigureSpec or scientific topology.
- It does not execute route recommendations.
- It does not duplicate shared source objects.
- It does not treat a PDF object as a scientifically meaningful node/edge.
- Any stale source/review/route hash fails closed and removes stale output.
- `execution_authorized` remains false until a separate executor and fidelity gate are implemented.

## Validation

- Deterministic tests for each route class and object treatment.
- Exactly-once object inventory and source-order stability.
- Boundary-crossing and multi-region overlap blocks.
- Hash mismatch and stale-output deletion.
- Route/source/review provenance consistency.
- CI must run without PaddleOCR or model weights.
- Real paper replay must separately compare the manifest with actual PDF-imported PPTX objects.

## Later increment

P1-01D2 will add provenance annotations to imported PPTX shapes (stable source object IDs, route-unit IDs, source order) and an output audit. It must reuse the existing `pdf_figure_import` implementation and must not change its geometry semantics without dedicated regression fixtures.
