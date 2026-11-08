# Tree-KG Figure 2 source-composition study

Source: [Niu et al., ACL 2025, Figure 2](https://aclanthology.org/2025.acl-long.907.pdf), PDF page 3. The source figure was inspected at high resolution in `source_fig2_crop.png`. `TK02_treekg_source_composition` is a newly drawn derivative, not an embedded crop or pixel trace.

## Matched visual structure

- Original aspect ratio and unequal Initial Construction / Iterative Expansion panels.
- Left textbook and three extraction steps, pink summary nodes, vertical tree edges, then horizontal relations after relation extraction.
- Upper expansion field: numbered 1, 2 and 6; convolution before/after, horizontal-to-core/non-core edge transformation, two-graph structure merge.
- Lower field: stacked 3/4 labels, dashed threshold enclosure, central LLM cue, 5 edge-prediction label, candidate graph enclosures, score/strength annotations and output graphs.
- Source-like serif text, thin black paths, muted pastel node classes and pale tan transformation arrows.

## Asset and export boundary

The seven pictograms are transparent PNG fallbacks derived from publicly available SVGs: six Tabler robot icons (MIT) and one Lucide open-book icon (ISC, stroke recolored brown). Original SVGs, upstream license texts, source URLs and SHA-256 hashes are in `assets/`. The graph, arrows, labels and panel boundaries remain editable PowerPoint objects. No original-paper figure image is embedded.

The high-fidelity file has 316 PowerPoint objects, including the seven licensed icon pictures. `validate_high_fidelity.py` passed: 0 text-box overlaps, 0 line-through-text/ellipse occlusions, 0 out-of-bounds shapes, only allowlisted icon pictures, and PDF text extraction for the key method labels. The `audit_pptx.py --strict` raster-picture prohibition is intentionally inapplicable to these explicitly allowed icons; its other checks are independently enforced by the local validator.

## Remaining differences and use

The robot pictogram is an MIT-licensed substitute, not the exact author artwork. Some node positions, graph links, line weights and score arrows are schematic, and Figure 2's tiny labels remain small. This version is the high-fidelity **source-composition study**; `TK01` is the larger-label presentation explanation. Neither is a journal reproduction certification or an independently reviewed scientific figure.
