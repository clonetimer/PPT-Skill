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
