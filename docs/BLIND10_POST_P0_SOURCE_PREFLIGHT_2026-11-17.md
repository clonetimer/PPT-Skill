# Blind10 post-P0 regression — source preflight execution (2026-11-17)

## Result

**10/10 original source PDFs passed the source-identity and crop preflight.**

This execution re-acquired the exact ten user-provided PDFs from the connected Library and checked each file against the immutable SHA-256 in `tests/fixtures/blind10_first_pass_frozen_2026-11-13.json` and the manually reviewed crop manifest `tests/fixtures/blind10_source_regions_2026-11-14.json`.

| Gate | Result |
|---|---:|
| Original source SHA-256 matches | 10/10 |
| Selected page and crop bounds valid | 10/10 |
| Caption anchor found within crop | 10/10 |
| Source identity/crop preflight | **PASS** |

The ten source files are not copied into this repository. The audit report records hashes, crop metadata, page dimensions and caption checks only.

## Reproduction

Run locally with the original ten PDFs in a private directory:

```bash
python tools/audit_blind10_sources.py \
  --source-dir ./ten_papers \
  --manifest tests/fixtures/blind10_source_regions_2026-11-14.json \
  --output qa/blind10_source_preflight_audit.json \
  --csv qa/blind10_source_preflight_audit.csv \
  --contact-sheet qa/blind10_source_crop_contact_sheet.png
```

Dependencies: PyMuPDF and Pillow.

## Visual review notes

The contact sheet is rendered at a consistent scale from the frozen PDF-point crop rectangles. It is a source-selection aid, not a reproduction result.

The corrected source selections remain:
- PINN: full three-panel Figure 4, including the lower loss/convergence/legend area.
- UCFNet: Figure 2, the proposed architecture, not Figure 1.

## Evidence boundary and next execution gate

This preflight does **not** regenerate or score any PPTX. It does not change the frozen first-pass baseline (10 generated, 0 strict passes, mean model-assessed score 18.2/24), and it does not establish post-P0 improvement.

Next: execute the post-P0 pipeline against these exact source crops, preserve per-paper source-layout/manifest/PPTX/render/OOXML evidence, then perform multi-round local repair and source-grounded re-audit. Keep the original first-pass outputs immutable. Expert review and actual PowerPoint 2016 host round-trip remain separate acceptance gates.

The ten-paper cohort remains `DEVELOPMENT_REGRESSION_ONLY`; do not report it as a new blind holdout or as independent-paper generalization.
