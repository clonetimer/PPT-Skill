# First-pass and final-delivery success metrics

## Definitions

**First-pass success rate**

`first_pass_passed / frozen_first_pass_population`

This rate is calculated from an immutable first-pass baseline. Later repairs never rewrite the first-pass result.

**Final-delivery success rate**

Two rates are reported:
- `accepted / completed_valid_human_reviews`: success among tasks with a completed, evidence-backed, independent human final review;
- `accepted / registered_tasks`: success against the full registered cohort, so pending work remains visible.

A task counts as accepted only when the reviewer is explicitly human and independent of the build, the initial blind review precedes benchmark expectations, source and scientific relationships are checked, final-size evidence is recorded, all six dimensions score at least 2/4, and every hard-failure flag is explicitly false.

A repaired task is counted in `accepted_after_repair` when its final review passes and `repair_rounds > 0`.

## Calculation

Use a frozen baseline JSON and the canonical V7.6 `review.json`:

```bash
python tools/final_delivery_success.py \
  path/to/frozen_first_pass_baseline.json \
  path/to/review.json \
  --output dist/final_delivery_success_v76.json
```

The calculator detects the canonical V7.6 review-ledger schema automatically. Run `python tools/validate_release_readiness.py review.json` separately before release; that gate verifies the current source and artifact SHA-256 values and requires the full cohort to pass.

## Current measurement boundary

- C01-SEANet Stage 1: 12/24, FAIL, AI technical review; preserved as a historical first-stage record, not a human final review.
- C01-SEANet v7.4 and C01-composite v7.5: automated repair and structural audits are not independent human acceptance.
- Final-delivery rate remains `NOT_YET_MEASURABLE` until human final reviews are entered.
- A 15-figure first-pass rate must use a frozen, complete 15-item first-pass baseline; it must not be inferred from a single C01 review or from CI success.
