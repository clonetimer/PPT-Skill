# GR01 GraphRAG flowchart source record

Checked on 2026-11-07 against Microsoft GraphRAG documentation:

- [Edge et al., *From Local to Global*, Figure 1 and Section 3.1](https://arxiv.org/pdf/2404.16130): the global method's central relationship is text → entity/relationship graph → hierarchical communities → community summaries → parallel community answers → final global answer. The original figure and paper, rather than the software overview alone, ground `GR02_graphrag_method`.
- [Default indexing dataflow](https://microsoft.github.io/graphrag/index/default_dataflow/): documents become text units; entities and relationships are extracted and summarized; graph communities and reports are produced; text units, entity descriptions, and community reports can be embedded. Claim extraction is method/config dependent and is omitted from this overview.
- [Indexing overview](https://microsoft.github.io/graphrag/index/overview/): structured outputs are stored as tables, with embeddings in a configured vector store.
- [Global search](https://microsoft.github.io/graphrag/query/global_search/): uses community reports as context with map and reduce stages.
- [Local search example](https://microsoft.github.io/graphrag/examples_notebooks/local_search/): combines graph data and source text units; entity description embeddings support matching the query to relevant entities.

The slide is a **documentation-grounded conceptual reconstruction of Microsoft GraphRAG's standard workflow**, not a pixel redraw of one official diagram or an exact execution trace. It presents global and local query modes as alternatives. It does not claim every deployment stores all optional outputs or runs every optional indexing workflow. The labeled arrows are the scientific relations checked for this example.

`GR02_graphrag_method` is a **paper-grounded reconstruction of the global-answer method**. It uses illustrative nodes and community clusters, not research data or a copied publisher artwork. It deliberately excludes local search from the main path. Its independently written `GR02_expected_topology.json` requires the cross-stage community-report handoff that the first trial omitted.
