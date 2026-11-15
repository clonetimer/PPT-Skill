# Source-figure crop fidelity — design (2026-11-14)

## Intent

Continue the accepted P1-01 source-first fidelity programme in
`docs/BLINDTEST_10PAPER_IMPROVEMENT_BACKLOG_2026-11-13.md`. A selected paper
figure must be the *same region* in source-layout extraction, editable PDF
import, structural/text audit, and rendered comparison. At present only the
source-layout sidecar receives `--region`, while the actual importer and QA
consume the full page.

## Contract

- `--region X0 Y0 X1 Y1` means PDF points on the **original selected page**,
  before normalization; output slide is exactly the region size.
- Exclude off-region shapes, labels, and pictures. Clip supported crossing
  vectors/images; if exact editing would misrepresent source ink (a rotated
  picture, partial glyph, or stroke fringe whose centerline is outside the
  crop), explicitly fail and require manual reconstruction. Preserve paint
  order and source bytes even when an output path aliases the source inode.
- All import-route audits inspect the selected region. Render comparison uses
  its pixel crop, never a stretched full-paper page.
- Reject nonfinite, inverted, out-of-page or unsupported rotated-page crops;
  require nonnegative zero-based API page indices / positive one-based CLI
  pages. Never silently fall back to the full page or the last page.
- Preserve original source hash, selected page index, region, and result
  provenance in the manifest. Do not claim human scientific/visual approval,
  Office 2016 host acceptance, or improved independent blind-test rate.

## Approaches

1. **Chosen: thread one validated crop through PDF readers.** Apply a
   temporary in-memory PyMuPDF cropbox to each reader and use PDF `clip` for
   visual comparison. This keeps the source immutable and avoids a derivative
   PDF with a different source hash.
2. Generate a cropped intermediary PDF and pass it to existing tools. This
   adds a second source hash, temporary copyrighted artifact and confusing
   page indexing; it is unnecessary for the current readers.
3. Crop only preview images or only PPTX shapes. This leaves vector/text QA
   and resource accounting inconsistent, so it cannot satisfy the contract.

## Boundaries

Scope is PDF-import/source-visual correspondence, not automatic panel
semantics, guessed arrow directions, style approximation, or a new blind set.
The frozen ten-paper 0/10 strict first pass remains a historical baseline;
corrected examples are only development regression evidence.
