# Native PowerPoint object provenance — Image-first V8

## Purpose

Image-first Stage B must produce a slide whose text, panels, graph glyphs, arrows and connectors are independently editable. Visual similarity alone is insufficient. Each native object must also be traceable to its source FigureSpec element so that local repairs can be audited without losing provenance.

## Renderer naming contract

`tools/render_figure_spec.py` writes stable native PowerPoint shape names when the opt-in `--preserve-source-ids` flag is enabled. Default rendering remains byte-compatible with the existing canonical PPTX baselines. The opt-in names use the form:

`semantic_id__source_element_id__part`

- `semantic_id` identifies the scientific or presentation role.
- `source_element_id` is the stable FigureSpec element ID.
- `part` identifies the native object generated from that element.

Composite FigureSpec elements are expanded into deterministic native object names:
- graph: `edge-01`, `edge-02`, … and `node-01`, `node-02`, …;
- polyline: `segment-01`, `segment-02`, …;
- line with arrow: `line` and `arrowhead`;
- sensor glyph: `sensor-body`, `sensor-stem`, `sensor-foot`;
- grid: `grid-base`, `grid-column-01`, `grid-row-01`, …;
- polygon, rectangle, ellipse, text and picture: one source-linked native object.

The names do not alter visible geometry or text. They provide a stable handle for native-object diffs and localized corrections.

## Audit utility

Run:

```bash
python tools/render_figure_spec.py path/to/figure_spec.json --svg dist/figure.svg --pptx dist/figure.pptx --preserve-source-ids
python tools/audit_figure_spec_pptx.py path/to/figure_spec.json dist/figure.pptx --report dist/object_provenance.json
```

The audit reports:
- source-element coverage;
- missing source element IDs;
- semantic-object counts;
- native text, shape, connector, chart and picture inventory;
- a per-source-element map of native PowerPoint shape names.

The audit is read-only. It does not edit the FigureSpec or PPTX.

## Regression coverage

`tools/test_figure_spec_pptx_provenance.py` verifies:
1. semantic IDs and source element IDs survive opt-in provenance rendering;
2. default rendering leaves legacy shape names and canonical outputs unchanged;
3. composite graph, polyline and arrow elements receive deterministic part names;
4. every supported source element is mapped by the audit;
5. duplicate source element IDs are rejected.

## Gate boundary

This preflight qualifies the generic native-object renderer and provenance audit. It is **not** the C01 Stage-B reconstruction, does not use the V3 Image2 target as an accepted visual reference, and does not produce a parity score. C01 Stage B remains locked until the designated human reviewer approves Stage A.
