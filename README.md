# Academic Defense PPT Skill

A research-defense slide skill focused on source-matched scientific diagrams, vector-first authoring, scientific fidelity, and projection legibility.

## V7 direction
V7 replaces the one-style-fits-all workflow with three source-specific figure profiles:
- **A — Black-and-white academic framework**: research overview, knowledge graph, multi-stage diagnosis logic.
- **B — Engineering system flow**: control systems, satellite architecture, FDIR loops, state management.
- **C — Source-matched journal figure**: GNN/CNN/Transformer architectures, signal processing, and paper-specific method diagrams.

The central rule is: **select the visual grammar from the source figure, then rebuild it as editable vector artwork.**

## Baseline status
V7.0 is a traceable prototype baseline, **not a visually accepted release**. Current examples still have known issues in layout density, connector routing, font hierarchy, and source-figure fidelity. Read [docs/KNOWN_ISSUES_V7.md](docs/KNOWN_ISSUES_V7.md) before reusing any prototype as a final slide.

The original user-provided reference PPTX is not included in this public repository. Only derivative redraws, style metadata, and general-purpose tooling are included.

## Repository structure
```text
SKILL.md
profiles/
  STYLE_PROFILES_V7.json
  VECTOR_COMPONENT_CATALOG_V7.json
examples/
  A01_black_white_academic.svg
  A02_reciprocal_rank_evidence_detail.svg
  B01_engineering_fdir.svg
  C01_FBG_SEANet_source_visible_redraw.svg
  D01_v7_workflow_and_style_profiles.svg
tools/
  build_svg_examples.py
  audit_pptx.py
  validate_svg_examples.py
docs/
  CHANGELOG.md
  KNOWN_ISSUES_V7.md
  QA_REPORT_V7.md
  SOURCE_ATTRIBUTION.md
  VECTOR_WORKFLOW.md
```

## Quick start
1. Read `SKILL.md`.
2. Choose a profile in `profiles/STYLE_PROFILES_V7.json`.
3. Inspect a relevant SVG example.
4. Build a FigureSpec from the paper figure, caption, equations, and official code.
5. Create the diagram as SVG; keep labels as text and use reusable vector groups.
6. Integrate into PowerPoint using native shapes/text where practical, or insert SVG and convert it to Office shapes when supported.
7. Render the deck to PDF and complete the QA gates in `SKILL.md`.

Rebuild the SVG examples:
```bash
python tools/build_svg_examples.py
```

Audit an existing PowerPoint file:
```bash
python tools/audit_pptx.py path/to/deck.pptx
```

## Typography
- Slide titles: 20–28 pt.
- Primary diagram labels: target 14–18 pt.
- Secondary technical labels: 12–14 pt for dense technical diagrams.
- Source notes: 9–10 pt.
- Split dense diagrams before shrinking the whole figure.

## Source boundary
The original user-provided reference PPTX is not redistributed. A/B profiles record visual characteristics, while examples are derivative redraws. C01 is a source-visible structural redraw, not a pixel-level copy.
