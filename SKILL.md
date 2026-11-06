---
name: academic-defense-ppt
version: 7.1.1
description: Source-matched academic-defense slides with vector-first figures, FigureSpec dual rendering, and projection-aware QA.
---

# Academic Defense PPT Skill

## Mission
Produce scientifically accurate, readable academic-defense slides. Select the visual language from the actual source figure. Do not force every figure into one universal card template.

## Core principles
1. Scientific topology, terminology, equations, and evidence boundaries take priority over decoration.
2. Prefer vector-native artwork and editable text. Use raster images only for genuine photographic content.
3. Preserve source composition, hierarchy, relative module proportions, directed edges, feedback routes, operators, legends, and line grammar.
4. Do not invent layers, dimensions, node assignments, equations, or component relationships.
5. Split dense mechanisms into overview and detail slides before shrinking the figure.
6. Never use object count as a proxy for visual quality.
7. Do not claim exact reproduction without inspecting and comparing the source figure.

## Source-specific visual profiles
Read profiles/STYLE_PROFILES_V7.json before drawing.

### A — Black-and-white academic framework
- Times New Roman, white background, thin black strokes.
- Use section dividers only where source-grounded or functionally necessary.
- Use database cylinders, process modules, directed connectors, graph nodes/edges, and evidence paths.
- Avoid decorative color cards, heavy shadows, unnecessary icons, and dense crossing connectors.

### B — Engineering system flow
- Microsoft YaHei in PowerPoint; SVG fallback: Noto Sans CJK SC, DejaVu Sans, Microsoft YaHei.
- Muted blue/purple/green/yellow/pink fills with dark-gray strokes.
- Preserve orthogonal feedback, state transitions, safety routes, guard conditions, and execution priority.
- Keep transition labels short and outside module text areas.

### C — Source-matched journal figure
- Match the paper's typography, line width, palette, panel order, and geometry.
- Use graph topology, waveforms, frequency bands, pooling/convolution blocks, branches, and operators only when supported.
- Record source-visible, paper/code-grounded, or domain-adaptation status.
- Never call a structural redraw a pixel-level reproduction.

## FigureSpec-first production
V7.1.1 introduces deterministic dual rendering for B01 and F07.

1. Author geometry, text, colors, and connectors in JSON under figure_specs/.
2. Dimensions are inches; text sizes are points.
3. Use explicit line breaks; do not rely on PowerPoint auto-wrap when rendering the same spec to SVG.
4. Supported primitives: text, rect, line, grid, stack_grid.
5. The same FigureSpec renders to SVG and editable native PowerPoint shapes/text/connectors.
6. The renderer clears the default theme shadow effect style.
7. Build examples with: python tools/build_v71_examples.py
8. Validate with: python tools/validate_figure_specs.py

Scope honesty: FigureSpec dual rendering currently covers B01 and F07. A01 and C01 remain separate vector/PPTX prototype pages and have not yet been migrated.

## Typography
- Titles: generally 20–28 pt.
- Primary module labels: target 14–18 pt.
- Secondary labels: 12–14 pt for dense technical figures.
- Source notes: 9–10 pt.
- Match the source's hierarchy; there is no universal 14 pt minimum.
- Use explicit CJK fallback in SVG. PowerPoint may use installed Microsoft YaHei; SVG renderers may use Noto Sans CJK SC.
- Do not compress line spacing or reduce text to compensate for poor layout.

## Vector and grid policy
- SVG is the default source for diagrams, network structures, and scientific schematics.
- Use native PowerPoint text/shapes/connectors for ordinary modules and labels.
- For dense 40×40 matrices, use grid lines or a vector pattern, not 1,600 independent cell rectangles.
- Do not imply channel-to-cell assignments unless the source specifies them.
- Use raster imagery only for genuine hardware, experiment scenes, or source photographs.

## Mandatory QA
### Scientific fidelity
Verify every node, branch, edge direction, feedback route, operator, formula, label, legend, unit, and abbreviation.

### Visual fidelity
Compare panel order, relative proportions, whitespace, alignment, line grammar, typography, and palette. Use side-by-side or overlay comparison when original pixels are available. Record unresolved differences.

### Projection legibility
Inspect the rendered PDF at presentation size. Check clipping, text intersections, line crossings, arrow-label proximity, and contrast. Keep connector labels short and outside arrowheads.

### Editability and portability
Keep ordinary labels/modules native where practical. SVG picture objects must remain vector and be convertible to Office shapes in supported Office versions. Test PowerPoint for Windows and LibreOffice; macOS remains a separate target.

### Evidence and attribution
Use source-visible redraw, paper/code-grounded reconstruction, or domain adaptation. Cite the paper, figure, caption, DOI, implementation, or user source.

## V7.1.1 acceptance state
- B01: overlap and transition-label fixes; FigureSpec dual rendering; no theme shadow.
- F07: 40×40 line grid; no 1,600 cell rectangles; neutral occupancy display with explicit schematic caveat.
- C01: OCF notch-filter terminology and SR readout corrected; duplicate method boxes and summation operator removed.
- A01: section-heading collision removed.
- Remaining: strict original-figure overlay for C01 and Windows PowerPoint compatibility review.
