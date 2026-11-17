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
