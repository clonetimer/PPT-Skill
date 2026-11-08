# Transformer source-matched redraw QA

Source: Vaswani et al., [*Attention Is All You Need*](https://arxiv.org/pdf/1706.03762), PDF pp. 3–4, Figures 1–2. The original PDF is kept locally as `source_attention_is_all_you_need.pdf`; the figures were inspected visually. `source_style.json` records seven observed visual anchors and the corresponding drawing decisions.

`TR03` is a bottom-up structural redraw of Figure 1; `TR04` is an operator-path redraw of Figure 2. Neither embeds the paper image. The original paper's visual grammar is preserved at the level of composition, operator-specific fill, residual and repetition paths, positional-sum symbols, independent Q/K/V paths, and the V bypass. Exact positions, dimensions, line curves and font metrics are not pixel-matched.

Checks: both FigureSpecs passed the V7.6 schema, source-PDF hash, scientific contract and independent topology fixture. The fixture contains 20 architecture and 16 attention relations. Negative mutations remove the encoder→cross-attention and V→final-MatMul routes and must fail. Strict PPTX audits found 130 and 86 native objects respectively, zero raster pictures, out-of-bounds objects, overlapping text boxes or inherited theme shadows. Text and arrow contrast preflight passed. Windows PowerPoint exported both to PDF and PNG, and the previews were visually inspected.

This is a development structural redraw, not a journal submission. An independent technical reader and actual final-size assessment remain outstanding. The comparison is with this paper's Figures 1–2; it is not a universal style template for other papers.
