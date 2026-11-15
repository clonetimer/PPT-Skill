# C01 Image2 Stage-A candidate v2 — expert review handoff

**Status: READY_FOR_HUMAN_REVIEW — NOT APPROVED**  
**Stage B: BLOCKED until a human reviewer approves Stage A.**

## Candidate asset

- File: `C01_Image2_target_v2_1920x1080.png`
- Original Image2 output: 1672 × 941 px
- Review copy: 1920 × 1080 px (Lanczos resize; no crop)
- SHA-256: `d0699384dcffce0918627121d28d7ce7c6e899b159cc64fdc881987f4d311c5b`
- Size: 1,757,059 bytes
- The image is attached to the ChatGPT conversation; it is not yet committed to this repository.

## Source locks

- FigureSpec: `figure_specs/c01/C01_composite_defense_slide.json`
  - version: `7.4.0`
  - Git blob: `67a6a62a370fabe04ef6f1fd772a8a712c82af26`
  - SHA-256 of fetched UTF-8 content: `6ea3e2464d5a10e02586a542883fc6054f7622ed8975ee297afc1ae8143d41db`
- Topology contract: `specs/c01_composite_expected_topology_v75.json`
  - Git blob: `234f2401bf2c2d4201746cc2c36a22fc74247ba9`
  - SHA-256 of fetched UTF-8 content: `259551bda14b4da3847480353bfb95e7d65e5c89bbe4475846ecee4e4b59a776`
  - 18 critical directed relationships; 21 required semantic nodes.

## Assistant visual triage

### Present in the candidate

- Upper flow: sensor signals → OCF/notch filter → band-pass filters → B₁/B₂/B₃/Bq subgraphs → four-layer Total graph.
- Frequency direction is vertical and downward.
- A cross-panel `Total graph → Input` connector is present.
- Input graph shows 12 nodes arranged as four rows by three columns.
- Both the direct Input-to-first-GCN route and the Input → EA → first-GCN branch are visible.
- Main diagnosis path and second IR readout branch converge at Σ before Dense.
- Five class outputs are shown; only C₂ is orange.
- Evidence boundary says graph connectivity is schematic and no numerical adjacency matrix is asserted.
- The author-lab IR label versus public-abstract SR label discrepancy is explicitly left unresolved.
- The cited paper and DOI are present.

### Remaining expert-review point

The raster diagram contains dashed inter-layer connectivity in both graph illustrations. Although the four frequency layers and 12-node/four-row Input graph are visible, the exact nine-link count is not reliably auditable from the raster alone. The drawing is explicitly schematic and must not be interpreted as a numerical adjacency matrix. The expert reviewer should confirm whether the schematic representation is acceptable against the source-visible structure; if exact link count is required visually, revise the target before freezing.

## Stage-A decision

Do not mark this candidate approved automatically. A human reviewer must assess all six V8 checks:

1. Scientific content
2. Exact visible text
3. Source fidelity
4. Visual hierarchy
5. Projection readability
6. Reconstruction feasibility

Only after all six checks pass and blocking issues are cleared may the Stage-A target be frozen and Stage B begin.
