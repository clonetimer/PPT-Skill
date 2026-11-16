# C01 FBG-SEANet V4.3 — Stage-A revision candidate

**Review decision inherited from V4.2:** Revise Stage A (AI technical review; not a controlled human sign-off).  
**Candidate:** `C01_Image2_target_v4_3_1920x1080.png`  
**Dimensions:** 1920 × 1080 PNG  
**SHA-256:** `2d773aed94e4028876ecdac44cff756c87ebf4e176d6aaa23306461a070f41eb`  
**Status:** Generated; awaiting Stage-A re-review.  
**Stage B:** `not_started` / locked.

## Changes responding to returned findings

| Finding | V4.3 change | Verification boundary |
|---|---|---|
| A1 — Total graph line semantics | Rebuilt the Total graph glyph: eight horizontal solid within-row links; one dashed B₁→B₂ example; removed vertical solid inter-row edges and the direct B₃→B_N edge; added a vertical ellipsis and two short non-attached dashed continuation rails in the B₃/B_N gap, left of all nodes. | Deterministic raster patch + visual inspection. All cross-band details remain schematic; no adjacency matrix or exact edge count is claimed. |
| A2 — Cross-panel route | Removed the lower-only text card and added one continuous orthogonal directed connector from the Total graph's lower row, around the lower outer edge of the upper panel, through the left outer gutter, then into Input with an arrowhead. | Route is continuous in the PNG and does not cross the “02” heading or Reading guide. |
| A3 — Input glyph | Preserved 12 nodes in four rows of three and eight solid within-row edges; added three sparse dashed inter-row schematic links. | Dashed links indicate connectivity only; no numerical adjacency is asserted. |
| B1 — Detached output arrow | Removed the detached blue arrow; retained the single Dense → Fault classification arrow. | Visual inspection of output region. |

## Preserved source and method constraints

- The author-lab figure remains the direct visual reference for the two-panel structure and visible glyphs.
- Publisher high-resolution graphical abstract was not pixel-compared in this review cycle.
- IR/SR terminology remains unresolved: author-lab visual label appears as IR; public abstract uses SR. The evidence note is retained once.
- Sensor count M and frequency-band count N remain variable.
- Graph nodes, inter-band links, class outputs and waveform sketches remain schematic, not measured or recovered numerical structures.
- The normalized label B_N remains a redraw convention, not a claim about literal source typography.

## Remaining gate A4 — physical projection readability

**Not tested in this package.** The candidate is 1920 × 1080 and has passed native-resolution visual inspection only. A physical projector / presentation-size test must record:
- projector/display native resolution and screen diagonal;
- actual viewing distance;
- ambient lighting / contrast conditions;
- readability of Reading guide, Evidence boundary, graph-edge legend and DOI;
- any text that cannot be read without zooming.

A screen-scale simulation is supplementary only; it cannot be reported as a physical projection pass.

## Stage-A decision

V4.3 addresses A1–A3 and B1. It is ready for a new Stage-A technical / human review. A4 remains pending. The six Stage-A checks in the workflow manifest remain unapproved until the reviewer explicitly signs the new form. **Do not start Stage B before formal approval.**
