# C01 Image2 Stage-A Candidate V4.1

**Status:** generated and locally corrected candidate; final human Stage-A review pending.  
**Profile:** research-defense / academic presentation (16:9).  
**Image:** `C01_Image2_target_v4_1_1920x1080.png`.  
**Dimensions:** 1920 × 1080.  
**Bytes:** 1,823,791.  
**SHA-256:** `056ba83af5ceedf3dec73deff1cb134a0fc9c6b1e27b38c46b3580ec261b7a12`.  
**Source contract:** FigureSpec V4.1 + Topology Contract V4.1.  
**CI baseline:** #663 PASS — https://github.com/clonetimer/PPT-Skill/actions/runs/43857218000.

## V4.1 visual changes

- Total graph uses B_N for the Nth band, with an ellipsis and non-attached dashed continuation rail between B₃ and B_N. No specific B₃-to-B_N node edge is drawn.
- The legend differentiates solid intra-band connections from dashed inter-band schematic connections; one representative dashed edge remains.
- Reading guide separates band-pass filtering (per-band signal extraction) from graph construction (per-band subgraph formation and total-graph connection).
- Five near-square output markers are explicitly labelled Fault classification; only C₂ is highlighted.
- The IR/SR terminology note appears once in the Evidence boundary panel.

## Source and notation note

The author-lab graphic labels the final representative item “Sub graph N: Nth band”; the V4.1 redraw uses B_N as a normalized explanatory label. This does not claim that the author artwork literally prints B_N. The publisher abstract uses “sensitivity-aware readout (SR)”, while the author-lab graphic visibly says “IR layer”; no equivalence is asserted.

## Generation and correction provenance

V4.1 began as an ImageGen/Image2-style slide-image iteration based on the V4 visual candidate. A deterministic local raster correction then removed unsupported extra node-to-node dashed links in the Total graph and replaced them with one representative dashed example plus a non-attached continuation rail and ellipsis. The resulting target is 1920×1080. This correction is intentionally limited to the Total graph connectivity and does not fabricate numerical adjacency.

## Remaining acceptance gates

1. Human review of scientific content and source fidelity.
2. Exact text / B_N notation check.
3. Visual hierarchy check.
4. Physical projection-distance test.
5. Native editable PowerPoint reconstruction feasibility confirmation.
6. Explicit Stage-A approval.

Stage B remains locked. No editable PPTX, parity score or PowerPoint 2016 host round trip is claimed by this candidate record.


## CI / candidate-image handoff boundary

CI #663 validates the V4.1 FigureSpec, topology, DeckSpec, Image2 prompt and generated workflow manifest. The CI manifest remains `stage_a.status=planned` with `target_image=null` because the candidate PNG is supplied in the external human-review bundle rather than committed into the repository workspace. The candidate itself is generated and checksum-verified as recorded above; this distinction is intentional. Stage B remains `not_started`.
