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


## Implementation evidence — 2026-11-17

The first cross-paper implementation gate has passed in GitHub Actions #752.

| Corpus figure | AST nodes | Native PPTX shapes | Raster changed pixels | Text matches | Rendered text outside frame |
|---|---:|---:|---:|---:|---:|
| Mamba Figure 1 | 57 | 70 | 0 | 16/16 | 0 |
| Swin Figure 2 | 27 | 56 | 0 | 8/8 | 0 |

Both figures were rendered with the pinned LibreOffice profile and compared with the legacy FigureSpec renderer. The AST and legacy PNGs are byte-identical in this run; both generated PPTX files contain zero picture objects. The text calibration report records zero missing text, zero line-count mismatches, zero unavailable font metrics and zero false-negative overflow cases for both figures.

The calibration implementation now:
- matches PDF characters across page-level text blocks instead of assuming a PDF block is one PowerPoint text frame;
- reconstructs multiline source text from distinct PDF baselines;
- resolves per-character fallback fonts for subscripts and other missing glyphs;
- measures glyph outline bounds at the PDF character baseline;
- preserves real whitespace and uses a bounded whitespace-insensitive fallback only when extraction drops it;
- checks same-frame alphanumeric continuation to prevent partial-word matches;
- records exact unmatched and out-of-frame strings in the pilot summary.

The workflow also preserves the AST generalization directory as a failure artifact. The associated development lessons and regression requirements are recorded in `docs/P0_TEXT_GEOMETRY_AND_GLYPH_AUDIT_2026-11-13.md`.

### Pre-build fit estimate evidence

The AST generalization pilot now runs `audit_figure_spec_text_fit.audit_spec` before rendering and archives `text_fit_preflight.json` beside the PDF glyph calibration. The preflight reports font-resolved width/height estimates, a binary-searched minimum frame height, additional height needed and WCAG contrast without changing source geometry or shrinking fonts.

CI #762 measured both independent-paper examples:
- Mamba Figure 1: 16 text elements, 0 estimated overflows, 0 contrast failures; post-render calibration 16/16 matches and 0 overflow.
- Swin Figure 2: 8 text elements, 0 estimated overflows, 0 contrast failures; post-render calibration 8/8 matches and 0 overflow.

The initial preflight used the full font line box as single-line ink height and produced two false positives on Mamba math labels. Replacing that with glyph-outline ink height (while retaining font line-height for inter-baseline spacing) removed those false positives without changing the figures. The regression suite now covers the single-line fallback-glyph case and explicit multi-line baselines.

### Remaining P0 boundary

This is a successful pilot, not yet a production-default renderer switch. The pre-build fit report remains advisory: its agreement is established on two independent-paper examples, not the full 15-task corpus. Expand calibration across dense Chinese/mixed-font figures, rotated labels, long equations and multi-paragraph text before converting preflight warnings into hard release gates. Real Microsoft PowerPoint 2016 open/save/reopen remains a separate host test.
