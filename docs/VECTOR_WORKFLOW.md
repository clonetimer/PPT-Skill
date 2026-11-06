# SVG-first vector workflow

## 1. Figure specification
Record the figure purpose, audience, panel order, hierarchy, modules, directed edges, equations/operators, legends, source evidence, style profile, fonts, palette, line widths, and spacing.

## 2. Authoring
- Draw using SVG paths, text, groups, and reusable symbols.
- Keep labels as text wherever practical.
- Use explicit font-family, font-size, fill, stroke, stroke-width, and marker definitions.
- Use vector graph nodes, waveforms, cylinders, and state blocks.
- Avoid converting all labels to outlines unless a delivery constraint requires it.

## 3. PowerPoint integration
- Use native PowerPoint shapes for ordinary boxes, labels, connectors, and state transitions.
- Use SVG for complex graph topology or compound scientific artwork.
- In supported Office versions, use Convert to Shape / Ungroup when individual SVG parts must be edited.
- Keep the original SVG file as the editable source of truth.

## 4. Rendering and QA
- Export the full deck to PDF.
- Inspect at presentation size and at 100% zoom.
- Compare source and redraw side by side.
- Check clipping, overlaps, arrow direction, line crossings, typography, terminology, and source notes.
- Record unresolved differences.

## 5. Delivery
Include SVG, PPTX, PDF preview, source citation, style profile, and QA report. Do not claim a figure is exact when it is only a structural redraw.
