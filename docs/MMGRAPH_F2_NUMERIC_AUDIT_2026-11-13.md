# MMGraph-Agent F2 — source-grounded radar numeric audit (2026-11-13)

Source: Luo et al., [MMGraph-Agent](https://arxiv.org/abs/2611.10657), 2026, **Table 3**. The fixture contains only numerical F1 means and dataset identifiers; source figure images, photos and derivative PPTX files are not committed to this public repository.

## What the curves encode

The two F2 radar panels contain **9 axes and 9 methods each**. Radius is **not raw F1**:

\`r(method,dataset) = F1(method,dataset) / F1(MMGraph-Agent,dataset)\`.

The first panel has DocBench, MMLongBench-Doc, ViDoSeek, **Text-only Avg(6)**, FVQA, InfoSeek, MMSearch, SimpleVQA and LiveVQA. For the six-text-dataset aggregate, **average F1 values before dividing**, not average the six ratios. The second panel contains nine Knowledge+WebSearch datasets. Red MMGraph-Agent reference polygons have unit radius at every axis. The independent audit reads each native PowerPoint freeform's nine vertices; it does not infer data by image OCR.

## Observed result

| Panel | Source-visible PPTX candidate | Alternative aligned to Table 3 |
|---|---|---|
| K + WebSearch-only | **FAIL:** one axis of StdMMRAG/GPT differs | PASS |
| K+Web | PASS | PASS |

The single discrepancy in the first panel is **Standard MMRAG / GPT-4.1-mini at Text-only Avg(6)**:

- Table 3 F1(StdMMRAG-GPT), six-dataset mean: **10.9416667**
- Table 3 F1(MMGraph-Agent), six-dataset mean: **20.44**
- Expected normalized radius: **0.5353066**
- Recovered source-visible PPTX radius: approximately **0.52730**
- Absolute discrepancy: approximately **0.00801**, greater than the 0.003 audit gate

These measurements do not establish that the publisher artwork is wrong: authors may have generated the source figure from a different intermediate table. Preserve **both** the source-visible original and a separately named \`MMGraph_F2_Table3_Corrected.pptx\`. The correction script updates only this source-grounded vertex on the two overlapping editable freeforms, without flattening the chart or changing its other series. After correction, the maximum absolute normalized discrepancy on either panel is less than **0.0002**.

The 0.003 gate is a *numeric regression threshold*, not a visual score. We did not have the independent author \`F2.pdf\` available in the current container to re-evaluate full vector geometry or source-PDF SSIM. Screenshot comparison alone is not evidence for numerical fidelity.

## Reproduce

\`\`\`bash
python tools/audit_source_grounded_radar.py original_F2.pptx \
  --table tests/fixtures/mmgraph_f2_table3.csv \
  --manifest tests/fixtures/mmgraph_f2_radar_manifest.json \
  --report original_audit.json

python tools/correct_source_grounded_radar.py original_F2.pptx \
  --table tests/fixtures/mmgraph_f2_table3.csv \
  --manifest tests/fixtures/mmgraph_f2_radar_manifest.json \
  --output F2_Table3_Corrected.pptx \
  --report corrections.json --apply-data-corrections
\`\`\`

Without \`--apply-data-corrections\`, the correction utility refuses to edit scientific values. It also refuses to overwrite the input. \`tools/test_audit_source_grounded_radar.py\` runs a source-driven two-radar synthetic positive case and a deliberately mutated We-Math2.0 value negative case.

## Limits

- Some tiny legend glyphs may still be native PDF vector outlines rather than editable PowerPoint text.
- Screenshot SSIM and the Table 3 numeric geometry audit are separate checks.
- Actual Windows PowerPoint 2016 open, save, PDF/PNG export, and manual final-size inspection remain required.
