# Scientific Figure Planning (7.7.0-dev)

Identify the scientific task, inspect relevant paper figures, read the evidence, and choose graphical encodings that explain the claim. **Evidence type and visual expression are independent choices.** FigurePlan is an optional compiler for supported structural parts through the existing FigureSpec renderer; its preset vocabulary does not limit a whole paper figure. The agent or researcher authors its input; the planner validates references and selects glyphs. It does not parse arbitrary programs or establish scientific truth. Source-specific FigureSpec/vector geometry, existing python-pptx rendering, native components and chart contracts remain available.

Contents: [Route](#1-select-the-route) · [Evidence](#2-read-evidence-and-choose-visual-objects) · [Schema](#3-author-the-brief) · [Example](#4-run-a-complete-synthetic-example) · [Review](#5-review-the-actual-output)

## 1. Select the route

### Identify the scientific task and inspect paper figures

For an **academic paper figure / 学术论文插图** requested from code or a paper, first identify which scientific task the figure serves. Multiple tasks may occupy separate panels. Then choose the visual form from the source, the user's request and inspected scholarly references, while recording the evidence for each claim separately.

| Scientific task | What to produce |
| --- | --- |
| Method / mechanism figure | A checkable visual explanation of variables, operations, dimensions, neighborhoods/propagation, hierarchy, branches and fusion, using native/vector geometry. |
| Quantitative results figure | Data-driven marks with evidenced values, units, analysis definitions, uncertainty and axes. |
| Experimental apparatus / study-object figure | Real source photographs or microscopy, documented apparatus geometry, or a faithful schematic with clear observation/schematic status. |
| Graphical abstract / concept figure | A compact visual account of the scientific claim; exact relations remain checkable, and any object/scene artwork serves a specific explanatory role. |

Before drawing, **view the original paper figures and established paper figures for similar scientific tasks**, including the actual images and captions. If the source has no figure, record that limitation and inspect suitable published visual references. Record what their composition, panel structure, notation, repeated objects and line grammar communicate. Use the original paper/code for scientific content; use comparison figures for expression. A similar-looking architecture is not evidence that its internal mechanism exists in the user's implementation.

The phrases **科研插画、图形摘要、不要方框图/流程图** do not select an imagegen route. For a rejected generic method diagram, replace labels-in-boxes with source-derived graphical encoding: show the scientific objects and how they change or interact. Recoloring boxes, adding decorative dots or attaching a satellite does not explain a mechanism. Do not automatically convert this request into a science-popularization scene, cover image or asset poster.

### Assign tools to the information being shown

- **Precise scientific content:** use native/vector geometry or data tools for variables, mathematical operators, exact dependencies, dimensions, numerical marks, axes and labels. The geometry must express the information, not merely decorate a sequence of module names. Use source-specific FigureSpec or custom vector geometry when presets cannot represent it faithfully.
- **Observed images and apparatus:** use real source photographs, microscopy and documented equipment references, with provenance and relevant processing history. Draw a schematic only to the extent the sources support its geometry and connections. Missing internal structure remains unknown; an imagined cutaway is not evidence.
- **Non-precise illustrative content:** imagegen is appropriate only when an object/scene has a scientific explanatory purpose or the user explicitly requests conceptual artwork. It is optional, not a default repair for an unsuccessful method figure. If chosen, generate and inspect the artwork, disclose its illustrative status, and check any precise overlay after composition. Never use it to fabricate experimental images, measurement curves, maps or heatmaps as evidence.

These choices are independent of evidence type: a paper-grounded figure can include necessary raster images, and a graphical abstract can be entirely vector. Prefer editable objects for precise information; native/vector-first does not impose a zero-raster target. Honor an explicit all-native requirement by constructing native shapes/freeform curves or converting suitably licensed SVG geometry into editable objects and checking the requested host. An embedded SVG picture alone is insufficient. No preliminary imagegen study is required.

FigurePlan's 12 structural kinds are optional reusable components, not the permitted vocabulary of a paper figure. Do not force the whole figure into these kinds or invent `process` nodes to satisfy the schema. The ordinary figure brief can describe custom geometry and image layers without adding FigurePlan fields or a new schema.

### Use the existing routes for each layer or tool task

The following `intent` values describe tasks handled by existing tool routes. They do not classify every paper figure or determine its whole composition. Use the structural compiler only where its components fit; custom source-specific drawings and data tools remain available independently.

| `intent` | Evidence to read | Route and next action |
| --- | --- | --- |
| `redraw` | Actual reference figure and its caption | `source_spec / source_matched`: use the existing source-specific FigureSpec workflow; preserve inspected anchors and composition. |
| `reconstruct` | Paper method/equations and relevant code | `native / scientific_semantic`: compile supported computation/structure parts; use source-specific FigureSpec/vector geometry for mechanisms outside this vocabulary. |
| `conceptual` | A selected conceptual-artwork task and applicable source material | `imagegen / conceptual`: the planner records a handoff for disclosed illustrative artwork. A graphical abstract or paper-figure request does not automatically select this route. |
| `quantitative` | Raw data, units and analysis definitions | `existing_chart_pipeline / quantitative`: use the existing chart/data contract and its builder. |
| `workflow` | Real process or control steps | `native / engineering_flow`: functional rectangles and decision marks express the steps. |

The planner reports all five routes. The semantic compiler handles the structural content of `reconstruct` and `workflow`; it returns an explicit handoff for the other routes and does not invoke imagegen. For `redraw`, author a source-specific FigureSpec after inspecting the image, then use `python tools/render_figure_spec.py source.json --svg source.svg --pptx source.pptx` and the existing source-grammar checks. Preserve source-visible composition and marks; do not replace them with generated imagery or semantic presets merely because an operator has a familiar name. Imagegen and chart routes use their existing tools when selected. The semantic compiler does not embed arbitrary image panels; compose necessary image layers through the existing image/FigureSpec path.

## 2. Read evidence and choose visual objects

For a paper, identify the figure/panel, relevant formula and symbol definitions. For code, inspect the entry module and the methods implementing the claimed path; cite file lines or class/method names, configuration and known shapes. Compare training/inference and shared branches where they affect the claim. A reference image supports visible labels, objects and arrows; hidden adjacency, head fusion or weights need separate support. Record unresolved details explicitly.

Translate source-supported information into marks with an explicit meaning:

| Scientific information | Graphical encoding to consider |
| --- | --- |
| Variables and dimensions | Named vectors, matrices, tensor planes or indexed groups with supported dimensions and consistent symbols. |
| Operations and transformed states | Distinct mathematical operators and visible input/output states; use a reduction, segmented concatenation or sum junction only for the corresponding operation. |
| Neighborhoods and propagation | Evidenced adjacency, directed messages or local aggregation around identified nodes; distinguish a schematic neighborhood from a measured graph. |
| Repetition and hierarchy | Indexed heads, repeated elements, nested groups or levels whose count and role match the source. |
| Branches and fusion | Explicit branch origins and destinations, shared inputs, residual/conditioning paths and a visible merge operation. |

For a concrete reference, inspect [Graph Attention Networks, Figure 1 (PDF page 4)](https://arxiv.org/pdf/1710.10903#page=4) and the [authors' explanation](https://petar-v.com/GAT/). Its feature symbols, attention computation, neighborhood links and parallel heads carry scientific meaning. Use this as an expression reference for a comparable task; do not transfer standard GAT internals, head counts, adjacency or fusion into an unseen user implementation without source support.

These are examples, not a fixed palette. Domain words such as “satellite” or “fault diagnosis” identify the application; they do not select boxes, scene artwork or a scientific operator. When using FigurePlan, `node.kind` selects only its supported structural glyph. Use `process` for a genuine workflow step or a named module whose internals are unavailable; a reconstruction marks it `opaque: true` and explains the evidence boundary. Do not guess missing adjacency, attention, fusion or physical internals from a familiar method name.

Set layout after identifying these relationships. Coordinates use inches; `medium: "figure"` can use the figure's own aspect ratio. In a redraw, preserve source panel order and relationships. In a reconstruction, use compact, well-related panels to expose the mechanism without shrinking symbols below readable size. Existing [ML components](ML_COMPONENT_PRESETS.md) and custom FigureSpec/vector geometry remain available outside the first compiler vocabulary.

## 3. Author the brief

Use this optional brief for supported structural parts or a route handoff; it is not a universal paper-figure schema. The executable schema is enforced by [`tools/scientific_figure_plan.py`](../tools/scientific_figure_plan.py). Supply these fields when using that compiler:

| Field | Required form |
| --- | --- |
| Top level | `schema_version: "1.0"`, nonempty `id`, `title`, `claim`, one `intent` above, `medium: "figure"` or `"slide"`. The figure `id` is a portable filename using letters, digits, `_`, `.` or `-`, starting with a letter/digit. |
| `canvas` | Positive finite `width_in` and `height_in`; native PPTX output supports 1–56 inches per dimension. |
| `evidence` | Nonempty array of `{id, path, sha256, locator, kind}`. IDs are unique; `sha256` is the actual 64-character lowercase file digest. `kind` is `paper`, `code`, `reference_image`, `user_brief`, `synthetic` or `data`. Relative paths resolve under `--source-root`, which defaults to the brief's directory. |
| `nodes` | Array of `{id, kind, label, evidence: [IDs], params: {}, box: [x,y,w,h]}`. Native routes require nodes; node IDs are unique and boxes fit the canvas. The planner chooses `glyph`; any explicit override must agree with `kind`. |
| `edges` | Array of `{id, source, target, evidence: [IDs], kind}`. Unique IDs reference existing nodes; `kind` is `data`, `conditioning` or `residual`. Optional `source_port`/`target_port`: `left`, `right`, `top`, `bottom`, `input`, `output`. Optional `via: [[x,y], ...]` gives in-canvas waypoints. |
| `critical_edges` | Array of edge IDs derived from the source before drawing; nonempty for multi-node redraws/reconstructions. |
| `unknowns` | Array of nonempty descriptions; use `[]` when none are identified. Unknown attention adjacency/merge also generate explicit planner notes. |
| Redraw additions | At least one readable raster image/SVG with `kind: "reference_image"` and at least three distinct `source_anchors`. Render a PDF page/crop first. A text file cannot qualify by relabeling its evidence kind. |
| Optional layout | `panels: [{label,x,y,w,h}]` (optional `size`), `style: {font, font_size}`, and a visible `disclosure` string. These supplement the explicit node layout. |

Each node and edge needs a nonempty `evidence` list. Hashes identify the supplied bytes; the reader still checks that the cited locator supports the claim. If a source changes, read it again before updating the digest.

| Node `kind` | Glyph and `params` contract |
| --- | --- |
| `tensor` | `tensor_planes`; required `shape`: nonempty array of positive integers or nonempty symbolic strings. |
| `time_series`, `conv1d`, `embedding` | `signal_traces`, `temporal_kernel`, `indexed_vectors`; provide only evidenced parameters. Any supplied `shape` follows the dimension rule above. |
| `graph_attention` | `attention_heads`; required positive integer `heads`; `merge`: `concat`, `mean` or `unknown`; `adjacency`: `known` or `unknown` (both default to `unknown`). Known adjacency needs nonempty `graph_nodes` and `graph_edges` as pairs of zero-based node indices; unknown adjacency leaves both absent. |
| `pool` | `group_reduction`; positive integer `groups` and `reduction: "mean"`. If the first output `shape` dimension is numeric, it equals `groups`. |
| `add`, `concat`, `projection` | `sum_junction`, `segmented_concat`, `projection_map`. Compilation requires at least two non-conditioning input edges for `add`/`concat`; addition operands enter distinct geometric ports. Any supplied `concat.params.inputs` must equal the actual count. |
| `head` | `task_output`; positive integer `outputs` and nonempty `activation`, using `"unknown"` if unprovided. |
| `gate` | `decision_boundary`; nonempty string `threshold`, using `"unknown"` if unprovided. Conditioning enters a separate `top`/`bottom` boundary port, not the data input. |
| `process` | `process_box`; reconstruction requires `opaque: true` and a nonempty `explanation`. |

Unsupported structural kinds produce a planning error in this optional compiler. Use an explicit source-specific FigureSpec, existing components or custom vector geometry for the required mechanism; a compiler limit is not a reason to simplify away the science, switch to imagegen or introduce another schema. Changing a scientific operator into a generic process changes what the figure communicates.

## 4. Run a complete synthetic example

Run commands from the repository root. The ready-to-run public example is [`examples/semantic_figures/graph_attention.json`](../examples/semantic_figures/graph_attention.json):

```bash
python tools/build_scientific_figure.py examples/semantic_figures/graph_attention.json --output-dir dist/semantic_demo
```

To author a small brief yourself, create exact synthetic evidence bytes and print their digest:

```bash
python - <<'PY'
from pathlib import Path
import hashlib
source = Path("demo-output/semantic/evidence.txt")
source.parent.mkdir(parents=True, exist_ok=True)
source.write_bytes(b"Synthetic example: a two-head graph-attention module maps node features X [12,32] to Y [12,16]. Adjacency and head merging are unspecified.\n")
print(hashlib.sha256(source.read_bytes()).hexdigest())
PY
```

Save this complete JSON as `demo-output/semantic/brief.json`. Its digest matches the exact bytes above; replace both source and digest when using your own material.

```json
{
  "schema_version": "1.0", "id": "synthetic_gat",
  "title": "Two-head graph attention",
  "claim": "Node features pass through a two-head attention module.",
  "disclosure": "Synthetic structure; exact graph adjacency and head merging are unspecified.",
  "intent": "reconstruct", "medium": "figure",
  "canvas": {"width_in": 10, "height_in": 4.5},
  "evidence": [{"id": "s1", "path": "evidence.txt",
    "sha256": "d54374f233674fbf11908705462d7b885f57d68179d249a03f42579c8b105420",
    "locator": "line 1", "kind": "synthetic"}],
  "nodes": [
    {"id": "x", "kind": "tensor", "label": "Input X", "evidence": ["s1"],
     "params": {"shape": [12, 32]}, "box": [0.5, 1.1, 2, 2]},
    {"id": "attn", "kind": "graph_attention", "label": "Graph attention", "evidence": ["s1"],
     "params": {"heads": 2, "merge": "unknown", "adjacency": "unknown"}, "box": [3.4, 0.9, 3.1, 2.5]},
    {"id": "y", "kind": "tensor", "label": "Output Y", "evidence": ["s1"],
     "params": {"shape": [12, 16]}, "box": [7.5, 1.1, 2, 2]}
  ],
  "edges": [
    {"id": "e1", "source": "x", "target": "attn", "kind": "data", "evidence": ["s1"]},
    {"id": "e2", "source": "attn", "target": "y", "kind": "data", "evidence": ["s1"]}
  ],
  "critical_edges": ["e1", "e2"],
  "unknowns": ["Exact graph adjacency and head merging are unspecified."]
}
```

Compile the native figure, or inspect only its plan:

```bash
python tools/build_scientific_figure.py demo-output/semantic/brief.json --source-root demo-output/semantic --output-dir demo-output/semantic/rendered
python tools/scientific_figure_plan.py demo-output/semantic/brief.json --source-root demo-output/semantic --out demo-output/semantic/plan.json
```

The planner checks file bytes and references, then adds `route`, node `glyph`/`requirements` and `review_status`. The main compiler writes `<id>.plan.json`, `<id>.figure.json`, `<id>.svg`, `<id>.pptx` and `<id>.review.json` for native routes. The review JSON contains automatic check results while scientific and visual review remain pending. These synthetic dimensions illustrate the interface; they are not results from a paper or experiment.

## 5. Review the actual output

Open the actual rendered figure and any source/image layers; render a PPTX with the available host. Inspect the final PDF/PNG at the intended paper or presentation dimensions. Check readable font sizes and symbols, consistent notation and line types/weights, clear arrow semantics, compact multiple panels and adequate separation of related marks. Compare the image with the original source and inspected scholarly references. A prompt, tool route, passing CI, shape count or zero-image statistic does not establish paper-figure quality.

Follow each source-derived critical relation; check variables, dimensions, operations, neighborhoods/propagation, hierarchy, every repeated head, branches and fusion against the source. Distinguish sum from concatenation, check unknown-detail disclosures, and verify labels, clipping and arrow placement. A reader should be able to identify the actual mechanism from the marks. If the result remains a generic box pipeline, revise the graphical encoding rather than adding colors, dots, decorative objects or a default generated scene. Record the renderer actually used. A LibreOffice preview is evidence about LibreOffice output; it does not establish a Windows PowerPoint review.

Scientific and visual review begin as `pending`. Automated geometry/mechanism checks are bounded checks on the authored plan and marks; an omitted source relation can remain invisible to them. Review the source independently alongside the final image. Rectangles remain appropriate for opaque modules and genuine process steps.

The preflight checks actual per-head neighborhood arrows, provided dimensions,
visible critical routes and connector/text intersections. It stages all outputs
before publishing them, so an exporter failure preserves the last successful set.
Large groups and class outputs use visibly disclosed representative marks and
ellipsis while retaining the exact counts. Known-neighborhood glyphs support up
to six vertices; larger source graphs need a source-specific layout.

PPTX shapes and text in the compiled structural layer are independent editable objects. Connections use fixed coordinates and do not follow a node dragged in PowerPoint. Change boxes or waypoints in the brief, then compile again and inspect the result. State which illustration/source-image layers are raster; do not describe the whole composite as fully editable.

Use actual sourced photographs, microscopy and necessary source-artwork excerpts as image layers with hashes, rights and any crop/processing history. Check any apparatus schematic or cutaway against documented geometry; leave unavailable internals unknown. Record any selected generated artwork as illustrative, with its generation provenance and raster status. Keep exact topology, values, axes and scientific annotations in the native/vector or data path; source-artwork annotations that remain inside a crop are raster and must be described accordingly. Deliver the complete scientific figure with all required precise content; a decorative asset or concept image alone does not complete a paper method or results figure.

Publish synthetic examples and their synthetic evidence. Keep user screenshots and undisclosed research in the authorized local task. `7.7.0-dev` identifies this bounded executable path; it does not establish automatic source understanding, a frozen benchmark win rate, stable release status, or completed independent scientific/Office-host review.
