# Academic Defense PPT Skill

Research-defense slide generation with source-specific visual profiles, vector-first artwork, scientific fidelity checks, and projection-aware typography.

## V7.1.1 status
V7.1.1 refines the V7.0 prototype baseline. It fixes visible overlap and shadow defects and introduces a JSON FigureSpec dual-render pilot for B01 and F07. It is not yet a stable release: C01 needs stricter original-figure comparison, and Windows PowerPoint needs a separate compatibility check.

## Visual profiles
- A — Black-and-white academic framework: Times New Roman, thin black strokes, restrained section dividers, database cylinders, graph nodes, and evidence paths.
- B — Engineering system flow: Microsoft YaHei, muted pastel modules, dark-gray connectors, state transitions, and feedback loops.
- C — Source-matched journal figure: per-paper typography, graph/signal primitives, source-specific geometry, and explicit fidelity status.

## FigureSpec pilot
B01 and F07 are generated from:
- figure_specs/B01_engineering_fdir.json
- figure_specs/F07_telemetry_embedding.json

The same specification renders to SVG and editable native PowerPoint shapes/text/connectors. The 40×40 feature grid uses line geometry and a vector pattern rather than 1,600 independent rectangles. Occupancy is schematic; no exact channel-to-cell map is claimed.

## Repository layout
- profiles/: visual profiles and reusable vector components
- figure_specs/: canonical B01/F07 JSON specifications
- examples/: SVG examples, including generated B01/F07 V7.1.1 outputs
- tools/: renderer, builders, validators, and PowerPoint audit
- docs/: QA, known issues, source attribution, workflow
- dist/: generated standalone B01/F07 PowerPoint examples

## Quick start
1. Read SKILL.md and select the A/B/C profile.
2. Edit the relevant JSON FigureSpec, not SVG and PPTX separately.
3. Rebuild: python tools/build_v71_examples.py
4. Validate: python tools/validate_figure_specs.py
5. Validate SVG: python tools/validate_svg_examples.py
6. Audit a deck: python tools/audit_pptx.py path/to/deck.pptx --strict
7. Export to PDF and inspect at presentation scale.

## Important boundaries
The original user-provided reference PPTX is not redistributed. A01/B01 are derivative redraws, not exact copies of the user's source slides. C01 is a source-visible structural redraw, not a pixel-level reproduction. FigureSpec dual rendering currently covers B01 and F07 only.
