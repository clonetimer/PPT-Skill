---
name: academic-defense-ppt
version: 7.0
description: Research-defense slide production with source-matched vector figures, scientific structure checks, and projection-aware typography.
---

# Academic Defense PPT Skill

## Mission
Produce technically accurate, readable academic-defense slides. Select the visual language per figure from the actual source; do not impose a universal template.

## Core principles
1. Scientific topology and terminology take priority over decoration.
2. Prefer vector-native graphics and editable text over raster screenshots.
3. Preserve source composition, hierarchy, module relationships, arrows, operators, legends, and line grammar.
4. Do not invent layers, dimensions, node assignments, formulas, or component relationships unsupported by the paper, code, or user source.
5. If a figure is too dense, split it into overview and detail slides; do not shrink all labels to fit.
6. Never use PowerPoint object count as a proxy for visual quality.

## Choose a figure profile
Read profiles/STYLE_PROFILES_V7.json before drawing.

### A — Black-and-white academic framework
Use for research overviews, knowledge graphs, multi-stage diagnosis methods, and algorithm logic.
- Times New Roman; white background; black outlines; dashed section frames.
- Use database cylinders, direct arrows, thin rectangular process modules, graph nodes, and evidence paths.
- Avoid decorative colored cards, heavy shadows, and unnecessary icons.

### B — Engineering system flow
Use for control systems, satellite architecture, FDIR, platform architecture, and state machines.
- Microsoft YaHei; muted blue/purple/green/yellow/pink fills; dark gray strokes.
- Use rounded modules only when the source uses them.
- Preserve orthogonal feedback, state transitions, safety routes, and execution-priority boundaries.
- Use a distinct title/description hierarchy inside each module.

### C — Source-matched journal figure
Use for GNN/CNN/Transformer architectures, signal processing, and method diagrams.
- Match the original paper's typography, line width, palette, panel order, and geometry.
- Use graph topologies, waveforms, frequency bands, pooling/convolution blocks, branches, and operators only when supported.
- Record whether each part is source-visible, paper/code-grounded, or an adaptation.
- Do not claim pixel-level reproduction without direct original-figure comparison.

## Production workflow
1. Classify the slide purpose: research question, system overview, mechanism, algorithm, experiment, result, or conclusion.
2. Collect source evidence: inspect the actual figure, caption, paper text, equations, and official implementation when relevant.
3. Create a FigureSpec: panel order, modules, directed edges, operators, labels, geometry, typography, colors, and evidence status.
4. Select a style profile and inherit the source's visual grammar.
5. Draw in SVG first; use vector paths, text, groups, and reusable components. Keep labels as text wherever practical.
6. Integrate into PowerPoint: use native shapes/text/connectors for ordinary modules; use SVG for complex vector artwork. In supported Office versions, SVG can be converted to shapes.
7. Render the complete deck to PDF and inspect at presentation scale.
8. Deliver SVG, PPTX, PDF preview, style profile, source citation, and QA report.

## Typography and layout
- Slide title: 20–28 pt.
- Primary module labels: target 14–18 pt.
- Secondary labels: 12–14 pt for dense technical diagrams.
- Source notes: 9–10 pt.
- Keep a consistent font family within each figure unless the source requires otherwise.
- Do not compress line spacing or reduce text to compensate for poor layout.
- Split dense content instead of shrinking the whole figure.

## Vector and image policy
- SVG is the default source format for diagrams, flowcharts, graph structures, and network architectures.
- Use PNG/JPEG only for genuinely photographic or raster-based content.
- For dense grids and graphs, use reusable vector groups or compact vector patterns rather than thousands of independent decorative objects.
- Preserve a clean, editable text layer.

## Mandatory QA gates
### Scientific fidelity
Verify every node, branch, edge direction, feedback route, operator, formula, and label against source evidence.

### Visual fidelity
Compare panel order, relative proportions, whitespace, alignment, line grammar, typography, and palette against the source. Record unresolved differences.

### Projection legibility
Inspect the rendered PDF at 16:9 presentation size. Check clipping, overlap, crossing arrows, and label readability. Split dense content instead of shrinking it.

### Editability
Keep labels as text and ordinary modules as native PowerPoint shapes where practical. Confirm SVG assets open in Inkscape or Illustrator and PowerPoint rendering matches the preview.

### Evidence and attribution
Use one of: source-visible redraw, paper/code-grounded reconstruction, or domain adaptation. Cite the paper, figure, caption, DOI, or implementation. Never call a text-only reconstruction a visual reproduction.

## Repository assets
- examples/: standalone editable SVG examples.
- profiles/: style profiles and reusable component catalog.
- tools/audit_pptx.py: basic PowerPoint object, font, picture, and bounds audit.
- tools/validate_svg_examples.py: SVG XML and viewport validation.
- docs/: workflow, attribution, changelog, and QA records.
