# Scientific Figure Planning (7.7.0-dev)

Choose the requested visual form, read the evidence, and assign each part to the appropriate drawing tool. **Evidence type and visual expression are independent choices.** FigurePlan compiles an explicit structural layer through the existing FigureSpec renderer; it is not the vocabulary for every scientific illustration. The agent or researcher authors its input; the planner validates references and selects glyphs. It does not parse arbitrary programs or establish scientific truth. Existing python-pptx rendering, native components and chart contracts remain available.

Contents: [Route](#1-select-the-route) · [Evidence](#2-read-evidence-and-choose-visual-objects) · [Schema](#3-author-the-brief) · [Example](#4-run-a-complete-synthetic-example) · [Review](#5-review-the-actual-output)

## 1. Select the route

### Choose the visual form first

Use the user's requested form and any inspected visual reference to select **structure diagram**, **object/scene illustration**, or **hybrid figure**. Separately record whether the scientific claims come from a visible source figure, paper/code, measured data, or a disclosed concept. A paper-grounded method can use a hybrid illustration; it does not become conceptual evidence merely because part of its appearance is generated.

| Visual form | What to produce |
| --- | --- |
| Structure diagram | Precise native/vector dependencies, operators, mathematical structure or genuine workflow steps; FigurePlan handles the supported structural kinds. |
| Object/scene illustration | An imagegen object, scene or material layer carrying the requested visual subject, plus deterministic scientific labels where needed. The artwork is illustrative, with no claim to measured geometry or results. |
| Hybrid figure | A coherent illustrated subject/scene and an independently checked structure/data layer. Place the exact marks in the illustrated composition so the whole figure explains the claim. |

If the user asks for **科研插画、图形摘要、对象感、不要方框图/流程图**, choose illustration or hybrid and **actually invoke an available imagegen tool** for its non-data, non-topological object/scene/material layer. Inspect the returned artwork before composing the figure. A planner handoff, a written prompt or more varied native glyphs does not fulfill that instruction. If imagegen is unavailable, state that the illustration layer could not be generated and identify what remains incomplete; do not silently return a box diagram as the requested figure.

For a hybrid, keep this division explicit in the ordinary figure brief; no new FigurePlan fields are required:

- **Illustration layer:** identify the subject, explanatory scene, materials, perspective and visual reference. Generate only those illustrative objects and surfaces. Ask for space for precise overlays when needed, and identify the resulting raster artwork as generated/illustrative.
- **Exact scientific layer:** derive real dependencies, node identities, equations, dimensions, quantitative marks, axes, numerical values and labels from the sources. Draw these with native/vector components or the data pipeline, and verify them after composition. Do not ask imagegen to draw an entire architecture that must be exact or produce fake measurement curves, microscopy, maps or heatmaps as evidence.
- **Complete composition:** make the illustrated objects and their arrangement explain the requested mechanism. A decorative satellite next to an unchanged box pipeline does not make a complete illustrated method figure. A concept-only visual trial must be labeled as such; it does not establish a verified method or a completed deck.

Prefer editable objects in the exact scientific layer. Permit disclosed raster illustration layers; neither “all objects editable” nor “zero pictures” is a default illustration acceptance criterion; honor an explicit all-native requirement. FigurePlan's 12 structural kinds do not restrict what imagegen can depict, and illustrative subjects must not be disguised as `process` nodes to satisfy that schema.

If the user explicitly requires every object to be native and editable, use imagegen only for a visual study, then reconstruct the subject with custom native shapes/freeform curves or licensed SVG geometry converted into editable objects. Check that the requested host exposes those objects for editing; embedding an SVG as a picture is insufficient. If this cannot be achieved, state the limitation. A general “prefer editable” request still permits clearly identified raster illustration layers.

### Use the existing routes for each layer or tool task

The following `intent` values describe the task handled by an existing tool route. They do not select the visual form of the whole figure. In a hybrid, use `reconstruct` for the exact method layer and imagegen separately for the illustrative layer, while retaining the original evidence types.

| `intent` | Evidence to read | Route and next action |
| --- | --- | --- |
| `redraw` | Actual reference figure and its caption | `source_spec / source_matched`: use the existing source-specific FigureSpec workflow; preserve inspected anchors and composition. |
| `reconstruct` | Paper method/equations and relevant code | `native / scientific_semantic`: compile the precise computation/structure layer with object-specific glyphs. |
| `conceptual` | The requested concept and applicable source material | `imagegen / conceptual`: the planner records a handoff; the agent must actually use imagegen for the disclosed illustrative layer. |
| `quantitative` | Raw data, units and analysis definitions | `existing_chart_pipeline / quantitative`: use the existing chart/data contract and its builder. |
| `workflow` | Real process or control steps | `native / engineering_flow`: functional rectangles and decision marks express the steps. |

The planner reports all five routes. The semantic compiler handles the structural content of `reconstruct` and `workflow`; it returns an explicit handoff for the other routes and does not invoke imagegen. For `redraw`, author a source-specific FigureSpec after inspecting the image, then use `python tools/render_figure_spec.py source.json --svg source.svg --pptx source.pptx` and the existing source-grammar checks. Preserve source-visible composition and marks; do not replace them with generated imagery or semantic presets merely because an operator has a familiar name. Imagegen and chart routes use their existing tools. The semantic compiler does not embed arbitrary image panels; compose illustration layers through the existing image/FigureSpec path.

## 2. Read evidence and choose visual objects

For a paper, identify the figure/panel, relevant formula and symbol definitions. For code, inspect the entry module and the methods implementing the claimed path; cite file lines or class/method names, configuration and known shapes. Compare training/inference and shared branches where they affect the claim. A reference image supports visible labels, objects and arrows; hidden adjacency, head fusion or weights need separate support. Record unresolved details explicitly.

For the structural layer, choose a tensor plane for tensor dimensions, separate indexed heads for graph attention, a reduction glyph for pooling, segmented output for concatenation, and a sum junction for addition. Domain words such as “satellite” or “fault diagnosis” describe the application; `node.kind` controls the structural glyph, not the complete figure's visual form. Use a `process` rectangle for a genuine workflow step or a named module whose internals are unavailable. A reconstruction marks that module `opaque: true` and explains the evidence boundary. Generate illustrative subjects through the illustration route rather than forcing them into this list.

Set layout after these choices. Coordinates use inches; `medium: "figure"` can use the figure's own aspect ratio. In a redraw, inspect the reference and preserve its panel order and relationships. In a structural reconstruction, arrange objects to make their computation legible. In an illustration or hybrid, organize the explanatory subject/scene and place the precise layer within that composition. Existing [ML components](ML_COMPONENT_PRESETS.md) remain available for richer source-specific work outside this first vocabulary.

## 3. Author the brief

Use this brief for the supported structural layer or a route handoff, not as an illustration schema. The executable schema is enforced by [`tools/scientific_figure_plan.py`](../tools/scientific_figure_plan.py). Supply these fields:

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

Unsupported structural kinds produce a planning error. Extend the relevant glyph and its checks for a new exact mechanism, or use the existing source-specific components with an explicit FigureSpec. Use imagegen for the separate illustrative object/scene/material layer; that layer need not fit this vocabulary. Changing a scientific operator into a generic process changes what the figure communicates.

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

Open the actual generated artwork and the composed figure; render any PPTX with the available host. Inspect the final exported image at the intended size for both scientific content and the requested visual form. For an illustration or hybrid, check whether the objects, scene, materials and arrangement actually deliver the requested style and explain the claim. A prompt, tool route, passing CI, shape count or zero-image statistic cannot demonstrate this. If the result still reads as the rejected box diagram, revise the actual composition and artwork before claiming the request is satisfied.

For the precise layer, follow each critical relation, inspect every attention head, distinguish sum from concatenation, check unknown-detail disclosures, and verify labels, clipping and arrow placement in the final composite. Record the renderer actually used. A LibreOffice preview is evidence about LibreOffice output; it does not establish a Windows PowerPoint review.

Scientific and visual review begin as `pending`. Automated geometry/mechanism checks are bounded checks on the authored plan and marks; an omitted source relation can remain invisible to them. Review the source independently alongside the final image. Rectangles remain appropriate for opaque modules and genuine process steps.

The preflight checks actual per-head neighborhood arrows, provided dimensions,
visible critical routes and connector/text intersections. It stages all outputs
before publishing them, so an exporter failure preserves the last successful set.
Large groups and class outputs use visibly disclosed representative marks and
ellipsis while retaining the exact counts. Known-neighborhood glyphs support up
to six vertices; larger source graphs need a source-specific layout.

PPTX shapes and text in the compiled structural layer are independent editable objects. Connections use fixed coordinates and do not follow a node dragged in PowerPoint. Change boxes or waypoints in the brief, then compile again and inspect the result. State which illustration/source-image layers are raster; do not describe the whole composite as fully editable.

Use sourced photographs, microscopy and necessary source-artwork excerpts as image layers with hashes, rights and any crop/processing history. Record generated object/scene/material artwork as illustrative, with its generation provenance and raster status. Keep exact topology, values, axes and scientific annotations in the deterministic/native or data path; source-artwork annotations that remain inside a crop are raster and must be described accordingly. For requested illustration or hybrid output, deliver the composed image with its precise overlays, rather than treating a standalone decorative asset as the completed scientific figure.

Publish synthetic examples and their synthetic evidence. Keep user screenshots and undisclosed research in the authorized local task. `7.7.0-dev` identifies this bounded executable path; it does not establish automatic source understanding, a frozen benchmark win rate, stable release status, or completed independent scientific/Office-host review.
