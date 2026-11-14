# P1-01 Reviewed source geometry to FigureSpec (2026-11-14)

## Evidence and review boundary

The ten-paper development set exposed a recurring visual-layout problem: a
FigureSpec may preserve coarse terminology while rearranging the original
paper's panel proportions. Raw PDF rectangles, repeated alignment groups and
raster whitespace are not themselves verified scientific panels.

The path is now: **source layout extraction → human review → compiled
geometric constraints → explicit FigureSpec bindings → PPTX render and audit**.

A human can accept a source enclosure as a panel, accept a region, reject or
defer a candidate, or split an enclosure into two **geometric regions**.
All approvals require reviewer name, rationale and source locator; assistant
visual triage cannot accept or reject. Source/SourceLayout SHA-256 hashes and
candidate snapshots must remain unchanged.

A split decision in a review template:

~~~json
{
  "decision": "split_region",
  "split_axis": "horizontal",
  "split_position_pt": 95.0,
  "rationale": "The source composition has two visible regions",
  "evidence_locator": "Figure 4, PDF page 3"
}
~~~

The split is allowed only on a source enclosure/nested enclosure and must
leave at least 2 PDF points or 5% of the parent dimension at each side.
Children are labeled geometric regions, **not** confirmed scientific
subfigures or graph edges. Invalid split, invalid approval or a stale review
invalidates the entire file; no partial approvals are released.

## Commands

~~~bash
python tools/extract_source_layout.py paper.pdf --page 3 \
  --region 50 70 550 350 --output qa/source_layout.json

python tools/source_layout_review.py template qa/source_layout.json \
  --output qa/review.json

# A human completes review.json with decisions and evidence locators.

python tools/source_layout_review.py validate qa/source_layout.json \
  qa/review.json --output qa/review_audit.json

python tools/source_layout_constraints.py qa/source_layout.json \
  qa/review.json --output qa/reviewed_constraints.json
~~~

An explicit mapping file must bind an accepted source constraint ID to a
FigureSpec bounding-box element ID. Its source_constraints_sha256 and
figure_spec_sha256 fields must hold the *actual* file SHA-256 hashes. Example
binding structure:

~~~json
{
  "schema_version": "1.0.0",
  "source_constraints_sha256": "replace with actual 64-character SHA-256",
  "figure_spec_sha256": "replace with actual 64-character SHA-256",
  "bindings": [{
    "source_constraint_id": "rect_candidate_01",
    "target_element_id": "panel-outline"
  }]
}
~~~

Apply without overwriting the original FigureSpec:

~~~bash
python tools/apply_reviewed_geometry.py \
  figure_specs/original.json qa/reviewed_constraints.json qa/bindings.json \
  --output qa/figure_reviewed_geometry.json
~~~

Alternatively pass the same review and bindings to the unified pipeline:

~~~bash
python tools/reproduce_research_figure.py paper.pdf \
  --mode figurespec --page 3 --region 50 70 550 350 \
  --figure-spec figure_specs/original.json \
  --source-layout-review qa/review.json \
  --source-layout-bindings qa/bindings.json \
  --output qa/figure_reproduction --render-host auto
~~~

The pipeline then records source_layout_constraints.json,
reviewed_figure_spec.json, source_geometry_application_audit.json and hashes
in its delivery manifest.

## Correctness boundary

Only the explicitly named bounding-box geometry is changed (x/y/w/h).
Unbound elements, scientific labels, dataset values and semantic edges are
kept unchanged in the FigureSpec. Unknown target IDs, duplicate mappings,
unreviewed constraints, changed SHA-256, unsupported shape types, attempted
in-place overwrite, and source/target aspect ratio drift above 2% are errors.

The output is still **geometric evidence**, never automatic scientific
acceptance. A reviewer.type=human field is an attestation in JSON, not an
independent authentication system. Science/topology verification, final-size
visual comparison, Office 2016 real-host checks and an independently frozen
unseen-paper benchmark remain separate. The original ten-paper first-pass
strict score stays 0/10 until a different holdout is evaluated.
