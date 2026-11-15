# Multi-round local repair and 15-figure final review

## 1. Repair loop

The repair loop is deliberately conservative and non-destructive. It keeps the original first-pass PPTX, creates one immutable PPTX per repair round, records source-object-level diffs, and audits each candidate against the same composition manifest.

Supported explicit operations:
- `move`: set target EMU coordinates for a source-object ID.
- `rotate`: set target rotation in degrees.
- `set_text`: replace text in an editable text frame.

A plan must name the stable SourceLayout object ID. Optional expected text/rotation values act as preconditions. Unknown IDs and failed preconditions stop the loop. Each candidate is re-audited for object recall, missing/duplicate objects, source order, text CER, geometry IoU when comparable, and object class. A regression rejects promotion but the rejected PPTX and report are preserved.

Example plan:

```json
{
  "rounds": [
    {
      "operations": [
        {
          "source_object_id": "text_0_0_0",
          "operation": "move",
          "left_emu": 914400,
          "top_emu": 1097280
        }
      ]
    }
  ]
}
```

Run:

```powershell
python tools/local_repair_loop.py .\first_pass.pptx .\repair_plan.json .\source_composition_manifest.json --output-dir .\repair_runs --max-rounds 3
```

Outputs:
- `first_pass.pptx` — immutable first attempt;
- `round_01.pptx`, etc. — immutable candidate per round, including rejected rounds;
- `repair_history.json` — hashes, operations, object-level diffs, quality report, regression reasons, and promotion decisions;
- final path/hash — latest accepted candidate.

The engine does not invent scientific text or topology. Text changes must be explicitly supplied in the plan and checked against source evidence. Scientific and visual acceptance remain human gates.

## 2. Fifteen-figure comparison packet

Run:

```powershell
python tools/fifteen_figure_review_packet.py .\initial_pptx .\final_pptx --output-dir .\review_packet
```

The packet compares the 15 registered figure tasks and records shape-level changes. Identical PPTX files are marked `NO_REPAIR_APPLIED`; missing final outputs remain pending. It never counts CI as human approval.

**Current artifact audit:** the available V7.6 initial and reconciliation review bundles contain the same 16 PPTX files byte-for-byte. They are two review stages, not before/after repair outputs. Therefore no repair improvement is claimed from comparing those archives. Actual repaired PPTX files must be produced by the repair loop before a genuine before/after comparison can be made.

## 3. Final success accounting

The immutable first-pass metric remains separate. Final PASS requires a registered independent reviewer, review-order attestation, six evidenced rubric dimensions each >=2/4, and explicit clearance of all hard-failure checks. Pending reviews do not enter the completed-review denominator.
