# R1 source image clipping in the native importer

## Intent

Continue the user-authorized real-paper native reproduction work by moving the verified local-image clip repair into the reusable PDF import path. The original ten figures and their delivered files stay immutable. This is a development regression improvement, not a new blind benchmark.

## Approach

Extend `pdf_source_assets.collect_image_events`, which is already shared by the importer and structural audit. Use the PDF renderer's source SVG solely to recover each image occurrence's clip paths and placement. Replay those paths around that single source raster asset into a transparent PNG. All diagram vectors and text continue through the existing native importer. Store clip provenance with the image event and import manifest.

The builder selected this approach because it directly replaces the private 35-image repair. A new batch wrapper would not fix image fidelity; a general semantic FigureSpec adapter is a separate gap and outside this change. No arbitrary script execution or full-page raster fallback is introduced.

## Contract

- Preserve source order, repeated occurrences, raw source alpha/soft masks, and page/crop placement. Source clip paths apply before page cropping.
- Apply same-bounds curved clips as well as clips that reduce the bounding rectangle.
- Verify occurrence correspondence from paint order plus geometry, rather than matching only an XRef or a nearby rectangle.
- Unclipped supported images retain their original bytes when no clip changes their pixels or placement.
- Unsupported SVG transforms, masks, clip geometry or ambiguous correspondence produce an explicit unresolved-image diagnostic; native import cannot silently pass with unmasked pixels.
- Limit isolated clip renders to 16 million pixels each and 64 million per page; do not allocate oversized rasters. Rendering uses at least 576 dpi, increasing to the source pixel density for small high-resolution assets so clipping cannot downsample them.
- Record original asset hash, final asset hash, clip identity, geometry, method and output resolution. Source image bytes alone do not constitute visual approval.
- Existing source/PPTX/render evidence and external-review boundaries remain separate.

## Verification

Use synthetic PDFs with circular/even-odd/nested clips, repeated image uses, soft masks, partial figure crops, and nearby native content. Verify alpha pixels against actual PDF rendering; count native objects and compare their XML before/after. Reject ambiguous or unsupported input and resource exhaustion. Re-run focused importer/audit suites and the repository CI. Replay PINN, EvoOntology and UCFNet against their original source hashes in a new private directory, inspecting actual previews and keeping the delivered baseline unchanged.
