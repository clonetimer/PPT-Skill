# Tree-KG Figure Trial QA — revision after visual feedback

- Source: Niu et al., ACL 2025, PDF page 3 Figure 2 and Sections 3.1–3.3. Original PDF and seven visual anchors are retained in this directory.
- Source comparison: both phases, left-side before/after tree, graph-first operator vignettes, pastel node classes, numbered 1/2/6 and 3/4/5 arrangement, and dashed candidate/horizontal edges are present. The earlier long inter-operator arrow was removed because it implied a fixed order unsupported by the paper.
- Material remaining differences: this is a presentation-scale explanatory redraw with fewer example nodes and no robot glyphs or detailed score/matching loops. It must not be described as a pixel-matched source reproduction or a journal-ready figure.
- Scientific check: five independently listed required routes and eight required operator/input/output nodes passed against the FigureSpec. The paper's flexible operator collection is not encoded as sequential edges.
- Occlusion preflight: `python tools/audit_figure_occlusion.py dist/skill_tests/treekg/TK01_treekg_technical_route.json` reports zero line/text and line/ellipse penetrations. PowerPoint PNG was inspected after export.
- Editable export: 158 PowerPoint native shapes and text, with no source figure embedded as a picture. SVG/PPTX/PDF/PNG are co-generated or exported from the same FigureSpec. Strict PPTX audit passed with no out-of-bounds objects or text-box overlaps; smallest font is 9.5 pt.
- Remaining verification: no independent domain review or physical projection/print inspection. The diagram is a development example.
