# GR02 GraphRAG method figure review

## Figure claim and scope

The figure explains how an entity/relationship graph and hierarchical community reports support **global** question answering. It is a presentation-profile, paper-grounded schematic. The small example graph and community clusters are illustrative; local search and optional claim extraction are outside this figure. Source links and evidence boundaries are recorded in `SOURCE.md`.

## Checks completed

- The FigureSpec passed the V7.6 JSON schema and evidence contract, including a hash of the source ledger.
- Nine source-derived required relations in `GR02_expected_topology.json` agree with the declared and visible routed arrows. One relation explicitly joins indexing-time community reports to the query-time report batch.
- `test_v2.py` passed both the baseline and negative mutation. Removing the cross-stage route from both the drawing and self-declared edges causes the independent-fixture check to fail.
- The generated slide passed strict PowerPoint object audit: 106 native objects, zero pictures, zero out-of-bounds objects, zero text-box intersections and no theme shadow. Minimum text size is 9.3 pt, in the presentation profile.
- Text and arrow contrast passed the project's preflight functions. Windows PowerPoint exported one-page PDF and 1600 × 900 PNG; the PNG was visually inspected.
- The repository's 15 canonical FigureSpecs passed `tools/validate_scientific_ir.py`; 16 existing scientific-IR mutation tests passed.

## Remaining limits

No independent domain reviewer or actual-distance projection check has been performed. The presentation-sized artifact has no named journal target, final print size or production review; it must not be called journal-ready. The topology fixture checks selected source-derived relations but cannot itself prove that every scientifically important relation has been selected.
