# SVG-first and FigureSpec dual-render workflow

## Source-specific style
Choose A/B/C from the actual reference. Do not impose a universal card template.

## FigureSpec pilot (B01/F07)
- Author geometry, text, colors, and connectors in JSON under figure_specs/.
- Dimensions are inches; text sizes are points.
- Use explicit line breaks; the SVG renderer does not infer PowerPoint automatic wrapping.
- Supported primitives: text, rect, line, grid, stack_grid.
- The same spec renders to SVG and editable native PowerPoint shapes/text/connectors.

Example:
python tools/render_figure_spec.py figure_specs/F07_telemetry_embedding.json --svg examples/F07_telemetry_embedding_v71.svg --pptx dist/F07_telemetry_embedding_v71.pptx

## Theme shadow control
The default PowerPoint theme's first effect style contains a shadow. The renderer patches it to an empty effect list and adds an explicit empty shape effect list. Do not remove this step.

## Dense grids
Use grid / stack_grid. PowerPoint output uses native line geometry; SVG output uses a vector pattern. Do not draw 1,600 independent rectangles for a 40×40 grid. If channel coordinates are unknown, do not color cells as if the mapping were known.

## Validation
python tools/build_v71_examples.py
python tools/validate_figure_specs.py
python tools/validate_svg_examples.py
python tools/audit_pptx.py dist/academic_defense_ppt_v71_refined.pptx --strict

## Rendering boundary
SVG and PowerPoint are generated from the same FigureSpec, but their text engines may differ. Do not claim pixel identity. Inspect both outputs and document font fallback and line-wrap differences.
