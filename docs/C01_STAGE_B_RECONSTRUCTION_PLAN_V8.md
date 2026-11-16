# C01 Stage-B editable reconstruction plan — V8

**Gate:** preparation only. Stage B must not start until a human reviewer approves the revised Stage-A target image.

## 1. Canvas and layout

- PowerPoint canvas: 13.333 × 7.5 in (16:9).
- Target render: 1920 × 1080 px (144 px/in).
- White slide surface; deep-blue section headers; restrained blue, teal, ochre and violet accents.
- Main method area occupies the left ~78% of the slide; Reading guide and Evidence boundary occupy the right column.
- Title, labels, annotations and source citation remain native editable text.

## 2. Native object decomposition

### Panel A — frequency-band graph construction

- Sensor-signal container and four editable waveform polylines.
- OCF/notch-filter module and band-pass-filter module.
- Frequency-band labels: B₁, B₂, B₃, …, Bₙ. N is variable; the four visible examples are representative only and must not imply a fixed four-band method.
- Each displayed B_i subgraph uses a three-node, two-link motif for visual consistency. This is a schematic icon, not recovered numerical adjacency.
- Total graph displays four representative rows for B₁, B₂, B₃ and Bₙ, each with three nodes. The total number of bands remains N.
- Sparse dashed cross-band links are schematic. Do not assert an exact dashed-link count or a numerical adjacency matrix.
- Frequency indicator is a native vertical arrow pointing downward.
- Total graph → Input is a cross-panel native connector.

### Panel B — graph-level fault diagnosis

- Input graph container with 12 editable node circles in four rows by three columns.
- Eight solid within-row edges. Dashed inter-row links are sparse illustrative connectors; their exact count is not asserted.
- Direct Input → first GCN route.
- Separate Input → Energy-assisted module → first GCN branch.
- Main path: GCN₁ → pooling₁ → GCN₂ → pooling₂ → IR₁ → Σ → Dense.
- Secondary branch: pooling₁ → IR₂ → Σ.
- Five square class outputs are an illustrative five-class example, not a fixed class count. Only C₂ uses the orange highlight.
- All connectors remain native PowerPoint line/connector objects.

### Right-side guidance

- Reading guide with Filter, Construct and Diagnose sections.
- Evidence boundary states: N is variable; graph links are schematic; no exact dashed-link count or numerical adjacency is asserted; five outputs are illustrative; IR/SR terminology remains unresolved.
- All labels and body text remain editable; no screenshot text.

## 3. Semantic object IDs

The shared FigureSpec renderer preserves each source element ID and semantic ID in the native PowerPoint shape name when Stage B invokes its opt-in provenance mode (`--preserve-source-ids`), using the convention `semantic_id__source_element_id__part`. Composite source elements (graph nodes/edges, polyline segments, sensor components and arrowheads) receive deterministic part suffixes. Default rendering remains unchanged to preserve legacy canonical PPTX hashes. The read-only `tools/audit_figure_spec_pptx.py` produces a source-element-to-native-object map and object inventory. This is a renderer capability/preflight only; it does not start C01 Stage B or approve the target image.


Use stable semantic IDs for the critical objects:

sensor_signals, ocf, bandpass, band_1–band_4, total_graph, frequency_axis, input, input_graph_schematic, gcn_1, pooling_1, gcn_2, pooling_2, ea, sr_main, sr_ea, sum, dense, class_output, reading_guide, evidence_boundary.

The source topology contract contains 18 critical directed method relationships. These are process/data-flow relationships, not the dashed internal graph links. The latter remain schematic and do not have an asserted exact count.

## 4. Release audits

1. Verify all 18 critical directed method relationships and required semantic nodes.
2. Verify variable-N labels B₁, B₂, B₃, …, Bₙ; do not imply a fixed four-band algorithm.
3. Verify the three-node schematic motif is used consistently in B_i subgraphs and visible Total graph rows.
4. Verify the 12-node / four-row-by-three Input glyph and eight solid within-row edges.
5. Confirm dashed cross-band and inter-row links are explicitly schematic; do not count them as a recovered topology or claim a numerical adjacency matrix.
6. Confirm only C₂ is orange and the five outputs are described as illustrative.
7. Confirm the Frequency arrow points downward and Total graph → Input is present.
8. Confirm both Input → GCN₁ and Input → EA → GCN₁ paths.
9. Confirm both IR-labelled readouts converge at Σ before Dense, while preserving the unresolved public-abstract SR terminology note.
10. Audit editable-text coverage, object inventory, alt text, text overlap and out-of-bounds geometry.
11. Reject a full-slide raster background; all diagram elements must remain editable native objects.
12. Render the PPTX and compare against the approved Stage-A target using SSIM, MAE and dHash.
13. Perform a real PowerPoint 2016 open/save/reopen round trip before final acceptance.

## 5. Evidence boundary

- The 18 critical directed relationships describe the method-level process and diagnosis paths.
- The three-node B_i and Total graph motifs are a visual-consistency choice, not a recovered numerical graph topology.
- The 12-node Input glyph is a four-by-three source-visible schematic; its dashed inter-row links are illustrative.
- No exact count of dashed cross-band or inter-row links is asserted.
- No numerical adjacency matrix is asserted.
- Five class outputs are an illustrative example; actual class count may vary.
- Preserve the author-lab visible IR labels and disclose that the public abstract uses SR. Do not silently harmonize the terms.

## 6. Entry condition

Stage B begins only when the Stage-A manifest records:
- target image path, dimensions and SHA-256;
- human reviewer identity and review timestamp;
- all six approval checks passed;
- no remaining blocking issues.

Until then, no PPTX reconstruction or parity result is claimed.
