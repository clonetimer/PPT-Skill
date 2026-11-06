# Academic Defense PPT Skill

A research-defense slide skill focused on source-matched scientific diagrams, vector-first authoring, scientific fidelity, and projection legibility.

## V7 direction
V7 replaces the one-style-fits-all workflow with three figure-specific profiles:
- **A — Black-and-white academic framework**: research overview, knowledge graph, multi-stage diagnosis logic.
- **B — Engineering system flow**: control systems, satellite architecture, FDIR loops, state management.
- **C — Source-matched journal figure**: GNN/CNN/Transformer architectures, signal processing, and paper-specific method diagrams.

The central rule is: **select the visual grammar from the source, then rebuild it as editable vector artwork.**

## Repository structure
- SKILL.md
- profiles/STYLE_PROFILES_V7.json
- profiles/VECTOR_COMPONENT_CATALOG_V7.json
- examples/: five standalone SVG diagrams
- tools/audit_pptx.py
- tools/validate_svg_examples.py
- docs/: workflow, attribution, changelog, and QA records

## Quick start
1. Read SKILL.md.
2. Choose the relevant profile in profiles/STYLE_PROFILES_V7.json.
3. Inspect the nearest example SVG under examples/.
4. Build a FigureSpec from the paper figure, caption, equations, and official code.
5. Create the diagram as SVG; keep labels as text and use reusable vector groups.
6. Integrate into PowerPoint using native shapes/text where practical, or insert SVG and convert to Office shapes when supported.
7. Render the deck to PDF and complete the QA gates in SKILL.md.

## Typography
- Titles: 20–28 pt.
- Primary diagram labels: target 14–18 pt.
- Secondary technical labels: 12–14 pt.
- Source notes: 9–10 pt.
- Split dense diagrams before shrinking the whole figure.

## Source boundary
The original user-provided reference PPTX is not included in this public repository. The A/B profiles record its visual characteristics; only derivative redraws are included. The FBG-SEANet example is a source-visible structural redraw, not a pixel-level copy.
