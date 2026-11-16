# C01 FBG-SEANet V4.1 — Minor Revision response

**Scope:** Research-defense / academic-presentation slide. The separate publication profile remains a distinct future deliverable.  
**Previous decision:** V4 Minor Revision.  
**Current candidate:** V4.1.  
**Image:** `C01_Image2_target_v4_1_1920x1080.png`.  
**SHA-256:** `056ba83af5ceedf3dec73deff1cb134a0fc9c6b1e27b38c46b3580ec261b7a12`.  
**Status:** Ready for final human Stage-A review; not approved; Stage B remains locked.

## 1. Point-by-point response

| V4 Minor Revision item | V4.1 change | Verification boundary |
|---|---|---|
| Total graph Bₙ looked disconnected | Label normalized to B_N; one dashed inter-band example retained; a vertical ellipsis and short dashed continuation rail sit between B₃ and B_N | Rail is not attached to nodes. No B₃-to-B_N edge is asserted; no exact adjacency or edge count is claimed |
| Reading guide conflated filtering and graph construction | Split into two explicit statements: band-pass filtering obtains per-band signals; graph construction builds one subgraph per band and connects them into the total graph | Wording follows the publisher's description of FBG decomposing signals into bands, building per-band subgraphs, and connecting them |
| Class outputs were rectangular / unlabeled | Five near-square output boxes and a visible “Fault classification” label; only C₂ remains highlighted | Five classes remain illustrative, not a fixed model output count |
| Bₙ / B_N notation inconsistent | All visible labels use B_N with uppercase N; N remains variable | Author-lab artwork itself says “Sub graph N: Nth band”; B_N is the redraw's normalized notation, not a claim that the artwork prints the literal string B_N |
| IR/SR explanation repeated | Retained one note in Evidence boundary; removed duplicate central note | Author-lab image says IR layer; publisher abstract says sensitivity-aware readout (SR); equivalence remains unresolved |

## 2. Source verification

- The author-lab source image labels the last representative subgraph “Sub graph N: Nth band” and shows multiple graph layers with inter-layer dashed connectivity. It does not provide a numerical adjacency matrix in the visible graphic.
- The publisher article preview describes two stages: OCF/notch filtering to suppress operational components, followed by band-pass filtering for frequency-band subgraph construction; the abstract describes decomposing sensor signals into multiple frequency bands, building one subgraph per band and connecting them into the final graph.
- The publisher abstract names the sensitivity-aware readout (SR) layer. The author-lab graphic's visible readout label is IR layer. This discrepancy is not silently reconciled.

## 3. V4.1 evidence boundary

1. The four displayed bands are representative; N is variable.
2. The visible sensor labels indicate variable M; the graph-node glyphs are schematic and do not imply M=3.
3. Solid intra-band links and the dashed inter-band example are schematic; exact adjacency is not asserted.
4. The ellipsis and non-attached continuation rail indicate omitted intermediate bands without inventing a specific B₃-to-B_N node edge.
5. OCF before/after waveforms are illustrative, not measured.
6. Five square class markers are illustrative; only C₂ is highlighted.
7. IR/SR remains unresolved and is disclosed once.

## 4. Final Stage-A gate

The V4.1 candidate is ready to be considered for final human Stage-A sign-off. The six checks must be explicitly completed:

- Scientific content and method flow
- Exact visible text and mathematical notation
- Source fidelity and schematic/evidence boundary
- Visual hierarchy
- Projection-distance readability (must be physically tested)
- Feasibility of native editable PowerPoint reconstruction

CI can validate source contracts, prompt constraints and structural consistency. It cannot certify physical projection readability or an actual PowerPoint 2016 open/save/reopen round trip. Those remain separate human/host checks. Until approval is explicitly recorded, Stage A remains pending and Stage B remains not_started.


## CI verification

CI #663 PASS: https://github.com/clonetimer/PPT-Skill/actions/runs/43857218000. The workflow validates 13 V4.1-specific regression tests, generates and validates the source-locked Image2 prompt/manifest, and validates all 142 FigureSpec elements. The CI manifest status `planned` describes the repository-side prompt workflow; the actual PNG candidate is distributed separately in the human-review package and is not embedded in the CI manifest. Human Stage-A approval remains pending.
