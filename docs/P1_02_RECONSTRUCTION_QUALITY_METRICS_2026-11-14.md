# P1-02 Reconstruction Quality Metrics

## Command

```powershell
python tools/reconstruction_quality_metrics.py .\qa\source_composition_manifest.json .\qa\imported_figure.pptx --output .\qa\reconstruction_quality_metrics.json
```

Optional visual comparison evidence can be supplied with `--visual-report` from the existing first-pass PDF rendering comparison.

## Separate metric dimensions

- **Object preservation:** expected/actual counts, source object recall, unexpected object rate, missing/duplicate IDs, and class mismatches.
- **Source order:** exact order and Kendall tau over objects with native PDF paint-order indices. Unsequenced text spans are excluded.
- **Text fidelity:** NFC-normalized character error rate (CER), exact span matches, and missing/duplicated text spans. Punctuation and mathematical symbols are retained.
- **Geometry fidelity:** per-object bounding-box IoU only when the selected source region begins at the full-page origin and the coordinate mapping is directly comparable. Other crops/transforms are `NOT_COMPARABLE`.
- **Visual similarity:** optional existing rendered-PDF report with renderer/DPI provenance.
- **Scientific correctness:** explicitly `NOT_AUTOMATED`; requires independent human/domain review.
- **Office 2016:** explicitly `NOT_VERIFIED_BY_THIS_METRIC`; requires the real host test.

## Interpretation

The tool emits no blended score. Missing/duplicate source objects, class mismatches, malformed provenance, source-order mismatch, or an explicit visual discrepancy produce `FAIL`. A technically consistent import without visual evidence remains `NEEDS_REVIEW`. `TECHNICAL_PASS` requires applicable technical evidence and does not approve science or target-host rendering.

Geometry metrics are deliberately withheld for cropped/unknown coordinate transforms. Do not treat `NOT_COMPARABLE` as zero, pass, or failure. The frozen ten-paper strict first-pass result remains 0/10; those papers are development data only.
