# C01 V7.6 publisher-source correction

On 2026-11-07, the [publisher graphical abstract](https://ars.els-cdn.com/content/image/1-s2.0-S0952197626015575-ga1_lrg.jpg) was inspected at 1198 × 886 pixels. The JPEG downloaded for internal inspection had SHA-256 `17fc513156d13b314647c54cad9618f1b55df265c08abe8c300e4ddfb9962d5b`. The [author-posted copy](https://hai.snu.ac.kr/bbs/board.php?bo_table=sub4_1_a&wr_id=251) and [article abstract](https://www.sciencedirect.com/science/article/pii/S0952197626015575) provide independent provenance and terminology. Neither source image is committed or redistributed.

| Relation | Earlier redraw | Publisher graphical abstract and corrected redraw |
|---|---|---|
| Energy assist | Input → EA → lower SR | Input → EA → first GCN; the main input also enters that GCN |
| Lower readout | EA → lower SR | First pooling → lower SR → summation |
| Main readout | GCN/pooling → SR → summation | Same path; both readout boxes visibly say SR |
| Output | Summation → generic diagnosis arrow | Summation → Dense → fault-class output |

The corrected composite has 16 checked critical routes: five in the frequency-band panel and eleven in the diagnosis panel. The standalone SEANet diagram has twelve checked routes. `tools/validate_scientific_ir.py` compares declared edges to visible segment geometry and arrow direction; mutation tests reject the former EA-to-lower-SR shortcut and missing Dense route. The three-slide benchmark deck embeds the corrected composite.

The diagrams remain *structural redraws*. Sensor glyphs and graph adjacency are schematic. This inspection confirms the listed visible labels and routes; it does not establish pixel similarity, full-paper figure identity, domain approval or readability at a real projection distance. Pixel overlay and independent domain/final-size review remain pending. The V7.3/V7.4 QA reports preserve the earlier historical snapshots and should be read with this correction.
