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
