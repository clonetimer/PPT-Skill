# C01 V7.6 source-evidence correction

## Correction to earlier repository records

Earlier repository notes stated that the publisher-hosted high-resolution graphical abstract had been inspected at 1198 × 886 pixels and recorded a downloaded-image SHA-256. That statement is **retracted**: the publisher image URL could not be accessed in this review cycle. The associated image hash must not be cited as verified evidence.

The visual comparison in the Stage 1 review is based on the author-lab copy:

https://hai.snu.ac.kr/data/editor/2606/78d439b23291567a99c14c62e0bbf0a6_1780552979_7277.jpg

The publisher article page was used only for the publicly accessible abstract/Highlights and preview, not as a directly inspected graphical-abstract image or full-text source.

## Source-visible structure and corrected redraw

| Relation | Author-lab graphical abstract | Corrected redraw requirement |
|---|---|---|
| Overall layout | Upper Graph Construction (Time-Frequency Graph) panel and lower Graph-level fault diagnosis framework panel, connected from Total graph to Input | The complete composite presents both panels on one slide; the standalone SEANet asset is explicitly marked as a lower-panel excerpt |
| Energy assist | Input branches to the Energy-assisted Module; the module feeds the first GCN | Input → EA → first GCN; the main Input also feeds the first GCN |
| Main route | Input → GCN → pooling → GCN → pooling → upper readout → summation → Dense → class outputs | Preserve the same directed route and Dense output |
| Lower readout | First pooling branches to a lower readout, which feeds summation | Preserve the branch from first pooling to the lower readout and then summation |
| Readout label | The author-lab image appears to label both readout boxes IR layer | Preserve the visible author-lab label IR layer; add a note that the public abstract uses SR for sensitivity-aware readout. Do not silently harmonize |
| Pooling geometry | Both pooling modules have near-vertical left/right sides and slanted upper/lower edges | Use editable quadrilateral/freeform polygons with slanted top and bottom edges, not axis-aligned rectangles or generic trapezoids |
| Input graph | A vertically stacked multi-group graph symbol | Preserve the stacked multi-subgraph visual hierarchy; graph coordinates and adjacency remain schematic |
| Output | Five independent vertically stacked squares; the second square is highlighted orange | Preserve five separate editable squares and the second-square highlight |

## Evidence boundaries

- The author-lab image is the direct visual evidence for visible labels, two-panel layout, pooling silhouette and five-square output.
- The public abstract supports the method term sensitivity-aware readout (SR), but the accessible author-lab image appears to use IR. This discrepancy remains unresolved.
- The publisher high-resolution graphical abstract was not directly accessed. No publisher-image visual inspection or hash is claimed.
- The image does not provide enough information to recover a numerical adjacency matrix, exact graph-node coordinates, measured waveform amplitudes, or frequency cutoffs.
- The redraw is a structural, editable derivative. It is not a pixel-identical copy.

## Acceptance boundary

CI may verify object geometry, visible routes, editability, alternative text, no clipping and source-label disclosure. CI does not resolve the IR/SR terminology discrepancy, certify machinery-diagnosis domain correctness, or replace final-size/projection review and a real PowerPoint 2016 host round trip.
