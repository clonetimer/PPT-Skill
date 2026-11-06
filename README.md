# Academic Defense PPT Skill

## V7.3.0 — C01 source-matched vector reconstruction
C01 was rebuilt from the author-published FBG-SEANet graphical abstract as two editable 16:9 slides:
1. FBG construction: sensor signals → OCF/notch filter → frequency-band subgraphs → total graph.
2. SEANet diagnosis: GCN/pooling main path and EA/SR branch converging at the summation node.

V7.3 removes unsupported frequency-response waveforms and invented downstream classifier/representation boxes from V7.2. The readout is labeled SR according to the article text.

## FigureSpec
Canonical JSON:
- figure_specs/c01/C01_FBG_construction.json
- figure_specs/c01/C01_SEANet_graph_level.json

Build and validate:
python tools/build_c01_v73.py
python tools/validate_c01_v73.py

## Source
Lee et al., Engineering Applications of Artificial Intelligence 179 (2026), 115273. DOI 10.1016/j.engappai.2026.115273.
Author page: https://hai.snu.ac.kr/bbs/board.php?bo_table=sub4_1_a&wr_id=251

The original image is not redistributed. Sensor photographs are replaced with vector silhouettes; graph coordinates are schematic. V7.3 is a structural redraw, not pixel-identical.
