# P1-02 text direction, width and host layout preservation

Baseline: `d7213e7d6add52de4a0e84c4fd73ad193c2ac905`, Draft PR #10.

## Intent and root causes
Fix source-visible text errors before adding a layout repair engine. Preserve source text, anchors, font sizes, object counts and scientific topology.

Actual LibreOffice output exposed three independent defects: `atan2(-dir_y, dir_x)` reflects source text while preserving its AABB; the broad Arial mapping collapses ArialNarrow to regular Arial; and default `spAutoFit` can reflow source text even with `wrap="none"`. A separate image-comparison defect mistook 0.01pt page rounding for an aspect mismatch after integer rasterization.

## Chosen approach
Correct the angle sign in the existing importer; resolve Arial Narrow aliases before generic Arial; explicitly use `MSO_AUTO_SIZE.NONE`; audit angle and autofit as well as text-box bounds. Check physical PDF page ratios with the existing 0.003 tolerance before resampling raster grids. Keep visual similarity thresholds unchanged.

Rejected: global font shrinking, moving scientific nodes or connectors, rasterizing editable text, or silently resizing physically wrong pages. The implementation approach is a maintainer decision under the user's instruction to continue, not a new user-approved redesign.

## Boundaries
No OCR, new model, font binaries, user paper imagery, global size changes or automatic semantic relayout. Font availability remains a target-host requirement. LibreOffice evidence is not Office 2016 certification. The frozen strict ten-paper first-pass baseline remains 0/10.

## Verification
RED/GREEN tests: positive/negative/vertical angles, narrow aliases, source-size retention, rotation-only and autofit mutations, physical-vs-raster rounding and wrong-page rejection. Use actual render output for synthetic rotation/narrow probes and replay hash-matched wind/GIN development figures. Report unchanged paper scores and remaining visual risks rather than inferring a new blind pass rate.
