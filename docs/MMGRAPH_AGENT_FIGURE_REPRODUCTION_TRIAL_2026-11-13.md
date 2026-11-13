# MMGraph-Agent: three-source-figure editable reconstruction trial

Date: 2026-11-13. Branch: \`feat/mmgraph-agent-figure-fidelity-20261113\`.

## Source and rights boundary

- Publication: [MMGraph-Agent (arXiv:2611.10657)](https://arxiv.org/abs/2611.10657).
- Author project: [LHRLAB/MMGraph-Agent](https://github.com/LHRLAB/MMGraph-Agent).
- Author TeX source contains \`F1.pdf\`, \`F2.pdf\`, and \`F3.pdf\`. Source SHA-256 values appear in each local audit record; no original PDF, extracted images or derivative figure slides are committed to this public repository.
- The conversion mechanism and synthetic tests are reusable; permission to redistribute this particular author's figures has not been established.

## Measured outcomes

| Figure | Original PDF paths | Native PPTX vector objects | Editable text objects | Independent pictures | Source/PPTX SSIM | Assessment |
|---|---:|---:|---:|---:|---:|---|
| F1, challenges vs proposals | 216 | 215 | 94 | 17 | 0.765 | Structure PASS; strongly source-matched overall |
| F2, composite performance | 3,563 | 2,755 | 100 | 46 | 0.801† | Structure PASS; outer radar rings repaired; fine curve paths still need review |
| F3, construction/cache/policy | 318 | 317 | 116 | 0 | 0.840† | Structure PASS; mathematical labels corrected from source text |

† F2 and F3 scores are from the pre-repair exports. The post-repair PPTX files have not yet been remeasured against the original source PDFs; these values must not be presented as final scores for the repaired files.

All three PPTX files contain **zero full-figure pictures**; each source picture is an independent object. F2 includes native replacement bars and hatch marks measured against the author's figure, because the original PDF's clipping/pattern graphics rendered incorrectly in a generic import. The PDF encoded several local stroke widths too heavily for the PowerPoint equivalent; tuning 233 upper-panel strokes against the source preview improved F2 SSIM from 0.720 to 0.801. Its source-specific recovery scripts and resulting derivative figures remain in private delivery artifacts, not in this repository.

SSIM was computed on source PDF and LibreOffice-PDF-exported PPTX PNGs at matched page/crop dimensions: F1 90 dpi, F2 140 dpi, F3 72 dpi. It compares pixel appearance in that rendering environment; it neither proves every relation is correct nor predicts Office 2016 behavior. The audit checks text and shape preservation independently of this metric.

## Post-import correction pass (2026-11-13)

### F2: radar outer rings

The first imported PPTX render showed gaps in the two black outer radar-chart rings. The repair replaced those two malformed custom freeforms with native PowerPoint oval outlines, preserving their source bounding boxes, 0.8 pt stroke width, and original z-order. The radar data series, grid, numeric labels, dataset thumbnails and legend were not redrawn or flattened. The two ovals remain independently editable.

The ring defect is corrected in the private delivery candidate. Fine-grained differences in dense radar-series paths and small labels remain subject to source-PDF comparison; no final pixel-fidelity claim is made.

### F3: mathematical glyph recovery

PDF font encoding produced incorrect Unicode mappings for some mathematical glyphs. Using the paper's source text in §3.1–§3.3 and the supplied figure image, 51 malformed text fragments were grouped into 19 corrected, editable math labels. The final F3 file has 116 text objects and zero picture objects.

Corrected labels include:

- \`ψ(d)\` — rule-based document parser, §3.1 / Eq. (2).
- \`𝓜₁ᵗ\` and \`𝓜₂\` — L1 trajectory cache and L2 hypergraph store, §3.2.
- \`sₜ = (q, v_q, 𝓜₁ᵗ⁻¹, hₜ)\` — agent state, §3.2.
- \`C = 5\`, approximately 300-word digest, and \`L_cap = 5,000 tokens\` — bounded-context settings, §3.2 / Eq. (5).
- \`S(W)\`, \`π_θ\`, and \`η(N) = 1 − 2/(N + 2)\` — web-search interface, retrieval policy and call-count regulator, §3.3 / Eq. (6).
- \`ℛ_on = ∅\` — online retrieval disabled during offline training, §3.3.
- \`𝒜_txt\`, \`𝒜_img\`, and \`𝒜_ans\` — unified action channels, §3.3 / Eq. (6).

The corrections are recorded in the private delivery package's \`F3_MATH_REPAIR_MAP.json\`. They are editable text, not flattened equation images.

## Failures observed and regression protection

1. PDF compound fill paths were initially split, filling icon holes black. One PowerPoint compound freeform with multiple contours fixed this, covered by an in-memory test.
2. Using \`Inches(.0001)\` as a freeform scale quantized 91.44 EMU to 91 EMU, creating a proportional 0.48% shape offset; a floating-point scale fixed the alignment. F1 SSIM improved from 0.422 to about 0.765 and F3 from 0.553 to 0.840.
3. PDF charts used nested clipping paths. Ignoring clips made radar and bar graphics spill across other panels. The importer now preserves the axis-aligned source scissor envelope; truly nonrectangular clips still need exact polygon clipping.
4. Inserting all source photos before all vectors hid F2 benchmark thumbnails. The importer now respects source image paint order from the PDF bounding-box log.
5. A source PDF encoded 14 stroke widths as 9,525 pt; those were skipped with explicit warnings because clamping or accepting them could blot out neighboring content.
6. Original chart hatch/pattern fills did not survive generic clipping. F2 delivery used directly measured native bar/hatch reconstruction and source-aligned thin-stroke tuning. A generalized pattern/stroke-profile converter remains a separate project.
7. Two radar outer-ring freeforms did not render as closed circles in the first PPTX export. The post-import repair replaces only those two paths with native editable ovals; this regression is covered by the private artifact audit.

## Current acceptance boundary

The three candidate files are editable reconstructions, **not a claim of pixel-perfect or Office 2016-verified reproduction**. F2's outer rings are fixed, while some dense radar-series paths and tiny labels still need final source-PDF comparison. F3's mathematical labels are source-grounded and corrected, but its post-repair SSIM has not been recomputed. Manual scientific and final-size inspection remains required before publication use.

The private delivery bundle contains the three PPTX files, PDF/PNG previews, the merged three-page review PDF, a structural audit, and the F3 formula correction map. The original figure files and derivative slides are intentionally not committed to this public repository.

## Reproduction

Use \`tools/pdf_figure_import.py\` to generate native slides from licensed vector PDFs, followed by \`tools/audit_imported_pdf_figure.py\` and visual export/comparison. Run \`tools/test_pdf_figure_import.py\` and \`tools/test_audit_imported_pdf_figure.py\`. The generic pipeline intentionally does not include or distribute the MMGraph-Agent figure files or their media.
