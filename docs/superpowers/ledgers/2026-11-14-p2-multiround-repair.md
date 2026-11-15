# P2/P3 Execution Ledger — Multi-round Repair and 15-Figure Review

- Added `local_repair_loop.py`: immutable first-pass copy, bounded repair rounds, stable source-object targeting, preconditions, per-round PPTX, object-level diff, and quality audit.
- Added regression guards for object recall, duplicate/missing IDs, source order, text CER, geometry IoU when comparable, and object-class mismatch.
- Rejected rounds remain preserved with their diff and quality report; they are not promoted as final.
- Added tests for accepted repair, quality-regression rollback, and unknown source-object rejection.
- Added `fifteen_figure_review_packet.py`: registers 15 tasks, computes object-level PPTX differences, and leaves human final review pending.
- Audited available V7.6 initial and reconciliation bundles: 16 PPTX files exist in each and every paired file is byte-identical. These bundles are not a valid repair before/after pair; no improvement rate is claimed.
- Final success calculator hardened to require independent reviewers, six evidenced dimensions >=2/4, and explicit hard-failure clearance.
- First-pass historical baseline remains 0/10 and immutable. Final delivery rate remains not measurable until human reviews are completed.
