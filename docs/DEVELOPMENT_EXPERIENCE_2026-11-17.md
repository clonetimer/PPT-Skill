# Development experience — Blind10 source admission and regression setup (2026-11-17)

## What happened

The original ten-paper cohort was recovered from the connected Library and checked against the frozen source manifest. All ten source hashes matched; all selected page/crop rectangles were in bounds; all caption anchors were present (10/10 for each gate).

The first PR added a reproducible audit utility and a report, but the audit was not yet represented by a dedicated regression test or invoked by the main validation workflow. This meant the successful one-off execution was not fully protected against future regressions.

## Lessons to retain

1. **Separate admission from reproduction.** Source identity, page/crop validity and caption containment are preconditions. They do not demonstrate that a figure has been reconstructed.
2. **Make one-off checks reproducible.** Every manual preflight that is relied upon for release decisions should have a deterministic command, machine-readable output and regression tests.
3. **Test negative paths, not only the happy path.** The audit must fail closed for missing files, wrong hashes, out-of-page crops, missing caption anchors and invalid page indices.
4. **Wire new tests into the actual CI workflow.** A test file that is not called by the repository workflow provides no CI protection.
5. **Preserve the source cohort and its evidence boundary.** The original ten papers are development regression data after inspection; never reuse them to claim a fresh blind generalization rate.
6. **Keep technical and scientific acceptance separate.** PDF parsing, PPTX generation, OOXML validity and LibreOffice rendering are technical evidence. Scientific topology, source fidelity, visual quality, expert review and PowerPoint 2016 host round-trip remain separate gates.
7. **Do not publish a post-repair success rate before the rerun exists.** The 10/10 source preflight result must not be confused with 10/10 figure reproduction.

## Engineering follow-up

- Added `tools/test_audit_blind10_sources.py` with positive and fail-closed cases.
- Added the test to `.github/workflows/validate-assets.yml`.
- Next execution remains the exact ten-crop post-P0 reproduction, with immutable first-pass outputs, per-paper manifests, PPTX previews, object audits, local repair rounds and a final evidence ledger.

## Second increment: reproducible post-P0 batch execution

A successful source preflight alone left the team without an executable next step. The ten-paper run is now represented by `tools/run_blind10_post_p0.py`, which:

- Revalidates all ten frozen source PDFs and crops before starting any generation.
- Refuses to overwrite a nonempty output directory, preserving prior evidence.
- Creates an isolated directory and delivery manifest per figure.
- Uses source-picture-preserving recovery for the three crops known to have no PDF vector drawing records (Wind Turbine, HarnessMM and IIoT); the other seven require native editable import.
- Records technical pipeline statuses and manifest hashes separately from scientific human acceptance and PowerPoint 2016 host validation.
- Continues after a per-paper exception and records it as `PIPELINE_EXCEPTION`, so one pathological PDF does not erase the remaining cohort's evidence.
- Does not calculate a strict reproduction pass rate from technical generation statuses.

Regression tests cover all-ten dispatch after successful preflight, fail-closed preflight blocking, and immutable non-overwrite behavior. The new test is wired into the main CI workflow.

### Operational command

```bash
python tools/run_blind10_post_p0.py \
  --source-dir ./ten_papers \
  --manifest tests/fixtures/blind10_source_regions_2026-11-14.json \
  --output-dir dist/blind10_post_p0
```

This command performs the technical PDF-import route only. FigureSpec reconstruction, source-grounded scientific topology review, multi-round repair, expert acceptance and native Office 2016 round-trip remain distinct follow-up gates.

## CI confirmation for the batch-runner increment (2026-11-17)

- Full Linux validation workflow #842 completed **SUCCESS** after the batch runner and its tests were wired into CI.
- The combined editable-PDF/Office-portability test step passed; repository tool compilation passed.
- Windows PowerShell parser job passed. This validates script syntax only; it does not execute Microsoft PowerPoint or prove Office 2016 host compatibility.
- PP-DocLayoutV3 / PP-OCRv6 real-inference job remained **SKIPPED** because its workflow condition is restricted to PR #10. Do not count this as a successful model inference test.
- The preceding #841 run was cancelled by a newer push; #842 is the authoritative completed run for this increment.

The next blocking work is no longer CI wiring: execute the batch runner in an environment containing the ten private PDFs and retain the actual per-paper PPTX/manifests/previews. CI uses mocked inputs and cannot supply this evidence.

## Third increment: test failure isolation and source-route policy

Expanded the batch-runner regression suite to assert two important contracts directly:

- A synthetic importer exception in the first paper is recorded as `PIPELINE_EXCEPTION`, while the remaining nine papers still execute and retain their own manifests.
- The three source-picture-only cases explicitly pass `require_native=False`; all other seven pass `require_native=True`.

This prevents future refactors from silently converting the image-preservation exception into a false claim of native editability, or from reintroducing fail-fast batch behavior.

## R1 native-vector reproduction findings (2026-11-17)

The uploaded development branch was executed locally against the exact private first-five PDF crops. Source preflight passed 5/5. The first official post-P0 import run produced:
- Wind Turbine: `RASTER_SOURCE_ONLY` (one full-figure picture; no native vectors).
- PINN Tool Wear: blocked by `UNSUPPORTED_SOURCE_CROP_EDGE_TEXT`.
- Attention-GIN: source figure flattened into one full-page picture; its 367 page drawing records did not intersect the selected crop in the importer coordinate system, so this case must not be counted as vector recovery.
- Agent Distillation: blocked at the frozen budget (`127,713 > 100,000` source segments).
- EvoOntology: blocked by crop-edge text; an expanded-crop experimental candidate recovered 327 native vectors and 271 text objects, but text audit found a U+25A1 white-square glyph substitution, so it remains unaccepted.

