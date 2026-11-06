# V7.1.1 QA Report

## Scope
Four-slide refined prototype:
1. A01 — black-and-white academic framework.
2. B01 — engineering FDIR and mode-state management.
3. C01 — FBG-SEANet source-visible structural redraw.
4. F07 — telemetry vector, 40×40 feature grid, and L=5 temporal stack.

## Programmatic audit
- Slides: 4
- PowerPoint shapes: 396 total
- Text-box overlaps: 0
- Out-of-bounds objects: 0
- Theme first effect style: empty (no inherited shadow)
- B01/F07 generated PPTX picture objects: 0
- C01 uses 12 SVG vector picture objects; there are no non-SVG picture objects.

Per-slide counts:
- A01: 52 shapes, 0 text overlaps, 0 out of bounds.
- B01: 55 shapes, 0 text overlaps, 0 out of bounds.
- C01: 109 shapes, 12 SVG picture objects, 0 text overlaps, 0 out of bounds.
- F07: 180 shapes, 0 picture objects, 0 text overlaps, 0 out of bounds.

## FigureSpec dual-render validation
The validator rendered both JSON specs to SVG and editable PPTX:
- B01: 55 native shapes, 0 pictures, 0 out of bounds, 0 text overlaps, no theme shadow.
- F07: 180 native shapes, 0 pictures, 0 out of bounds, 0 text overlaps, no theme shadow.

F07 uses 39 internal vertical and 39 internal horizontal grid lines plus an outer boundary; it does not create 1,600 cell rectangles. The exact channel-to-cell mapping is not claimed.

## Visual QA
- B01: former state-description overlaps and transition-label wraps are removed.
- C01: duplicate box layers and duplicate summation operator removed; OCF notch-filter and SR readout terminology corrected.
- F07: neutral grid, explicit valid/padded counts, schematic-occupancy caveat, and five-plane temporal stack.
- A01: section heading no longer intersects KG evidence annotation.

## Rendering boundary
B01/F07 are generated from the same FigureSpec, but SVG and PowerPoint are not pixel-identical. Font metrics, antialiasing, and renderer-specific text placement differ. CJK SVG fallback is Noto Sans CJK SC / DejaVu Sans / Microsoft YaHei; PowerPoint text uses Microsoft YaHei.

## Evidence boundaries
- A01/B01: derivative redraws of user-provided visual styles / engineering concepts.
- C01: source-visible structural redraw, not pixel-level reproduction.
- F07: article-text/equation-grounded telemetry embedding representation, not a direct copy of the original paper artwork.

## Acceptance
V7.1.1 resolves the specific layout defects listed in KNOWN_ISSUES_V7.md. It remains a prototype. Windows PowerPoint rendering and strict C01 original-figure overlay remain open.
