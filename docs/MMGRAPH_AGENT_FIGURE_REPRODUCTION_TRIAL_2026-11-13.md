# MMGraph-Agent: three-source-figure editable reconstruction trial

Date: 2026-11-13. Branch: `feat/mmgraph-agent-figure-fidelity-20261113`.

## Source and rights boundary

- Publication: [MMGraph-Agent (arXiv:2611.10657)](https://arxiv.org/abs/2611.10657).
- Author project: [LHRLAB/MMGraph-Agent](https://github.com/LHRLAB/MMGraph-Agent).
- Author TeX source contains `F1.pdf`, `F2.pdf`, and `F3.pdf`. Source SHA-256 values appear in each local audit record; no original PDF, extracted images or derivative figure slides are committed to this public repository.
- The conversion mechanism and synthetic tests are reusable; permission to redistribute this particular author's figures has not been established.

## Measured outcomes

| Figure | Original PDF paths | Native PPTX vectors | Editable text spans | Independent pictures | Source/PPTX SSIM | Assessment |
|---|---:|---:|---:|---:|---:|---|
| F1, challenges vs proposals | 216 | 215 | 94/94 | 17/17 | 0.765 | Structure PASS; strongly source-matched overall |
| F2, composite performance | 3,563 | 2,670 | 100/100 | 46/46 | 0.720 | Structure PASS; radar traces and several icons visibly differ |
| F3, construction/cache/policy | 318 | 317 | 148/148 | 0/0 | 0.840 | Structure PASS; mathematical glyph substitutions require review |

All three PPTX files contain **zero full-figure pictures**; each source picture is an independent object. F2 includes native replacement bars and hatch marks measured against the author's figure, because the original PDF's clipping/pattern graphics rendered incorrectly in a generic import. Its source-specific recovery script and resulting derivative figures remain in private delivery artifacts, not in this repository.

SSIM was computed on source PDF and LibreOffice-PDF-exported PPTX PNGs at matched page/crop dimensions: F1 90 dpi, F2 140 dpi, F3 72 dpi. It compares pixel appearance in that rendering environment; it neither proves every relation is correct nor predicts Office 2016 behavior. The audit checks text and shape preservation independently of this metric.

## Failures observed and regression protection

1. PDF compound fill paths were initially split, filling icon holes black. One PowerPoint compound freeform with multiple contours fixed this, covered by an in-memory test.
2. Using `Inches(.0001)` as a freeform scale quantized 91.44 EMU to 91 EMU, creating a proportional 0.48% shape offset; a floating-point scale fixed the alignment. F1 SSIM improved from 0.422 to about 0.765 and F3 from 0.553 to 0.840.
3. PDF charts used nested clipping paths. Ignoring clips made radar and bar graphics spill across other panels. The importer now preserves the axis-aligned source scissor envelope; truly nonrectangular clips still need exact polygon clipping.
4. Inserting all source photos before all vectors hid F2 benchmark thumbnails. The importer now respects source image paint order from the PDF bounding-box log.
5. A source PDF encoded 14 stroke widths as 9,525 pt; those were skipped with explicit warnings because clamping or accepting them could blot out neighboring content.
6. Original chart hatch/pattern fills did not survive generic clipping. F2 delivery used directly measured native bar/hatch reconstruction. A generalized pattern converter remains a separate project.

## Current acceptance boundary

The three candidate files are useful editable reconstructions, **not a claim of pixel-perfect or Office 2016-verified reproduction**. F2 still differs in the dense radar traces and upper-left icon treatment. F3 has small mathematical text-formula substitutions; MathML/native equation reconstruction was not attempted. For publication, manual scientific and final-size inspection is required before replacing the published originals.

## Reproduction

Use `tools/pdf_figure_import.py` to generate native slides from licensed vector PDFs, followed by `tools/audit_imported_pdf_figure.py` and visual export/comparison. Run `tools/test_pdf_figure_import.py` and `tools/test_audit_imported_pdf_figure.py`. The generic pipeline intentionally does not include or distribute the MMGraph-Agent figure files or their media.
