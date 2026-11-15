# P1-01C Evidence-Based Reconstruction Routing

## Purpose

After the source PDF has been extracted and a human reviewer has accepted panel/region bounds, generate an auditable recommendation for how each reviewed area should be reconstructed.

## Command

```powershell
python tools/source_reconstruction_router.py .\qa\source_layout.json .\qa\review.json --output .\qa\reconstruction_routes.json
```

The command fails closed when the review is stale, invalid, or contains no human-accepted facts. Any existing output file is removed before validation, so a stale route file cannot be mistaken for a current result.

## Route classes

| Route | Evidence condition | Suggested treatment |
|---|---|---|
| `native_vector` | Vector primitives without raster content | Preserve native editable paths |
| `native_text` | Native text spans only | Preserve text and glyph geometry |
| `mixed_native_picture` | Raster images plus native vector/text objects | Keep raster and editable objects separate |
| `source_picture_only` | Raster image assets only | Preserve the source crop as a picture |
| `unsupported_source` | No recoverable objects in reviewed bounds | Stop and inspect the source |
| `manual_review_required` | Boundary-crossing or unclassified objects | Resolve ownership before reconstruction |

## Evidence accounting

Each route records:
- Source image, vector and text object IDs
- Original PDF paint order where available
- Intersection ratio between each object and reviewed bounds
- Counts and any ambiguous boundary crossings
- Human-reviewed panel/region identifier and exact source bounds

An object is considered contained only when at least 90% of its own bounding-box area lies inside the reviewed region. A crossing or unclassified object forces manual review. Objects are never silently duplicated or assigned to an adjacent panel.

## Safety boundary

The output is advisory only:
- `execution_authorized` is always `false`.
- No FigureSpec is changed.
- No scientific nodes, labels, connectors, or topology are inferred.
- A mixed route does not imply that the raster portion is editable.
- A native vector route does not imply that its paths have verified scientific meaning.

A separate reconstruction executor and fidelity gate will be required before these recommendations can drive automatic edits.
