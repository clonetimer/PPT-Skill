# C01 Composite v7.5 QA and repair record

## Scope

C01 Composite v7.5 is the complete two-panel FBG-SEANet structural redraw. It contains the upper frequency-band graph-construction panel, the lower graph-level diagnosis panel, and the Total graph → Input connection. It is distinct from the C01-SEANet lower-panel excerpt.

## Source-grounded repairs

The directly inspected visual source is the author-lab graphical abstract. The publisher high-resolution graphical abstract could not be accessed; previous claims of publisher-image inspection are withdrawn. The author-lab image appears to label both readout blocks IR layer, while the public abstract uses SR. The composite preserves the visible IR labels and discloses the unresolved terminology difference.

- **Round 01:** add an editable total-graph icon with four stacked band-subgraph rows (12 nodes), eight within-row illustrative edges and dashed inter-band connectors inside the lower Input block. The Total graph route is anchored to the Input container rather than the visible text label. The icon is explicitly schematic and does not encode a numerical adjacency matrix or a source-backed inter-band edge count.
- **Round 02:** restore five independent vertically stacked class-output squares after Dense, with the second square highlighted orange; restore the Dense → class-output connector and the `fault class` label.
- Both pooling modules use editable freeform quadrilaterals with near-vertical sides and slanted top/bottom edges, matching the author-lab source silhouette.
- The five output squares remain separate native shapes; the second square is highlighted orange.
- All objects are native PowerPoint shapes. Each object receives non-empty alternative text; the title carries a whole-figure description. The three-slide DECK01 method slide now embeds the v7.5 composite.

## Automated acceptance

The v7.5 validator checks:
- all 18 source-critical routes (five upper-panel, one cross-panel, twelve lower-panel);
- the 12-node editable input graph icon representing four stacked band subgraphs, with eight illustrative within-row edges and at least one dashed inter-band connector; the connector count is not a scientific acceptance criterion;
- two source-like pooling quadrilaterals and the explicit IR/SR terminology note;
- five independent class-output squares and the second-square highlight;
- the Dense → class-output semantic route;
- no rasterized objects, missing alt text, text overlap or out-of-bounds shapes.

The v7.5 artifact retains a particular set of dashed connector shapes as a visual schematic. Their rendered count is an implementation detail, not a recovered property of the paper method. The later V8 source contract supersedes this legacy representation: it requires sparse schematic links, explicitly withdraws the unsupported exact-nine claim, and uses one representative dashed inter-band example plus a non-attached continuation marker in the V4.1 target. Do not carry the v7.5 line count into V8 Stage B.

Automated PASS is necessary but does not replace independent domain review, final-size review or a real PowerPoint 2016 host round trip.

## Review status

- Initial baseline: C01 composite v7.4.
- Round 01 and Round 02: preserved as separate PPTX files with SHA-256, FigureSpec object diffs and rendered comparison.
- Human final review: PENDING.
- Office 2016 host round trip: PENDING.
- The C01-SEANet Stage 1 score (12/24, FAIL) remains an immutable historical assessment of the original lower-panel-only artifact. It is not retroactively changed by this composite repair.
