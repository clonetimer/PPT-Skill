# C01 V7.3 Source and Evidence Record

## Primary paper
Lee, S. K., Kim, H., Chae, M., Kim, H., Yang, J., Yoon, H., & Youn, B. D. (2026). Frequency-band graph-based sensor fusion with sensitivity-aware energy assist network for machinery system fault diagnosis. Engineering Applications of Artificial Intelligence, 179, 115273. DOI: https://doi.org/10.1016/j.engappai.2026.115273

## Author-published graphical abstract
Seoul National University, Hyperautonomy Artificial Intelligence Lab:
https://hai.snu.ac.kr/bbs/board.php?bo_table=sub4_1_a&wr_id=251

Image:
https://hai.snu.ac.kr/data/editor/2606/78d439b23291567a99c14c62e0bbf0a6_1780552979_7277.jpg

## Paper-grounded statements
- FBG decomposes sensor signals into frequency bands, builds one subgraph per band, and connects the subgraphs into the final graph.
- OCF applies a notch filter to remove operational components.
- Band-pass filters produce frequency-specific subgraphs.
- SEANet uses a sensitivity-aware readout (SR) layer.
- EA embeds energy-related features into each graph node.

## Terminology
The article text explicitly defines the sensitivity-aware readout as SR. V7.3 uses SR rather than relying on the small preview's visually ambiguous glyph.

## Source boundary
The repository contains editable derivative redraws, not the publisher image. Sensor photographs are replaced with vector silhouettes and graph coordinates are schematic, not a numerical adjacency matrix.
