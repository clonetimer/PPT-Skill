# C01 Stage-B editable reconstruction plan — V8

**Gate:** preparation only. Stage B must not start until a human reviewer approves the Stage-A target image.

## 1. Canvas and layout

- PowerPoint canvas: 13.333 × 7.5 in (16:9).
- Target render: 1920 × 1080 px (144 px/in).
- White slide surface; deep-blue section headers; restrained blue, teal, ochre and violet accents.
- Main method area occupies the left ~78% of the slide; Reading guide and Evidence boundary occupy the right column.
- Title and source citation remain native editable text.

The current Image2 candidate is the composition reference. Final object coordinates are frozen only after Stage A is approved.

## 2. Native object decomposition

### Header and source

- Title banner and title text.
- Two section headers: frequency-band graph construction; graph-level fault diagnosis.
- Footer citation and DOI.

### Panel A — frequency-band graph construction

- Sensor-signal container and four editable waveform polylines.
- OCF/notch-filter module and band-pass-filter module.
- Four band-subgraph cards: B₁, B₂, B₃ and Bq.
- Each band card uses editable nodes, intra-band edges and text labels.
- Total graph uses four translucent layer polygons, 12 node circles, eight solid intra-layer edges and nine dashed inter-layer edges.
- Frequency indicator is a native vertical arrow pointing downward.
- Total graph → Input is a cross-panel native connector.

### Panel B — graph-level fault diagnosis

- Input graph container with 12 editable node circles in four rows by three columns.
- Eight solid intra-row edges and nine dashed inter-row edges.
- Direct Input → first GCN route.
- Separate Input → Energy-assisted module → first GCN branch.
- Main path: GCN₁ → pooling₁ → GCN₂ → pooling₂ → IR₁ → Σ → Dense.
- Secondary branch: pooling₁ → IR₂ → Σ.
- Five square class outputs C₁–C₅; only C₂ uses the orange highlight.
- All connectors remain native PowerPoint line/connector objects.

### Right-side guidance

- Reading guide with Filter, Construct and Diagnose sections.
- Evidence boundary with schematic-adjacency disclaimer and unresolved IR/SR terminology note.
- All labels and body text remain editable; no screenshot text.

## 3. Semantic object IDs

Use stable semantic IDs for the critical objects:

`sensor_signals`, `ocf`, `bandpass`, `band_1`–`band_4`, `total_graph`, `frequency_axis`, `input`, `input_graph`, `gcn_1`, `pooling_1`, `gcn_2`, `pooling_2`, `ea`, `ir_main`, `ir_branch`, `sum`, `dense`, `class_output`, `reading_guide`, `evidence_boundary`.

Critical connectors use the 18 directed relationships in `specs/c01_composite_expected_topology_v75.json`.

## 4. Release audits

1. Verify every required semantic node and all 18 directed relationships.
2. Verify the four band layers, 12-node/four-row Input graph, eight intra-layer edges, nine inter-layer edges and five class outputs.
3. Confirm only C₂ is orange.
4. Confirm the Frequency arrow points downward and Total graph → Input is present.
5. Confirm the direct Input → GCN₁ route and Input → EA → GCN₁ branch both exist.
6. Confirm both IR readouts converge at Σ before Dense.
7. Audit editable-text coverage, object inventory, alt text, text overlap and out-of-bounds geometry.
8. Reject a full-slide raster background; all diagram elements must remain editable native objects.
9. Render the PPTX and compare against the approved Stage-A target using SSIM, MAE and dHash.
10. Perform a real PowerPoint 2016 open/save/reopen round trip before final acceptance.

## 5. Non-negotiable evidence boundary

The graph drawing is a schematic representation. Do not claim a numerical adjacency matrix or invent exact physical connectivity. Preserve the source-visible IR labels and disclose the unresolved public-abstract SR terminology discrepancy; do not silently expand either abbreviation.

## 6. Entry condition

Stage B begins only when the Stage-A manifest records:
- target image path, dimensions and SHA-256;
- human reviewer identity and review timestamp;
- all six approval checks passed;
- no remaining blocking issues.

Until then, the plan is prepared but no PPTX reconstruction or parity result is claimed.
