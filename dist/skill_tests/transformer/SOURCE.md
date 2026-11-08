# Transformer source and scope

Primary source: [Vaswani et al., *Attention Is All You Need*, NeurIPS 2017](https://arxiv.org/pdf/1706.03762), checked 2026-11-07.

- Figure 1 and §3.1: original encoder–decoder topology, N=6 layers in each stack, encoder self-attention then FFN, decoder masked self-attention then encoder–decoder attention then FFN, residual connections followed by LayerNorm.
- §3.2 and Figure 2: scaled dot-product attention and parallel multi-head projections; Q/K/V source semantics; causal mask before softmax.
- §3.3–3.5: position-wise FFN, shared embedding/output weights, scale by sqrt(d_model), and sinusoidal positional encodings.
- Base-model dimensions: d_model=512, d_ff=2048, h=8, d_k=d_v=64.

These are paper-grounded **conceptual reconstructions**, not pixel copies. The two figure pages cover the original model's forward architecture and main sublayer mathematics. They omit optimizer, training schedule, beam search, modern pre-norm variants, KV caches and architecture variants. No illustrative token or attention pattern is presented as measured model output.
