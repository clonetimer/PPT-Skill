# C01-SEANet first local repair case — 2026-11-14

## Defect and scope

The standalone SEANet redraw has a small but visible alignment defect: the `fault class` output label is center-aligned inside a text box whose right edge is already aligned with the output glyph. This leaves the label visually left-shifted relative to the output marker.

The first repair changes only the paragraph alignment of FigureSpec element `el_0052` from center to right. It does not change the label text, scientific topology, font family, font size, text-box position, dimensions, object order, or any connector.

## Evidence and source boundary

The figure's scientific topology is checked against the publisher graphical abstract and the paper-grounded statements recorded in `docs/C01_V73_SOURCE.md` and `docs/C01_V76_SOURCE_CORRECTION.md`. The 12 standalone critical routes remain unchanged. The repair is a presentation alignment adjustment, not a scientific correction. The source redraw remains schematic for sensor glyphs and graph adjacency.

## Executed repair

- Immutable initial FigureSpec fixture: `tests/fixtures/C01_SEANet_graph_level_initial_v73.json`
- Current source of truth: `figure_specs/c01/C01_SEANet_graph_level.json`
- Target stable element ID: `el_0052` (`fault class`)
- Operation: `set_alignment(center -> right)`
- Repair rounds: 1 accepted, 0 rejected
- Object-level diff: exactly one object, paragraph alignment only
- Source object inventory: 88/88 unique and preserved
- Source-order fidelity: exact match; Kendall tau = 1.0
- Text fidelity: 14/14 spans exact; CER = 0
- Comparable geometry: mean bounding-box IoU = 1.0
- PPTX parity against final FigureSpec render: PASS
- Strict PPTX audit: 88 shapes, 0 pictures, 0 out-of-bounds, 0 text-box overlaps, no theme shadow

The quality engine returns `NEEDS_REVIEW` rather than final PASS because independent human review is still required. Its manifest is explicitly an editable FigureSpec/PPTX repair baseline, not a publisher-PDF source layout. The metrics establish that the local edit did not damage the existing PPTX object structure; they do not establish source-image fidelity.

## Actual render verification

LibreOffice exported both the immutable first pass and repaired PPTX to PDF at 90 DPI. The rendered pixel diff is confined to the output-label region:
- image size: 1200 × 675
- changed pixels at threshold 8: 342 (0.0422%)
- changed bounding box: `[1093, 372, 1152, 383]`
- all other rendered regions are pixel-identical under this comparison.

PowerPoint 2016 host rendering and independent domain review remain separate acceptance gates.

## Final review

Status: **PENDING**. This repair is comparison-ready, not yet counted as a final delivery PASS. Reviewer should confirm the label's visual alignment at presentation size and verify the six rubric dimensions with evidence.
