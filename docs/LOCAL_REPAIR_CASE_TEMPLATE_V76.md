# V7.6 local repair case template

This template standardizes **evidence and execution**, not the scientific repair itself. Each figure is diagnosed against its own source, data contract and intended output profile. Do not apply a generic visual treatment to all figures.

## Required case record

Each repair case lives under `dist/repair_cases/<TASK_ID>/` and contains:

- `rounds/first_pass.pptx`: immutable initial artifact, with SHA-256.
- `rounds/round_01.pptx`, `rounds/round_02.pptx`, ...: immutable candidates, one file per repair round.
- `round_NN_object_diff.json`: added, removed and modified PowerPoint objects; include FigureSpec/DeckSpec semantic diffs where available.
- `round_NN_quality_audit.json`: mechanical regression results for the candidate.
- `renders/first_pass.pdf` and page PNGs; equivalent PDF/PNGs for every round.
- `renders/first_pass_vs_round_NN.png`: visual comparison at the same render size.
- `repair_history.json`: source/input hashes, diagnosis, operation rationale, candidate hash, quality audit, accept/reject decision, and pending human/host checks.
- `repair_case_summary.json`: machine-readable case status and final artifact hash.

## Ordered workflow

1. **Freeze the input.** Record source document, FigureSpec/DeckSpec/data inputs and hashes. Copy the first-pass PPTX once; never overwrite it.
2. **Diagnose before editing.** Map each defect to source evidence, affected semantic object/route, visible consequence, and acceptance test. Record confirmed defects separately from stylistic preferences and unverified hypotheses.
3. **Plan a local repair.** Specify the exact object IDs, expected prior values, intended changes, source rationale and negative tests. Prefer local changes; rebuild a whole panel only when the underlying semantic structure is wrong.
4. **Execute one round.** Generate a new PPTX from the previous accepted candidate. Never overwrite a prior round. Save the source-spec diff and native PowerPoint object diff.
5. **Audit the candidate.** Run scientific topology/data checks, editability, image policy, accessibility, font/geometry, overlap and bounds checks. Compare all hard gates against the previous accepted candidate; reject regressions but preserve rejected files for audit.
6. **Render every round.** Use an isolated LibreOffice profile outside the evidence directory. Save PDF and page PNGs at fixed DPI; create before/after comparisons. Do not treat a successful export as a scientific pass.
7. **Promote only accepted rounds.** Record the decision and hashes. The final artifact is a candidate for independent review, not an automatic human acceptance.
8. **Prepare independent review.** Reviewers inspect source and final-size output, complete the blind initial record before reading implementation/benchmark expectations, then complete the six dimensions and hard-failure checks.

## Required quality gates

- Scientific: labels, formulas, values, direction and semantic routes match source evidence; no unsupported inference.
- Data/image: raw values, row counts, image hash, processing log and scale/calibration remain traceable.
- Readability: no text collision or clipping; critical content is legible at the intended final size.
- Accessibility: contrast and non-color encodings are checked; alt text and reading order are present.
- Editability/reproducibility: editable vector/text objects remain native; source/configuration hashes and build command are recorded.
- Visual: local repair does not introduce unrelated layout, typography or style regressions.

A CI PASS means only that the automated checks ran and passed. It does not replace independent domain review, actual projection/print-size inspection or a PowerPoint 2016 host round trip.

## Reusable implementation

Use `tools/repair_case_artifacts.py` for SHA-256, PPTX object snapshots/diffs, isolated LibreOffice rendering and side-by-side render evidence. Domain-specific builders and validators remain responsible for generating and judging each repair candidate. The C01-SEANet and C01-composite cases are the first examples; DECK01 v7.6 exercises the same case packaging with a DeckSpec-level repair.
