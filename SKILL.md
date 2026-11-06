---
name: academic-defense-ppt
version: 7.2
description: Source-specific academic-defense slide production with vector-first figures, split technical narratives, and evidence-aware visual QA.
---

# Academic Defense PPT Skill

## Mission
Produce scientifically accurate, projection-readable academic-defense slides. Select the visual grammar from the actual source; do not force all figures into a universal template.

## Principles
1. Scientific topology, terminology, equations, and evidence boundaries outrank decoration.
2. Prefer SVG/vector artwork and editable text; use raster only for genuine photographs.
3. Preserve source composition, hierarchy, module proportions, directed edges, operators, and legends.
4. Do not invent graph coordinates, sensor-to-node mappings, network layers, or fusion operators.
5. Split dense mechanisms into sequential slides before shrinking labels.
6. A structural redraw is not an exact reproduction. Require direct source inspection and overlay comparison before claiming high visual fidelity.

## Visual profiles
- A: black-and-white academic framework; Times New Roman, restrained lines, source-matched dividers and evidence paths.
- B: engineering system flow; Microsoft YaHei, muted pastel modules, dark-gray connectors, feedback and state transitions.
- C: source-matched journal figure; match the paper's typography, palette, line grammar and panel structure. Keep unverified details schematic and explicitly labeled.

## FigureSpec workflow
1. Inspect the source figure, caption, article text, equations and author code where available.
2. Create a structured FigureSpec containing panels, modules, edges, operators, labels, geometry, typography, palette and evidence status.
3. Render SVG and editable PowerPoint from the same specification.
4. Inspect the exported PDF at presentation scale; verify text intersections, clipping, arrow direction, line crossings and font fallback.
5. Deliver source specs, SVG, PPTX, PDF and a QA report.

## Dense diagrams
- Use native paths/lines, reusable vector symbols and graph primitives.
- Never expand a 40×40 matrix into 1,600 independent rectangles.
- Do not color grid cells as if channel mapping were known when the source does not specify coordinates.
- Separate graph construction, representation learning, readout and classification when a single slide becomes crowded.

## Evidence labels
- source-visible redraw
- paper/code-grounded reconstruction
- domain adaptation

Never call a paper-grounded structural reconstruction an exact visual reproduction.

## V7.2 C01 example
C01 is split into two slides:
1. Frequency-band graph construction: multi-sensor signals, OCF/notch filter, band-pass responses, per-band subgraphs and final FBG.
2. Graph-level representation: FBG input, GCN/pooling stages, SR readout, graph-level representation and classification; EA branch is shown separately.

The exact graph topology, sensor-to-node mapping and EA fusion operator are not asserted where unavailable. See docs/C01_V72_QA.md and docs/C01_V72_SOURCE.md.
