---
name: academic-defense-ppt
version: 7.4.0
description: Source-matched academic-defense slides with editable vector FigureSpecs and projection-aware QA.
---

# Academic Defense PPT Skill

Produce technically accurate, readable academic-defense presentations. Select visual grammar from the actual source; do not impose a universal card template.

## Principles
1. Scientific topology, terminology, equations and evidence boundaries take priority.
2. Prefer editable vector graphics and native PowerPoint text/shapes; use raster only for genuine photographs.
3. Preserve source composition, panel order, proportions, arrows, branches, operators and line grammar.
4. Do not invent layers, edges, node mappings, equations or downstream blocks unsupported by the source.
5. Split dense mechanisms before shrinking labels.
6. Shadows are off by default. Reproduce them only when visible in the selected source, using explicit source-specific shapes; never inherit the PowerPoint theme shadow.
7. Distinguish source-visible redraws, paper/code-grounded reconstructions and domain adaptations.

## Profiles
- A: black-and-white academic framework, Times New Roman, thin strokes and restrained section boundaries.
- B: engineering system flow, Microsoft YaHei, muted pastel modules, feedback and state transitions.
- C: source-matched journal/network figure, paper-specific typography, graph nodes/edges, sensor waveforms, pooling geometry, readout and fusion layout.

## FigureSpec
Canonical source is JSON under `figure_specs/`. Render SVG and editable native PowerPoint from the same FigureSpec. C01 primitives include text, rect, trapezoid, line, polyline, ellipse, sensor and graph. F07 also uses grid and stack_grid.

## C01 source-matched pattern
FBG: sensor rows and waveforms → OCF/notch filter → B1/B2/B3/Bq subgraphs → total graph.
SEANet: Input → GCN → pooling → GCN → pooling → SR; parallel Input → EA module → SR; both feed the summation node.
The paper text defines SR as sensitivity-aware readout. Sensor photographs may be replaced with vector silhouettes when vector-first output is required; disclose this. Graph coordinates remain schematic unless a numerical adjacency matrix is available.

## Composite defense-slide layout
When the user wants the complete method on one slide, use the V7.4 layout:
- Two related figure panels stacked in the left column.
- Reading guide, evidence boundary and citation in the right column.
- Reflow dense modules for the narrow panel; do not uniformly scale a full-width diagram.
- Keep the two-slide V7.3 version as the detail/teaching alternative.

## QA
Verify topology and terminology against the paper/caption/official code. Render the complete deck to PDF. Check text overlaps, clipping, out-of-bounds objects, SVG validity, raster objects and theme shadows. Do not claim pixel identity without high-resolution source and direct overlay.

V7.4 local QA: 320 native shapes; 31 text boxes; zero text-box intersections; zero out-of-bounds objects; zero raster picture objects; no theme shadow. Windows PowerPoint validation remains open.
