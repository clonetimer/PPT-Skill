# P0-04 fail-closed release gate — 2026-11-14

## Implemented

The release classifier is now part of the single production entrypoint `tools/reproduce_research_figure.py`. Both PDF-import and FigureSpec routes write a versioned `delivery_manifest.json` and a `quality_report.json`, including source/candidate hashes, route evidence, blockers, and pending approvals. Conversion or resource failures are recorded rather than reported as generated PPTX success.

### Route-specific acceptance

| Route / evidence | Classification |
|---|---|
| Empty / missing / incomplete candidate | `STRUCTURE_FAIL` |
| PDF importer hits a drawing/vertex/time budget | `RESOURCE_LIMIT` |
| Visible source image cannot be recovered, or import class is missing/unknown | `UNSUPPORTED_SOURCE` |
| Full-page raster only, native reconstruction required | `UNSUPPORTED_SOURCE` |
| Full-page raster only, diagnostic image mode explicitly allowed | `RASTER_SOURCE_ONLY` |
| Local source image with no native figure primitives | `UNSUPPORTED_SOURCE` by default; `SOURCE_PICTURE_ONLY` only when explicitly allowed |
| Mixed native primitives and local source images | `mixed_native_picture`; may proceed through structure and visual checks |
| Missing/failed structure, text, or OOXML audit | `STRUCTURE_FAIL` |
| FigureSpec has no semantic edge/quantitative relation contract | `NEEDS_SCIENTIFIC_REVIEW` |
| FigureSpec declared edges differ from actual connector links | `NEEDS_SCIENTIFIC_REVIEW` with explicit edge blockers |
| Import route lacks a source-to-candidate PDF visual comparison | `NEEDS_VISUAL_REVIEW` |
| FigureSpec route lacks a successful candidate render | `NEEDS_VISUAL_REVIEW` |
| All machine checks pass, human approvals pending | `TECHNICAL_PASS`, never full acceptance |
| All required approvals explicitly recorded | `FULL_ACCEPTED` |

### Evidence requirements

- Both routes require a non-empty candidate, a structure audit, a text-geometry/content audit and a passing OOXML preflight.
- PDF import additionally requires a recognized reconstruction class: `native_only`, `mixed_native_picture`, or `source_picture_only`. Unknown classes fail closed.
- PDF import visual evidence must be a source comparison. FigureSpec is a deliberate scientific re-layout; its evidence is a candidate render, not a misleading SSIM comparison to the original page.
- FigureSpec semantic audit checks unique element IDs, evidence references, declared semantic endpoints, and correspondence between `semantic_edges` and actual `semantic_link` connector objects. This is an internal-consistency audit, **not** proof that the source paper supports the science.
- `FULL_ACCEPTED` requires explicit scientific approval, visual approval, rights clearance, and (by default) verified target Office host evidence. A user can disable the Office-host requirement only for diagnostic/non-release use.
- Source math/Unicode risk flags remain a review blocker. No automatic formula guessing is permitted.

## Reproduction

PDF source import:

~~~bash
python tools/reproduce_research_figure.py source.pdf \
  --output dist/reproduction --mode import --render-host auto
~~~

FigureSpec route:

~~~bash
python tools/reproduce_research_figure.py source.pdf \
  --output dist/reproduction --mode figurespec \
  --figure-spec figure_specs/example.json --render-host auto
~~~

Explicitly permitted picture-only diagnostic recovery:

~~~bash
python tools/reproduce_research_figure.py source.pdf \
  --output dist/reproduction --mode import --allow-source-picture-only
~~~

The last command reports `SOURCE_PICTURE_ONLY`; it does not promote the result to native editable reconstruction.

## Verification

- [CI #177 PASS](https://github.com/clonetimer/PPT-Skill/actions/runs/43552465077), commit `cfbadbf2`.
- Release classifier tests: 20/20.
- End-to-end pipeline tests: 9/9.
- FigureSpec semantic/output audit tests: 6/6.
- Existing PDF import, XRef recovery, budget, text, Office OOXML, first-pass, F2 numeric and unseen-family tests also pass.
- The Windows CI job parses the PowerShell script only. Real PowerPoint 2016 COM open/save/reopen and final-size visual inspection remain outstanding.
- The frozen ten-paper strict first-pass result remains **0/10**. P0-04 prevents false acceptance; it does not claim to improve scientific fidelity by itself.

## Remaining limitations

- FigureSpec semantic audit validates declared graph consistency; independent scientific/domain approval is still mandatory.
- `TECHNICAL_PASS` is not a publication or release approval.
- Office OOXML preflight and LibreOffice rendering are not Microsoft PowerPoint 2016 host verification.
- P0-04 does not fix the visual simplification measured in the ten-paper blind cohort. The next workstream is P1-01: source-first panel/layout/style extraction.
