# Source Attribution and Evidence Boundaries

## User-provided visual references
A/B style profiles were derived from selected pages of a user-provided PowerPoint:
- Slide 189: black-and-white academic framework.
- Slide 208: pastel engineering architecture.
- Slide 213: online FDIR feedback loop and mode management.

The original PowerPoint is not redistributed. Only style characteristics and derivative redraws are included.

## FBG-SEANet (C01)
Primary paper: Lee et al., Engineering Applications of Artificial Intelligence 179 (2026), 115273.
DOI: https://doi.org/10.1016/j.engappai.2026.115273

Author-published graphical abstract:
https://hai.snu.ac.kr/bbs/board.php?bo_table=sub4_1_a&wr_id=251

The V7.3 redraw follows the visible FBG construction and SEANet two-branch diagnosis layout. It is not a pixel-level copy. Sensor photographs are replaced by editable vector silhouettes; graph coordinates and edges are reconstructed from the visible schematic and are not an asserted numerical adjacency matrix.

The article text explicitly defines the sensitivity-aware readout as SR. V7.3 uses SR rather than relying on the small raster preview's visually ambiguous label.

The publisher image is not redistributed in this repository. See docs/C01_V73_SOURCE.md and docs/C01_V73_QA.md for the evidence boundary and validation results.

## Evidence labels
- source-visible structural redraw: the published/user-provided figure was visually inspected and its visible structure redrawn.
- paper/code-grounded reconstruction: article text, equations, captions, or official code support the structure, but the original figure image was not directly inspected.
- domain adaptation: a new figure adapted to a domain rather than reproduced from one source.

Do not upgrade an evidence label without new source inspection.
