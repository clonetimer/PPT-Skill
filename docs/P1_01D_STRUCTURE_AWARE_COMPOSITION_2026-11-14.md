# P1-01D Structure-Aware Composition Manifest

## Command

```powershell
python tools/source_region_composer.py .\qa\source_layout.json .\qa\review.json .\qa\reconstruction_routes.json --output .\qa\source_composition_manifest.json
```

Inputs must share the same source PDF, SourceLayout hash, and human review hash. Stale route evidence is rejected and an existing output is removed before validation.

## What it produces

- One figure-level object inventory.
- One composition unit for each human-accepted panel or geometric region.
- Per-object class, source order, overlap ratio, bounds, treatment, and editability expectation.
- A single shared-object registry for objects crossing multiple reviewed regions.
- A deterministic source-order sequence; text spans without a native paint-order index remain in a stable secondary reading order.
- Blockers for unsupported/manual routes, unknown objects, stale hashes, and shared boundary objects.

## Route-specific treatment

| Route | Object treatment |
|---|---|
| `native_vector` | Keep vector primitives as editable shapes |
| `native_text` | Keep text spans as editable text |
| `mixed_native_picture` | Preserve image assets as pictures and vector/text as editable objects |
| `source_picture_only` | Preserve the original raster image as a picture |
| `unsupported_source` | Block composition |
| `manual_review_required` | Block composition until ownership is resolved |

A mixed route never authorizes flattening the entire panel. Shared objects are referenced once at figure level and block execution until their ownership is resolved.

## Existing importer reuse

`tools/pdf_figure_import.py` already reconstructs PDF vector paths, text spans, and raster image paint events as separate PowerPoint objects in source paint order. P1-01D does not create a duplicate importer. It creates the composition contract that a subsequent P1-01D2 importer audit can verify against the actual PPTX output.

## Safety and status

The manifest is not a PPTX and does not execute route recommendations. `execution_authorized` remains false. It does not infer scientific node identity, edge direction, or causal relations. A `COMPOSITION_PLAN_READY` status means only that the object inventory and route evidence are internally consistent; it is not a visual-fidelity or scientific-accuracy pass.
