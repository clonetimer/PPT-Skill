# Scientific visual planning, first implementation

## Goal and observed failure

Make paper/code-grounded method figures communicate their scientific objects and
mechanisms before choosing decoration. The user's observed failure is a plausible
flowchart made of pale boxes. Main already has rich primitives, but no runnable
semantic-to-glyph entry point. The installed personal skill is an older V3 fixed
figure library. A working renderer alone does not resolve either entry problem.

## Scope and decisions

Build an additive path on main, independent of the unmerged PDF-import and V8
branches. Preserve the existing renderer and scientific checks. Add a small
evidence-linked FigurePlan, deterministic glyph selection, native compilation,
and mutation checks for visual-semantic omissions. An agent still reads the
paper/code and authors the plan; this is not an automatic source-code parser.

Separate source-visible redraw, paper/code reconstruction, conceptual artwork,
quantitative charts and workflow diagrams. Domain words such as satellite or
fault diagnosis must not override an explicit graph-attention or tensor kind.
Source redraw follows source layout; reconstruction follows evidenced semantics.
Exact topology uses vector/native output. Conceptual artwork can use imagegen.

Review ruling: source redraw routes to the existing source-specific FigureSpec
authoring path, not this semantic preset compiler. A fixed glyph substitution
cannot establish fidelity to arbitrary source artwork. Verify actual image/SVG
bytes and distinct anchors; no automatic image-similarity claim is made.

The first compiled vocabulary is tensor, time_series, conv1d, embedding, add,
graph_attention, pool, concat, projection, head, gate and process. Unsupported
kinds fail with an actionable message rather than becoming a generic rectangle.
Plain process boxes remain appropriate for workflow steps and opaque components
whose internal workings are not provided.

Evidence records contain local path, SHA-256, precise locator and kind. Nodes and
edges cite evidence IDs. A reference-image record supports only visible labels
and relations. Unknown attention adjacency, head merge rules, dimensions and
weights remain unknown. Schematic patterns carry visible disclosure; drawn
matrices/traces never pretend to be empirical data.

## Alternatives considered

1. Prompt-only tightening is cheap but does not connect semantic objects to
   rendering or detect a plausible-looking box-only regression.
2. Pure image generation can explore appearance but cannot establish exact
   topology, text or native editability.
3. A semantic plan compiled through the current SVG/PPTX engine is selected.
   It provides testable correspondence while preserving design freedom through
   explicit layout and optional waypoints. It costs a small bounded vocabulary.

These are implementation decisions under the user's instruction to research and
begin execution, not additional user-approved product requirements.

## Technical basis

- GAT author explanation: https://petar-v.com/GAT/ (neighborhoods and heads).
- PlotNeuralNet author code: https://github.com/HarisIqbal88/PlotNeuralNet/blob/master/pycore/tikzeng.py
  (operator-specific geometry; consulted, not copied).
- ONNX: https://onnx.ai/onnx/repo-docs/ShapeInference.html (unknown dimensions).
- Graphviz: https://graphviz.org/docs/layouts/dot/ (layout solves placement, not
  scientific meaning). Graphviz is not a new runtime dependency in this slice.

## Interfaces

FigurePlan input has schema_version='1.0', id, title, claim, intent
('reconstruct'|'redraw'|'conceptual'|'quantitative'|'workflow'), medium
('figure'|'slide'), canvas={width_in,height_in}, evidence[], nodes[], edges[],
critical_edges[] (edge IDs), unknowns[], optional panels[] and style{}.

Evidence: {id,path,sha256,locator,kind}; kinds are paper, code, reference_image,
user_brief, synthetic. Nodes: {id,kind,label,evidence:[IDs],params:{},
box:[x,y,w,h]}. Optional node glyph override must match its kind. Edges:
{id,source,target,evidence:[IDs],kind:'data'|'conditioning'|'residual',
source_port?,target_port?,via?:[[x,y],...]}. Panels are {label,x,y,w,h}.

Parameter vocabulary: shape (positive ints or nonempty symbolic strings),
heads (positive int), merge ('concat'|'mean'|'unknown'), adjacency ('known' or
'unknown'), graph_nodes and graph_edges only for known adjacency; pool uses
groups and reduction ('mean'); head uses outputs and activation; process uses
opaque=true and explanation when used in a reconstruction.

plan_figure(brief:dict, source_root:Path)->dict validates the evidence hashes and
references, selects route={renderer,profile,reason}, attaches node glyphs and
requirements, and preserves input. It does not infer hidden layers or weights.

draw_node(node:dict)->dict returns elements (existing FigureSpec primitive
format), ports (left/right/top/bottom plus input/output aliases), and box.
Every mark has semantic_owner and visual_role; repeated heads have head_index.
Node labels/parameters remain exact. Unknowns are disclosed, not fabricated.

compile_figure(plan:dict)->dict joins primitives and visible connectors into the
existing renderer format, with semantic_edges and plan provenance. A separate
audit_figure(plan:dict,spec:dict)->dict checks geometry and mechanism coverage.
It cannot certify scientific truth or aesthetic quality from metadata alone.

## Acceptance and boundaries

Run existing tests unchanged. Test route selection, evidence corruption,
unsupported kinds, mismatched semantics, omission of a head, and deletion of an
actual required connector. Render SVG and native PPTX from the same spec; inspect
LibreOffice PDF/PNG outputs, not only serialized metadata. Use fresh-agent usage
and independent visual/code review. Do not call these human domain review or
PowerPoint 2016 validation.

The supplied screenshots are local regression inputs. Public examples use
synthetic descriptions; do not upload user screenshots or undisclosed research
details into the public repository. Update the installed skill with a focused,
verified scientific path while retaining its defense-deck resources.

Do not claim a stable V8 release, a frozen held-out win rate, automatic parsing
of arbitrary programs, journal acceptance, or completion of Office-host review.
