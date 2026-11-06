# V7.0 QA Report — Baseline, Not Acceptance

## Scope
V7.0 contains the Skill, A/B/C style profiles, reusable component metadata, five SVG examples, an SVG builder, a PowerPoint audit script, and a five-slide editable prototype deck delivered separately from the public repository.

## Reference baselines inspected
The user's original reference deck was inspected locally and is intentionally not copied into this public repository.
- Reference slide 189: 83 recursive drawing objects (29 lines, 26 auto-shapes, 19 text boxes, 4 picture objects, nested groups/freeforms). Times New Roman; 11/13/14 pt hierarchy; black-and-white multi-panel framework.
- Reference slide 208: 21 recursive objects. Microsoft YaHei; 20 pt title and 14 pt body; pastel module fills; dark-gray connectors.
- Reference slide 213: 25 editable objects. Microsoft YaHei; 20 pt title and 14 pt body; four-stage FDIR chain, closed-loop feedback, and NORMAL/RECONFIG/DEGRADED/SAFE state flow.

## Included prototypes
- A01: academic framework overview.
- A02: reciprocal-rank fusion and evidence-coverage detail.
- B01: online FDIR and mode-management loop.
- C01: FBG-SEANet structural redraw based on the author-published graphical abstract.
- D01: style-profile and vector-workflow overview.

## Programmatic checks
The local prototype deck contains 5 slides. Its latest audit reports:
- 0 embedded raster-picture objects in generated prototype slides.
- 0 generated-shape out-of-bounds objects.
- Recursive shape counts, explicit font ranges, and object bounds are available from the audit script.
- SVG examples pass XML parsing and basic width/height/viewBox validation.

These checks do not establish visual quality. Current examples still contain known defects: crowded panel layouts, connector-label proximity, small secondary labels, generic module geometry, and incomplete source-figure matching. See `KNOWN_ISSUES_V7.md`.

## Evidence boundaries
- A01 and B01 are derivative redraws of user-provided reference styles, not exact duplicates.
- C01 is a source-visible structural redraw, not a pixel-level copy. Sensor glyphs are vector substitutes; graph geometry remains schematic.
- A02 is a content-detail diagram, not a verified reproduction of a specific published figure.
- D01 is an internal workflow page, not a final defense-slide design.

## Acceptance status
**V7.0 is a baseline upload only. It is not accepted as the final visual quality.** V7.1 must address the known issues and implement a single FigureSpec source for SVG and PowerPoint before the production workflow is considered stable.
