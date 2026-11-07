# V7.1.1 Visual QA — Resolved and Remaining Issues

## Resolved
- A01: narrowed the online-diagnosis section heading to remove collision with the KG-evidence annotation.
- B01: combined state descriptions into explicit short lines and shortened transition labels.
- B01/F07: generated from JSON FigureSpec, with one source driving SVG and native PowerPoint output.
- B01/F07: removed the default theme shadow style.
- C01: corrected OCF label to Notch filter and IR to SR; removed stale duplicate method blocks and duplicate summation operator; softened panel boundaries.
- F07: replaced 1,600 cell rectangles with a 40×40 native line grid and five-plane temporal stack. Counts are shown without fabricating a row-major cell map.
- All four slides: latest PDF render checked; no out-of-bounds shapes or text-box intersections detected.

## Remaining
- A01: style redraw, not a pixel-accurate reproduction of source slide 189.
- B01: engineering adaptation of FDIR/mode management, not a reproduction of a published figure or the user's original slide.
- C01: source-visible structural redraw. Sensor glyphs are vector stand-ins; some graph topology remains schematic. A region-by-region overlay against the author-published graphic is still required.
- F07: exact channel-to-cell coordinates are not available; the grid remains neutral and explicitly schematic.
- Historical V7.1 status: dual rendering covered B01/F07 only. Current V7.6 development examples also cover C01, four Iris charts and one image-plus-quantification panel.
- SVG and Office rendering are not pixel-identical because font metrics and text engines differ.
- Windows PowerPoint and macOS PowerPoint still require independent checks.

V7.1.1 is a refined prototype, not a stable release. Do not claim C01 high-fidelity reproduction until original-figure overlay review is complete.