### Successful native-vector diagnostic candidates

- PINN Tool Wear: after expanding the top crop edge to include the complete journal header span, a candidate was generated with 774 native vectors, 11 text objects and 31 picture objects. Structure audit PASS, text-geometry audit PASS, visual audit PASS. Pipeline status remains `NEEDS_VISUAL_REVIEW`; no scientific or Office 2016 acceptance is claimed.
- Agent Distillation: a crop including the full figure caption generated 828 native vectors, 57 text objects and 4 pictures. Text audit PASS, but structure audit FAIL because only 4 of 15 source picture blocks were retained. It is an inspectable diagnostic candidate, not a deliverable.

### Lessons

1. Crop-edge validation must be based on the actual selected crop and the full glyph bounding box. Header/caption spans can cross the crop boundary by a few points; adjust and re-audit the crop rather than disabling the guard.
2. Resource budgets should be tested independently from crop/text preflight. Raising the budget did not bypass Agent Distillation's crop-edge glyph blocker; do not misdiagnose the failure as a resource-only issue.
3. Native vector count alone is not sufficient. Image events must also be reconciled against source image blocks; Agent's 828 vectors did not compensate for 11 missing source pictures.
4. GIN's page-level drawing records and selected figure crop occupy different coordinate regions in the inspected PDF. Before changing its route, establish the source drawing/image coordinate transforms; do not claim that the 367 unrelated records are recovered figure vectors.
5. Keep diagnostic candidates even when the pipeline rejects them. They expose the next repair target and must remain explicitly REVIEW/FAIL rather than being relabelled PASS.

### Evidence boundary

These runs are local post-P0 technical diagnostics on the frozen development cohort. Human scientific review and actual PowerPoint 2016 host round-trip were not performed. Strict R1 acceptance remains 0/5.


## R1 full-cohort continuation (2026-11-17)

The remaining five source PDFs were run through the post-P0 import pipeline using the frozen page/crop manifest. New technical candidates:
- SkillSmith: 212 native vectors + 115 text objects; structure and text geometry PASS; visual approval pending.
- UCFNet: 122 native vectors + 110 text objects + 3 pictures; structure and text geometry PASS; visual approval pending.
- EvoOntology: 327 vectors + 271 text + 74 pictures; structure PASS; U+25A1 glyph remains NEEDS_REVIEW.
- Paths-over-Graph: 336 vectors + 90 text + 7 pictures; structure FAIL because source picture events are not all retained.
- HarnessMM remains blocked by crop-edge glyph protection.
- IIoT is source-picture-only and is not counted as native semantic reconstruction.

The first five status remains: PINN has 774 vectors and passes structural/text/visual screening but still needs visual approval; Agent has 828 vectors and 4/4 crop-visible images retained after the crop-aware audit fix; Wind Turbine and Attention-GIN are source-picture-only; EvoOntology needs glyph review.

Focused tests: crop-aware audit 6/6, PDF importer 21/21, text geometry 9/9, crop assets 5/5 PASS. Human scientific acceptance and PowerPoint 2016 host round-trip remain outstanding.

Key lessons:
1. Use the same crop scope for source and candidate image-preservation metrics.
2. Never treat page-wide drawings as target-figure vectors without spatial intersection.
3. Distinguish source-picture-only fidelity from native editable semantic reconstruction.
4. Preserve glyph clipping protection; expand crop or request reviewed geometry rather than dropping text.
5. A high vector count cannot mask missing picture events or text substitution.


## R1 full-cohort status consolidation (2026-11-18)

The ten-paper cohort now has a single evidence ledger and source-vs-candidate contact sheet. Current technical classifications:

- Wind Turbine: source-picture-only candidate; semantic editable reconstruction remains open.
- PINN: 774 vectors, 11 text objects, 31 pictures; technical structure/text/visual checks pass, but final visual review remains pending.
- Attention-GIN: target crop is image-backed; the 367 page drawing records are outside the selected figure crop. FigureSpec reconstruction required.
- Agent Distillation: 828 vectors, 57 text objects, all 4 crop-visible image paint events retained; crop-aware structure audit passes.
- EvoOntology: 327 vectors, 271 text objects, 74 pictures; structure passes, U+25A1 glyph review remains.
- HarnessMM: still blocked by crop-edge text guard.
- IIoT: source-picture-only candidate; semantic reconstruction remains open.
- Paths-over-Graph: 336 vectors, 90 text objects, 7 pictures; structure audit fails image-event retention.
- SkillSmith: 212 vectors, 115 text objects; structure/text geometry pass, visual review pending.
- UCFNet: 122 vectors, 110 text objects, 3 pictures; structure/text geometry pass, visual review pending.

The all-ten evidence package preserves originals, candidate PPTX/renders where they exist, and per-paper status. The ten-paper cohort remains a development regression set. No independent blind-generalization claim is made.

Remaining release gates: native semantic reconstruction for three image-backed cases, HarnessMM crop-edge handling, PoG image retention, EvoOntology glyph resolution, visual/expert review for all candidates, and PowerPoint 2016 host round-trip. The frozen scientific rubric is unchanged.
