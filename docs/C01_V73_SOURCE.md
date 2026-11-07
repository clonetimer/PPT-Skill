# C01 V7.3 Source and Evidence Record

## Primary paper
Lee, S. K., Kim, H., Chae, M., Kim, H., Yang, J., Yoon, H., & Youn, B. D. (2026). Frequency-band graph-based sensor fusion with sensitivity-aware energy assist network for machinery system fault diagnosis. Engineering Applications of Artificial Intelligence, 179, 115273. DOI: https://doi.org/10.1016/j.engappai.2026.115273

## Author-published graphical abstract
Seoul National University, Hyperautonomy Artificial Intelligence Lab:
https://hai.snu.ac.kr/bbs/board.php?bo_table=sub4_1_a&wr_id=251

Image:
https://hai.snu.ac.kr/data/editor/2606/78d439b23291567a99c14c62e0bbf0a6_1780552979_7277.jpg

## Publisher graphical abstract checked in V7.6
Publisher-hosted high-resolution JPEG:
https://ars.els-cdn.com/content/image/1-s2.0-S0952197626015575-ga1_lrg.jpg

The 1198 × 886 image was visually inspected on 2026-11-07; SHA-256 of the downloaded JPEG is `17fc513156d13b314647c54cad9618f1b55df265c08abe8c300e4ddfb9962d5b`. The publisher image is used for internal source comparison and is not redistributed in this repository. Reviewers should inspect the linked image directly before consulting the second-stage correction report.

## Paper-grounded statements
- FBG decomposes sensor signals into frequency bands, builds one subgraph per band, and connects the subgraphs into the final graph.
- OCF applies a notch filter to remove operational components.
- Band-pass filters produce frequency-specific subgraphs.
- SEANet uses a sensitivity-aware readout (SR) layer.
- EA embeds energy-related features into each graph node.

## Terminology
The article text explicitly defines the sensitivity-aware readout as SR. The publisher graphical abstract visibly labels both readout boxes SR; the smaller author-site copy can look ambiguous.

## Source boundary
The repository contains editable derivative redraws, not the publisher image. Sensor photographs are replaced with vector silhouettes and graph coordinates are schematic, not a numerical adjacency matrix. Pixel overlay and independent domain review remain pending; the checked graphical abstract supports the listed labels and routes, not exact visual identity.
