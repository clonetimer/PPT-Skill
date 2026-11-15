# C01 Image2 Stage-A visual review — V8

**Decision: NEEDS_REVISION**  
**Reviewer type:** assistant visual triage (not independent human approval)  
**Stage B:** blocked; no PPTX reconstruction has started.

## Candidate asset

- Original Image2 output: 1672 × 941 px (16:9).
- Normalized review copy: 1920 × 1080 px, resized without content changes.
- Normalized candidate SHA-256: `db59e8898fde22cb1cb05787da69e666202ed16731ccb2b141277f700efc15e4`
- Image2 prompt asset SHA-256: `766d2afa7f4f392a344852b7878ed69ed544a0a5d0c3b12d839885d720fba159`
- Source FigureSpec SHA-256 used by the CI-generated C01 manifest: `9a941580e8310fa4c6367c68c15cece0893d8fe0122f04048cf39794f6ca9f14`
- Source topology contract SHA-256: `8638eb930aee670fa2549d02e571f294fd620b65141537bd8debc2f8d5e6affb`

## Checks that are visibly represented

- The upper and lower method panels are distinct and connected by a visible `Total graph → Input` route.
- The Input thumbnail is drawn as a four-row graph schematic.
- The diagnosis panel has two `IR layer` blocks, five square class outputs, and only the second output highlighted in orange.
- The evidence boundary states that graph adjacency is schematic and records the unresolved author-lab `IR` versus public-abstract `SR` terminology difference.
- The reading guide separates Filter, Construct, and Diagnose.

## Blocking defects

1. **Frequency direction:** the candidate draws a horizontal rightward Frequency axis. The source topology requires a vertical downward axis.
2. **Energy-assisted input branch:** the `Input → Energy-assisted module` connection is not clearly drawn. The visible `Energy-assisted module → first GCN` connection alone is insufficient.
3. **Total graph structure:** the candidate reduces the total graph to one network. The source contract requires four aligned band layers and nine dashed inter-band links.

The image is therefore a useful composition/style candidate, but it is not a source-faithful target and must not be frozen.

## Required next revision

Regenerate Stage A from the source-bound prompt and retain all 18 critical directed relationships. In particular, preserve the vertical-downward Frequency axis, the Input-to-EA branch, four total-graph layers, nine inter-band links, 12-node Input graph, and five square outputs with only C2 highlighted. Keep all graph connectivity schematic; do not invent a numerical adjacency matrix.

The Stage-A review can only become `approved` after the corrected image is inspected and all six review checks are completed by a human reviewer.
