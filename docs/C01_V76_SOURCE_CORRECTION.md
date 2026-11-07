# C01 V7.6 publisher-source correction

On 2026-11-07, the [publisher graphical abstract](https://ars.els-cdn.com/content/image/1-s2.0-S0952197626015575-ga1_lrg.jpg) was inspected at 1198 × 886 pixels. The JPEG downloaded for internal inspection had SHA-256 `17fc513156d13b314647c54cad9618f1b55df265c08abe8c300e4ddfb9962d5b`. The [author-posted copy](https://hai.snu.ac.kr/bbs/board.php?bo_table=sub4_1_a&wr_id=251) and [article abstract](https://www.sciencedirect.com/science/article/pii/S0952197626015575) provide independent provenance and terminology. Neither source image is committed or redistributed.

| Relation | Earlier redraw | Publisher graphical abstract and corrected redraw |
|---|---|---|
| Energy assist | Input → EA → lower SR | Input → EA → first GCN; the main input also enters that GCN |
| Lower readout | EA → lower SR | First pooling → lower SR → summation |
| Main readout | GCN/pooling → SR → summation | Same path; both readout boxes visibly say SR |
| Output | Summation → generic diagnosis arrow | Summation → Dense → fault-class output |

The corrected composite has 17 checked critical routes: five in the frequency-band panel, the total-graph-to-SEANet-input connection, and eleven in the diagnosis panel. The standalone SEANet diagram has twelve checked routes. `tools/validate_scientific_ir.py` compares declared edges to visible segment geometry and arrow direction; mutation tests reject the former EA-to-lower-SR shortcut and missing Dense route. The three-slide benchmark deck embeds the corrected composite. The [second-pass comparison](C01_LITERATURE_COMPARISON_2026-11-07.md) records explicit band-pass labeling, the OCF fault-cue explanation and schematic inter-band links.

The diagrams remain *structural redraws*. Sensor glyphs and graph adjacency are schematic. This inspection confirms the listed visible labels and routes; it does not establish pixel similarity, full-paper figure identity, domain approval or readability at a real projection distance. Pixel identity is not a suitable acceptance target for the reflowed defense layout; independent domain/final-size review remains pending. The V7.3/V7.4 QA reports preserve the earlier historical snapshots and should be read with this correction.

The second-pass source comparison also corrected the standalone FBG title from `time-frequency graph` to the publisher's `frequency-band graph` and added a qualitative OCF fault-cue label. These are recorded as explicit historical-label exceptions, not as evidence for numerical graph adjacency.
