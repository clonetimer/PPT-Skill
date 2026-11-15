# P1-02 Multi-Dimensional Reconstruction Quality Metrics

**Date:** 2026-11-14  
**Status:** Design baseline

## Objective

Evaluate source-PDF-to-PPTX reconstruction using independent, interpretable metrics. Do not collapse editability, geometric fidelity, scientific correctness, and visual similarity into one opaque score.

## Metric dimensions

### A. Object preservation
- Source object recall: source objects expected by the composition manifest that appear exactly once in the PPTX, divided by expected objects.
- Unexpected object rate: annotated PPTX source objects not present in the manifest, divided by actual annotated objects.
- Duplicate object count: source IDs appearing more than once.
- Object-class accuracy: expected image/vector/text class matches actual PowerPoint picture/vector/text shape class.

### B. Source-order fidelity
- Compare ordered source paint-order IDs against actual PPTX shape order for objects with a native source order.
- Report exact-order rate and normalized Kendall tau.
- Text spans without a native paint-order index are excluded from this metric and reported separately; do not invent paint-order values for text.

### C. Geometry fidelity
- Report per-object bounding-box IoU and normalized center/size errors only when the source-to-slide coordinate transform is explicitly known and hash-locked.
- The first implementation supports full-page imports with a validated page-coordinate transform.
- Cropped or rotated source pages without an explicit transform are marked `NOT_COMPARABLE`, not assigned fabricated scores.

### D. Text fidelity
- Compare extracted source PDF text spans with PPTX text from matching source-object IDs.
- Report exact-match rate, normalized character error rate (CER), and missing/extra text spans.
- Preserve case and symbols. Unicode normalization is recorded; math symbols are not silently substituted.
- Font family/size/rotation checks are separate from textual CER.

### E. Raster fidelity
- Report source-image identity and dimensions, aspect-ratio error, crop/transform metadata, and optional image pixel similarity.
- If the importer embeds a transformed/re-encoded image and exact source bytes are not available, mark pixel identity as `NOT_COMPARABLE`; do not call it a pass.
- Full-figure rendered comparison remains a separate visual metric.

### F. Visual similarity
- Reuse the existing `compare_rendered_pages` pipeline and report global similarity, mean absolute difference, worst tiles, and visual-review triggers.
- State renderer and DPI. LibreOffice output is not equivalent to PowerPoint 2016 output.
- Never interpret the SSIM-style screening score as calibrated scientific correctness.

### G. Scientific correctness
- Human/domain review separately scores scientific nodes, labels, numerical values, topology/direction, and causal interpretation against frozen source-grounded contracts.
- Automated object metrics cannot award scientific correctness.
- No model-generated self-score may be presented as independent domain review.

## Reporting contract

Every report contains:
- source PDF, SourceLayout, review, route, composition manifest, and PPTX SHA-256;
- metric values, denominators, excluded/not-comparable counts, and explicit reasons;
- separate technical status and scientific/host review statuses;
- no single blended score;
- immutable first-attempt identifier and separate repair-attempt lineage.

## Status rules

- `FAIL`: missing/duplicate source objects, wrong object class, or order violation beyond the declared contract.
- `NEEDS_REVIEW`: non-comparable transforms, source glyph uncertainty, unresolved visual discrepancy, or human scientific review pending.
- `TECHNICAL_PASS`: all applicable object/text/geometry/visual technical gates pass; scientific and Office host approvals remain separate.
- `NOT_COMPARABLE`: evidence or coordinate mapping is insufficient; never coerce this to zero or pass.

## Validation strategy

- Synthetic fixtures with known expected object IDs, shapes, text, geometry, and order.
- Mutation tests remove, duplicate, reorder, resize, and reclassify objects.
- Coordinate transform tests include nonzero crop origin and non-integer scale.
- CER tests include punctuation, Unicode normalization, Greek letters, superscripts, and missing glyphs.
- The ten development papers can be replayed for debugging, but must not be described as a new blind holdout. The frozen strict first-pass baseline remains 0/10.
