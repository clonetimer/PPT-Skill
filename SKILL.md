---
name: academic-defense-ppt
version: 7.0.1
description: Research-defense slide production with source-matched vector figures, scientific structure checks, and projection-aware typography.
---

# Academic Defense PPT Skill

## Mission
Produce technically accurate, readable academic-defense slides. Select the visual language per figure from the actual source; do not impose one universal template.

## Core principles
1. Scientific topology and terminology take priority over decoration.
2. Prefer vector-native graphics and editable text over raster screenshots.
3. Preserve the source figure's composition, hierarchy, module relationships, arrows, operators, legends, and line grammar.
4. Do not invent layers, dimensions, node assignments, formulas, or component relationships unsupported by the paper, code, or user source.
5. If a figure is too dense, split it into overview and detail slides; do not shrink every label to fit.
6. Never use PowerPoint object count as a proxy for visual quality.

## Choose a figure profile
Read `profiles/STYLE_PROFILES_V7.json` before drawing.

### A — Black-and-white academic framework
- Times New Roman; white background; black outlines; dashed section frames only where the source uses them or they materially clarify grouping.
- Use database cylinders, direct arrows, thin process modules, graph nodes, and evidence paths.
- Avoid decorative colored cards, heavy shadows, and unnecessary icons.

### B — Engineering system flow
- Microsoft YaHei; muted blue/purple/green/yellow/pink fills; dark-gray strokes.
- Use rounded modules only when the source uses them.
- Preserve orthogonal feedback, state transitions, safety routes, and execution-priority boundaries.
- Use a distinct title/description hierarchy inside each module.

### C — Source-matched journal figure
- Match the original paper's typography, line width, palette, panel order, and geometry.
- Use graph topologies, waveforms, frequency bands, pooling/convolution blocks, branches, and operators only when supported.
- Record whether each part is source-visible, paper/code-grounded, or an adaptation.
- Do not claim pixel-level reproduction without direct original-figure comparison.

## Current baseline warning
V7.0 examples are prototypes only. Known issues are recorded in `docs/KNOWN_ISSUES_V7.md`. In particular, avoid dense dashed-panel layouts, repeated generic rectangles, uniformly bold centered labels, and connectors that cross reading regions.

## Production workflow
1. Classify slide purpose: research question, system overview, mechanism, algorithm, experiment, result, or conclusion.
2. Collect evidence: inspect the actual figure, caption, paper text, equations, and official implementation when relevant.
3. Create a structured FigureSpec: panel order, modules, directed edges, operators, labels, geometry, typography, colors, and evidence status.
4. Select a source-matched style profile.
5. Draw in SVG first using vector paths, text, groups, and reusable components.
6. Integrate into PowerPoint with native shapes/text/connectors where practical; insert SVG for complex vector artwork.
7. Render the complete deck to PDF and inspect at presentation scale.
8. Deliver SVG, PPTX, PDF preview, source citation, style profile, and QA report.

**Implementation honesty:** V7.0 has an SVG example generator and a separate PowerPoint prototype. It does not yet provide deterministic dual rendering from one FigureSpec. Until that is implemented and tested, validate SVG and PPTX outputs separately; do not claim they are guaranteed to be identical.

## Typography and layout
- Slide title: 20–28 pt.
- Primary module labels: target 14–18 pt.
- Secondary labels: 12–14 pt for dense technical diagrams.
- Footers: 9–10 pt.
- Match the source's type hierarchy; do not enforce a universal minimum font size.
- Use the same font family within a figure unless the source requires otherwise.
- Maintain clear hierarchy through weight, size, and contrast rather than arbitrary color.
- Do not compress line spacing or reduce text to compensate for poor layout.
- Split dense content before reducing primary labels.

## Vector policy
- SVG is the default source format for diagrams, flowcharts, graph structures, and network architectures.
- Use PNG/JPEG only for genuinely photographic or raster-based content.
- For dense grids/graphs, use reusable vector groups, paths, symbols, or patterns rather than thousands of independent decorative rectangles.
- Keep text as text where practical.

## Mandatory QA
### Scientific fidelity
- Verify every node, branch, edge direction, feedback route, operator, formula, and label.
- Check terminology and abbreviations against the source.

### Visual fidelity
- Compare panel order, relative proportions, whitespace, alignment, line grammar, typography, and palette against the source.
- When the original image is available, perform side-by-side or overlay comparison.
- Record unresolved differences explicitly.

### Projection legibility
- Inspect the rendered PDF at presentation size.
- Check text collisions, line crossings, clipped text, and contrast.
- Place connector labels with explicit offsets; labels must not touch arrowheads or obscure paths.
- Do not use dashed outer frames unless source-grounded or functionally necessary.

### Editability and portability
- Confirm labels remain text and ordinary modules remain native PowerPoint shapes where practical.
- Confirm SVG opens in Inkscape/Illustrator.
- Test font fallback and rendering across Windows PowerPoint and LibreOffice; macOS PowerPoint remains a separate compatibility target.

### Evidence and attribution
Use one of:
- `source-visible redraw`
- `paper/code-grounded reconstruction`
- `domain adaptation`

Never describe a text-only reconstruction as a visual reproduction.
