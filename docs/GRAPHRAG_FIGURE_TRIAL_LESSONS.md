# GraphRAG figure trial: what changed in the skill workflow

The 2026-11-07 trial began with `dist/skill_tests/graphrag/GR01_graphrag_flow`: an editable 16:9 overview. It passed schema, declared-route and PowerPoint structure checks, yet its indexing and query paths were disconnected. It also compressed the paper's community hierarchy and parallel community answers into labels. This was a failure of source-to-figure selection, not a failed renderer or a reason to add decorative icons.

## Evidence and scope

- [Edge et al., *From Local to Global*, Figure 1 and Section 3.1](https://arxiv.org/pdf/2404.16130) identifies the global-answer mechanism: graph index, hierarchical communities, community summaries, community answers and final synthesis.
- [Microsoft GraphRAG indexing dataflow](https://microsoft.github.io/graphrag/index/default_dataflow/) distinguishes text units, extracted graph items, communities, reports and embeddings.
- [Microsoft GraphRAG global search](https://microsoft.github.io/graphrag/query/global_search/) expands the map and reduce stages. [Local search](https://microsoft.github.io/graphrag/query/local_search/) has a different retrieval path, so the revision treats it as a separate mode.
- [Nature figure guidance](https://research-figure-guide.nature.com/figures/building-and-exporting-figure-panels/) describes a particular journal's final-size, editability and panel rules. This 16:9 trial is a presentation-profile development figure, not a Nature submission.

## Specific lesson

`validate_drawn_routes(spec, set(spec["semantic_edges"]))` proves only that **declared** edges were drawn. If the author forgets a necessary edge in both the spec and the drawing, that check passes. Before layout, an independent source-derived topology fixture should list the claim-critical relations. The builder then checks its declared routes against the fixture and checks the visible routes geometrically. This still requires source interpretation; the fixture is not independent domain review.

## Revision and boundaries

`GR02_graphrag_method` focuses on the original paper's global method. It uses editable vector drawings for documents, text units, an entity relationship graph, nested communities, report batches and parallel answers. A required route connects indexing-time community reports to the query-time report batch. The negative mutation in `test_v2.py` removes that route from both the drawing and self-declared edges and must fail against `GR02_expected_topology.json`.

This remains a schematic. Node positions, community membership and report contents are illustrative; the figure does not depict actual extracted data, a full implementation trace or local search. The presentation profile and automated checks establish neither journal acceptance nor actual projection readability. Subsequent figures should choose the claim and target medium first, trace the source's scientific grammar, and preserve the original's important structures without blindly copying its styling.
