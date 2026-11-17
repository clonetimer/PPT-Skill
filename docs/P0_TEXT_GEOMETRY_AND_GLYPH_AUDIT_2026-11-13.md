# P0-03 — Source-aware text geometry, font mapping and glyph audit (2026-11-13)

## Root cause established

The previous PDF importer created each text box from the source's axis-aligned glyph bounding box, then applied the source rotation to that already-rotated box. It also expanded width by **0.55 × font size** and height by **1.35 × font size**. This double-counted rotation and inflated adjacent spans into PowerPoint collisions.

The frozen direct-import baseline exposed up to **55 apparent text intersections** in UCFNet, 21 in SkillSmith and 27 in PoG. EvoOntology's 16 out-of-bounds labels were primarily text already outside the selected source crop; the importer did not distinguish inherited crop clipping from newly introduced overflow.

## Implemented changes

1. **Oriented source geometry:** \`_span_local_geometry()\` uses \`fitz.recover_quad(line["dir"], span)\` to recover the glyph-oriented quad. PowerPoint width/height now come from the quad's local axes, are centered on the original glyph quad and receive only 1% font-size padding. This prevents rotating the source AABB a second time.
2. **Known font aliases:** Calisto MT, TeX Gyre Termes, Linux Libertine, STIX/Computer Modern math families and anonymous \`Unnamed-T3\` resources map to deterministic Office font families. The audit records the source→target family mapping and detects candidate run-family mismatches.
3. **Read-only source-aware audit:** \`tools/audit_text_geometry.py\` matches source PDF text spans to candidate PowerPoint text objects in source order, then reports source overlaps, candidate overlaps, *introduced* overlaps, source-inherited clipping, new out-of-bounds boxes, text corruption, font mismatches, mathematical Unicode and suspicious control/private-use/unassigned characters. It does not access mutating shape style getters.
4. **Release-gate integration:** \`figure_first_pass_gate.evaluate()\` includes the audit. New introduced overlap, new out-of-bounds text, text corruption or candidate font mismatch adds \`TEXT_GEOMETRY_FAILURE\` and returns \`FAIL\`. Suspicious source glyphs without a deterministic rendering can be held for review; scientific review remains independent.

## Real-source crop checks

The following figures were re-imported from the same private, user-supplied source crop PDFs used by the ten-paper direct-import study. Source PDF bytes and figure derivatives are intentionally not committed to this public repository.

| Figure crop | Source spans / PPT text objects | Legacy PPTX overlap count before → after | Source overlaps | Introduced overlaps | Source / candidate OOB | Text mismatch | Audit |
|---|---:|---:|---:|---:|---:|---:|---|
| EvoOntology | 285 / 285 | 3 → 0 | 1 | 0 | 16 / 16 (all inherited) | 1 unmapped U+0000 | **FAIL** |
| Paths-over-Graph | 86 / 86 | 27 → 1 | 1 | 0 | 3 / 3 (all inherited) | 0 | PASS |
| SkillSmith | 114 / 114 | 21 → 4 | 4 | 0 | 0 / 0 | 0 | PASS |
| UCFNet | 93 / 93 | 55 → 0 | 0 | 0 | 0 / 0 | 0 | PASS |

The remaining 1 PoG and 4 SkillSmith overlaps are present in the source figure and are therefore not counted as new importer defects. The 16 EvoOntology and 3 PoG out-of-bounds source spans are already clipped by the source crop; the new importer does not add further overflow.

### EvoOntology unmapped glyph — intentionally not guessed

The source PDF's Calisto font span at source index 16 contains U+0000 between \`Revenue\` and \`Operating Cost\`. Its original PDF rendering shows a small hollow-square glyph, while PowerPoint XML escapes U+0000 as the literal token \`_x0000_\`. The audit correctly returns **FAIL** rather than silently deleting it or guessing an operator. The visual source crop must be reconciled before this figure can be accepted.

### Mathematical text

- Synthetic round-trip test: \`θₜ → β²\` survives PDF extraction and remains selectable PowerPoint text with identical Unicode code points.
- UCFNet crop: 9 Greek/subscript/superscript/operator glyph occurrences detected, zero text mismatches.
- No suspicious Unicode in PoG, SkillSmith or UCFNet.

### Render review

After geometry correction, source-PDF vs LibreOffice-PDF SSIM screening on the same crop pages:

| Figure | SSIM |
|---|---:|
| EvoOntology | 0.8126 |
| Paths-over-Graph | 0.8417 |
| SkillSmith | 0.8237 |
| UCFNet | 0.7769 |

These values are renderer-specific triage metrics, not scientific correctness scores or Office 2016 host certification. Review contact sheet and per-figure source/candidate/difference images in the private QA bundle.

## Tests and CI

- \`tools/test_text_geometry_import.py\`: **4/4** — adjacent text, rotated quad, font aliases, exact math glyph round trip.
- \`tools/test_text_geometry_audit.py\`: **7/7** — source-intentional overlap, candidate-only overlap, text corruption, introduced overflow, inherited source crop overflow, math codepoints/font map, unmapped control glyph.
- Crop/XRef recovery: 5/5; dense-PDF budget: 5/5; existing importer and audit suites remain green.
- [GitHub Actions #147 — PASS](https://github.com/clonetimer/PPT-Skill/actions/runs/43463658973). This is Linux/LibreOffice and OOXML evidence; it is not an actual Windows PowerPoint 2016 runtime test.

## Remaining boundary

- The EvoOntology U+0000 glyph needs explicit source-grounded treatment. It remains blocked; do not substitute a mathematical operator based only on appearance.
- Source-inherited text clipped by the crop is reported separately; no new clipping is introduced. A publication-ready re-layout would need an explicitly authorized layout change.
- Real Office 2016 open/save/re-export and final-size visual review remain outstanding.
- The original ten-paper cohort is now a development regression set, not a new blind hold-out. Strict first-pass success on the frozen ten-paper FigureSpec cohort remains 0/10; this P0-03 repair must not be retroactively counted as a first-pass pass.


## Extension — PDF text calibration across independent text frames (2026-11-17)

### Failure pattern found in the independent-paper AST pilot

The Mamba and Swin generalization figures retained exact SVG/DrawingML raster parity, but the first text-calibration attempts failed for reasons that were not all actual layout defects:

- PDF text extraction groups characters into spans, lines and blocks according to renderer decisions. A PDF block is not equivalent to one PowerPoint text frame; adjacent independent text boxes may be merged into one block.
- A single source text frame may be emitted as multiple PDF spans or font runs when a fallback face renders a missing glyph (for example, mathematical subscripts and floor/ceiling symbols).
- A narrow PDF whitespace character can overlap the bounding box of a neighboring glyph. Removing whitespace on any intersection can turn a valid label such as `A patch` into `Apatch`.
- Explicit line breaks in one PowerPoint text frame may be represented by separate PDF baselines rather than a literal newline character in one text span.
- Font-wide PDF span bounds are not a reliable ink bound for mixed math fonts. Glyph-outline bounds, positioned by the PDF character baseline and the selected glyph face, are a better measurement basis.

### Corrective implementation

1. Keep a page-wide, character-position-preserving stream across PDF blocks and fallback-font runs. Do not assume a PDF block maps one-to-one to a PowerPoint text shape.
2. Preserve whitespace unless its box is fully contained by a same-baseline visible glyph. Do not discard it merely because bounding boxes intersect.
3. Match source text exactly first. If the PDF stream has dropped a whitespace glyph, retry with a whitespace-insensitive key and enforce alphanumeric token boundaries so a label cannot match only the prefix of a longer word.
4. Match explicit source newlines line-by-line against distinct PDF baselines; retain the selected glyph records for the final geometry calculation.
5. Resolve fallback faces per code point and measure the selected glyph outline. Retain the requested/resolved face and fallback decision in the audit record.
6. Compare reconstructed ink bounds with the original PPTX text-frame geometry. Keep the fast fontTools estimate as a separate diagnostic; do not treat a line-count disagreement alone as proof of overflow.
7. Emit the exact unmatched/overflowing text strings in the CI summary. Preserve the full generalization output directory as a failure artifact so the next diagnosis can inspect PDF, PPTX, render records and per-shape audit together.

### Regression fixtures required

- Adjacent independent text boxes on one PDF line.
- A multi-line label with an explicit source newline.
- A single label with a fallback-font subscript.
- A label containing floor/ceiling symbols.
- A narrow inter-word space that the PDF extractor may omit.
- A negative fixture proving whitespace-insensitive matching does not match `A patch` inside `A patches`.

### Acceptance boundary

A missing text match is not automatically classified as a source-layout defect until the character stream and rendered page are inspected. The fallback matcher may recover whitespace lost by PDF extraction, but it must not suppress true missing text or partial-word matches. Any actual ink outside the source text frame remains a hard calibration failure. LibreOffice results remain separate from Microsoft PowerPoint 2016 host certification.


### Additional regression lesson from the same-line boundary test

A compact-text fallback must distinguish two cases using the candidate frame and glyph positions, not only string adjacency:

- A preceding/following character from a separate PDF text object on the same baseline must not block a match when it is outside the candidate PowerPoint text frame.
- An alphanumeric continuation inside the candidate frame must still block a prefix-only match (for example, matching `A patch` inside `A patches`).

A regression fixture that places the neighboring character inside or overlapping the candidate frame is not a valid independent-text-box fixture; by geometry it is indistinguishable from a continuation of the same text object. Keep these positive and negative fixtures separate.


### Binary-search ceiling lesson for pre-build fit estimates

The first integrated FigureSpec preflight exposed a second boundary condition: a fixed 72 pt maximum search height is not sufficient for a very narrow box containing a long label. The binary search then reports `max_height_overflows` and returns no suggested height, even though a larger box would fit.

Derive the upper search bound from the text length and the selected font's line height (a conservative one-glyph-per-line ceiling), while retaining a practical minimum and the existing authored-height multiplier. Keep the solver advisory: report the minimum fitting height and the additional height needed; do not silently resize the FigureSpec or shrink the font.


### Glyph-ink preflight calibration lesson

The first cross-paper preflight compared the full OS/2/hhea line box with the text-frame height. That was conservative enough to flag short Cambria Math labels (`xₜ`, `yₜ`) even though the pinned LibreOffice PDF showed their actual ink fully inside the frame.

For a single line, calculate vertical demand from the selected glyph outlines' ink extents. For multiple lines, combine the maximum line ink height with the measured inter-baseline distance; retain the full font line-height metric for baseline spacing, not as the single-line ink height. Keep the post-render glyph-boundary check as the authoritative calibration. On the Mamba/Swin pilot, this reduced both preflight estimated-overflow counts to zero while preserving 24/24 PDF text matches and zero rendered overflow.

Multiline regression fixtures must contain actual newline characters. A literal backslash followed by `n` is two printable characters and does not exercise paragraph/line-break handling.


### Structural-gap text lesson from C01 regression (2026-11-17)

The continuation ellipsis sits inside a fixed semantic gap between the visible B₃ and B_N graph rows. Increasing its text frame from 0.08 in to 0.14 in fixed the initial clipping but crossed the topology boundary; the geometry regression correctly rejected it.

For text marks inside a constrained structural gap:
1. Treat the surrounding object geometry as a hard layout constraint; do not enlarge the text frame beyond the gap to satisfy font metrics.
2. Resolve the actual fallback font and glyph ink bounds first. A fallback vertical-ellipsis glyph at 9.5 pt produced an approximately 11 pt ink box, larger than the available gap.
3. Reduce the glyph's authored font size to fit the available frame, or replace a typographic mark with editable native vector dots when that is the clearer source-matched representation.
4. Keep the frame within the measured gap with a small geometric tolerance, and preserve the independent topology test.
5. Run the strict LibreOffice glyph calibration after the topology test; both must pass. Do not weaken either gate to make the other pass.

The C01 correction keeps the marker inside the B₃/B_N gap (y=3.127 in, h=0.127 in) and reduces its font size to 6 pt, leaving explicit tolerance at both gap boundaries. The intended visual meaning remains a non-attached continuation marker, not a B₃-to-B_N edge.


### Source-first correction for constrained output annotations

The C01 render audit also exposed five tiny `C₁`–`C₅` labels added beside the five class-output squares. Inspection of the author-lab source image shows five unlabeled squares, with the classification caption placed separately. The individual class labels were not required by the topology contract and were not source-supported.

The correct repair was not to keep shrinking the invented labels until they fit. Remove unsupported annotations, preserve the five source-visible square marks and the classification caption, and encode the absence of per-square labels in the evidence contract and regression test. This improves source fidelity and removes unnecessary tiny text from the slide.


### Evidence-hash maintenance after source-record edits

A later C01 regression exposed a separate provenance failure: adding a source-grounded clarification to `docs/C01_V73_SOURCE.md` changed the bytes of the registered source record, but the FigureSpec's `EvidenceRecord.source_file_sha256` still contained the previous hash. The scientific IR validator correctly failed closed before running downstream geometry/render tests.

Whenever a referenced local evidence file changes:
1. Update the evidence file first.
2. Recompute SHA-256 from the exact committed file bytes (including line endings).
3. Update every FigureSpec EvidenceRecord that references that file.
4. Run the source-evidence validator before the full workflow.
Do not weaken the provenance check or reuse a stale hash. A source-grounded clarification is still a source change and must remain hash-bound.


### Minimum presentation type size is a hard constraint

After removing unsupported C₁–C₅ labels, the C01 V4.1 classification caption was temporarily reduced to 8.5 pt to fit a narrow frame. CI's output-profile validator correctly rejected it because the presentation profile requires at least 9.5 pt for that caption class.

The repair preserves the minimum type size and widens/repositions the text frame inside the existing panel, aligning its right edge with the output group. Do not solve a geometry problem by violating the profile's minimum readable type size. When a caption is too wide, first reclaim horizontal space, adjust alignment, or reflow the text; only change font size when the output profile explicitly permits it.

The same source-fidelity rule now applies to both C01 Image-first V4.1 and V8: keep the five output squares unlabeled and retain the separate classification caption. The V8 builder, committed FigureSpec, topology contract, regression test and Image-first content lock are kept in sync.
