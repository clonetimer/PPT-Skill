# ADR — P0 renderer architecture for PPT-Skill V8

**Date:** 2026-11-16  
**Status:** Accepted for incremental implementation; production renderer migration gated by parity tests.

## Context

The current `FigureSpec` is a typed JSON element list and already acts as a common geometry source. However, `tools/render_figure_spec.py` emits SVG and python-pptx DrawingML from one interleaved loop. Text geometry and font resolution are also handled differently by the SVG and PPTX paths. The render record captures useful hashes, but the canonical visual workflow is not yet bound to a fixed Linux renderer/font environment.

The mature-case review supports three engineering changes: a backend-neutral AST with independent writers, a pinned headless renderer, and render-calibrated text geometry. These changes must not invalidate existing C01/V7.6/V8 artifacts or historical render evidence.

## Decision

### 1. FigureSpec → immutable FigureAST → independent writers

- FigureSpec remains the authoring/evidence contract and is not replaced by a new hand-maintained format.
- A compiler converts FigureSpec into an immutable AST with typed primitive nodes, geometry, paint, text content, semantic identifiers, evidence references and extensions.
- SVG and DrawingML writers consume the same AST. They may implement backend-specific serialization, but must not independently solve layout or reinterpret semantic edges.
- The AST records source SHA-256 and canonical AST SHA-256.
- Migration is incremental. The legacy renderer remains the production default until the new writers pass primitive coverage, object inventory, geometry, text and rendered-image parity on a representative corpus.

### 2. LibreOffice headless becomes the canonical CI visual renderer

- Canonical CI environment: Ubuntu 24.04 runner family, headless LibreOffice, Poppler, fixed locale/timezone, declared font packages and font-file SHA-256 values.
- Canonical output: PDF, per-slide PNGs, and a render record containing source PPTX hash, renderer versions, package versions, font resolution/hashes, DPI, environment and output hashes.
- A repeat-render test compares PNG hashes within the locked environment.
- Windows PowerPoint 2016 open/save/reopen remains a separate host-compatibility gate. It is not removed or re-labelled as tested merely because LibreOffice succeeds.

### 3. Text layout uses fast font metrics plus render calibration

- fontTools reads cmap/hmtx and OS/2/hhea metrics for a fast width/height estimate.
- A fit solver uses binary search to find a minimum text-box height at a fixed font size, or a maximum permitted font size under an explicit shrink policy.
- The default policy preserves authored font size. If the layout budget cannot accommodate the measured text, the build reports overflow and a suggested fix rather than silently reducing type.
- A headless render probe calibrates font metrics for the pinned LibreOffice profile. Font substitution and unsupported glyphs are explicit warnings/errors.
- WCAG contrast is measured against the resolved background; normal text target is 4.5:1. Large-text exceptions must be explicit in the profile.

## Non-goals

- Do not make LibreOffice success a claim of Microsoft PowerPoint compatibility.
- Do not replace source/evidence checks with visual similarity.
- Do not change historical V7.6/V8 render records or silently rebaseline their hashes.
- Do not automatically shrink all text to a global minimum size.
- Do not migrate all legacy FigureSpecs in one change.

## Release gates

1. AST round-trip and supported-primitive coverage.
2. SVG/DrawingML geometry and semantic parity on representative figures.
3. Zero unexplained native-object count changes.
4. Canonical LO repeated PNG render hashes stable in the locked CI environment.
5. Text-fit estimates compared with LO render probes; false-negative overflow rate measured.
6. Existing C01 and 15-task regression suite remains green.
7. PowerPoint 2016 host round-trip is still separately recorded as pending until executed on a real Office host.
