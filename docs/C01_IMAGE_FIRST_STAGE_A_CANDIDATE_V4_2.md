# C01 FBG-SEANet Image-first Stage-A candidate V4.2

**Purpose:** research-defense / academic-presentation visual target for the V8 Image-first workflow. This is a Stage-A image candidate, not an approved figure and not a Stage-B PPTX.

## Artifact identity

- File: `C01_Image2_target_v4_2_1920x1080.png`
- Dimensions: 1920 × 1080
- Format: PNG
- Bytes: 1,571,770
- SHA-256: `4358ab1a2886ea88f999ae886d7451a32a7b68bfa9abcf5bf3699b92201e0686`
- Source FigureSpec: `C01_composite_defense_slide_image_first_v4_1`
- Source topology: V4.1, 18 method-level directed relationships
- Status: **generated; human Stage-A review pending**
- Stage B: **not_started / locked**

The candidate PNG and review materials are supplied in the separate Stage-A review ZIP. The repository CI artifact continues to validate the prompt and content lock; it does not claim to contain the external PNG.

## Generation and correction provenance

1. Generated a first visual draft using the V8 Image-first slide brief.
2. Resized the 16:9 draft to the exact 1920 × 1080 output contract.
3. Applied deterministic local raster corrections to remove an unsupported duplicate GCN₁ block and correct the lower diagnosis path:
   - Input → Energy-assisted module;
   - Energy-assisted module → the same single GCN₁ block;
   - pooling₁ branches to the lower IR readout;
   - pooling₂ continues to the main IR readout;
   - both IR readouts merge at the circular `+` operator before Dense.
4. Removed the spurious leading numeral from the title.
5. Rechecked the final PNG dimensions, decodability and SHA-256.

The raster correction is limited to the Stage-A target image. Stage B, when authorized, must reconstruct the approved design using native editable PowerPoint text, shapes and connectors; it must not use the target PNG as a full-slide background.

## Scientific and source boundaries

- The author-lab graphical abstract is the direct visual reference for the two-panel structure, input graph stack, pooling silhouettes and five illustrative class-output markers.
- The publisher-hosted high-resolution graphical abstract was not directly accessible in this review cycle. Do not claim publisher-image pixel comparison.
- The author-lab figure visibly appears to use `IR layer`; the public abstract uses `SR`. The discrepancy remains unresolved and is disclosed once.
- Sensor dimension `M` and band count `N` are variable.
- Four visible band rows, 12 input nodes, eight within-row edges and five class markers are schematic examples; they do not assert fixed sensor count, band count, adjacency or class count.
- Dashed inter-band connectors are illustrative. No exact edge count or numerical adjacency matrix is asserted.
- OCF before/after traces are illustrative, not measured.

## Review state

This candidate has not been approved by a human reviewer. All six Stage-A checks remain pending:

1. Scientific content and method flow.
2. Exact visible text and mathematical notation.
3. Source fidelity and evidence boundary.
4. Visual hierarchy.
5. Projection-distance readability under the intended presentation conditions.
6. Feasibility of native editable PowerPoint reconstruction.

Do not start Stage B until a human reviewer records an explicit approval for all six checks and no blocking issues remain.
