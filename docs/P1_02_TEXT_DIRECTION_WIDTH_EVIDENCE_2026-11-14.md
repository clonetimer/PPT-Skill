# P1-02 text direction, width family and host autofit evidence

## Baseline and scope
Baseline commit: `d7213e7d6add52de4a0e84c4fd73ad193c2ac905`. Changes reuse the existing PDF importer; no new renderer, OCR or model is introduced. Source text, font sizes, anchors and shape counts are preserved. No user paper imagery or font binaries are redistributed.

## Reproduced defects and fixes
1. Text direction was reflected by `atan2(-dir_y, dir_x)`. Positive/negative slopes can have the same axis-aligned bounds, so the previous bounds audit passed a visually wrong result. The importer now uses the y-down source direction, and the read-only audit checks circular angle error with a 0.1 degree tolerance.
2. ArialNarrow aliases were consumed by the generic Arial prefix. Width variants are now resolved first.
3. `add_textbox` left host autofit enabled. Real LibreOffice output reflowed fixed source labels despite word-wrap being disabled. Imported text now explicitly uses `MSO_AUTO_SIZE.NONE`, without reducing size or moving objects. Mutating it back to host autofit fails the audit.
4. Comparing integer raster aspect ratios rejected a 360 x 240pt source vs a 360 x 240.01pt exported page. Comparison now uses physical PDF dimensions with the same 0.003 tolerance; physically wrong pages are rejected even if raster dimensions happen to match.

## Before/after render experiment
Host: LibreOffice 25.2.3.2, PyMuPDF 1.26.7. Identical input PDFs and the same post-fix evaluator, 144dpi, 4x4 tiles, are used for both outputs. The evaluator's physical-ratio correction is applied to both arms; no asymmetric scoring.

| Case | Type | Before global similarity | After global similarity | Specific observation |
|---|---|---:|---:|---|
| +/-30 degree text | Synthetic regression probe | 0.0853 | 0.5284 | Exported text slopes now follow the source rather than their reflections |
| Condensed adjacent labels | Synthetic regression probe | 0.2614 | 0.4566 | Four extracted wrapped lines become one baseline containing two text runs; both remain 14pt in PPTX |
| Wind framework | Development paper replay | 0.8278 | 0.8278 | Unchanged; still requires visual review |
| Attention-guided GIN | Development paper replay | 0.7993 | 0.7993 | Unchanged; still requires visual review |

These are SSIM-style screening values, NOT pass rates or calibrated fidelity scores. All four cases still trigger the existing visual-review rule. The synthetic results demonstrate the named defect fixes, not final visual acceptance. The two paper scores do not demonstrate a real-paper improvement.

Source hashes/locators: wind `db31d194acd69897fbd27d97835331e21801580c3fbca7a882b08cb16433b799`, page 3, crop `[303.2,66.7,557.8,364]`; GIN `489b449ef9efa52abc67ec08ee1b2af1fcc561b4324241b03f82e30a701062e7`, page 6, crop `[123.3,55.5,472.2,542]`. These match the frozen development crop fixture.

## Tests and limitations
The changed test suites exercise six angle directions, six narrow-font aliases, unchanged text/font size, reflected-angle and autofit mutations, and two aspect-ratio controls. Focused results: text import/audit 19 tests; importer 21 tests; first-pass gate 14 tests; all pass locally.

Full local unittest discovery ran 328 tests from the downloaded CI review archive: 322 succeeded; six errors were caused by assets absent from that archive, not bypassed. Four `test_audit_source_grounded_radar` cases lack `tests/fixtures/mmgraph_f2_table3.csv`; two `test_generalization_specs` cases lack the Mamba/Swin/expected-topology JSON fixtures. Full-repository remote CI must be verified separately. No independent code reviewer or real Office 2016 host was available for this run.

Remaining work: source-vs-host glyph metrics and baseline placement, target-font availability, actual paper raster/vector differences, and independent scientific/target-host acceptance. Automatic font shrinking and semantic relayout remain prohibited. Frozen strict first-pass score: **0/10 unchanged**.
