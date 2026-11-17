# C01 V4.2 Stage-A review package handoff

**Candidate:** `C01_Image2_target_v4_2_1920x1080.png`  
**Dimensions:** 1920 × 1080 PNG  
**Candidate SHA-256:** `4358ab1a2886ea88f999ae886d7451a32a7b68bfa9abcf5bf3699b92201e0686`  
**Review package:** `PPT-Skill_C01_V4_2_Stage_A_Review_Package.zip`  
**Package SHA-256:** `62464467bc69343e640454086c8932af4ccc69c88c60cbad9a5c2e831cb86241`  
**Package size:** 3,075,808 bytes  
**Status:** Stage A generated; human approval pending; Stage B not_started.

## Package contents

- V4.2 target PNG and the uncorrected ImageGen draft (provenance only; not the review target).
- V8 workflow manifest updated to `stage_a.status=generated`, with target path, dimensions and SHA-256 recorded.
- Locked V4.1 FigureSpec, topology contract and DeckSpec.
- Rendered Image-first prompt, including the corrected 12-node input graph row count and explicit single-GCN / EA-branch / pooling₁ readout constraints.
- Source evidence record, candidate provenance note, human Stage-A review form and SHA-256 manifest.

## Corrections included in V4.2

1. Removed the unsupported leading numeral from the slide title.
2. Removed a duplicate GCN₁ block from the Energy-assisted branch.
3. Restored Input → Energy-assisted module → the same single GCN₁.
4. Moved the lower IR readout branch to the output of pooling₁.
5. Preserved pooling₂ → main IR readout; both IR readouts merge at the circular `+` before Dense.

## Validation boundary

The ZIP SHA-256 manifest was checked with zero mismatches. The workflow manifest records Stage A as generated and Stage B as not_started. The candidate has only received visual precheck; this is not human approval.

The publisher high-resolution graphical abstract was not directly accessible. The author-lab graphic remains the direct visual source. The IR/SR discrepancy remains unresolved, and all graph adjacency/inter-band connectivity stays schematic.

## Human action required

Use `docs/C01_STAGE_A_REVIEW_FORM_V4_2.md` in the package. The reviewer must check the candidate at intended presentation size/distance and explicitly approve all six Stage-A dimensions. Any blocking issue returns the candidate to Stage-A revision. **Do not start Stage B before explicit human approval.**
