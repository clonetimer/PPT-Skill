# R1 PowerPoint 2016 Host Acceptance

## Purpose

Run the ten delivered R1 PPTX files in the actual target Windows PowerPoint installation. This is the outstanding host-compatibility gate; Linux/LibreOffice rendering and Windows PowerShell parser CI are not substitutes.

## Inputs

- The ten final R1 v3 PPTX files from the frozen delivery package.
- The repository script `windows/Test-PowerPoint2016RoundTrip.ps1` at the exact reviewed commit.
- A Windows desktop with PowerPoint installed and permission to launch PowerPoint COM automation.

Keep the original input directory read-only. Use a new, empty output directory outside the input directory for every run. The script rejects output paths inside the input directory and refuses to overwrite existing round-trip artifacts; use a fresh output directory for retries so previous failure evidence remains intact.

## Confirm the host

1. Open PowerPoint.
2. Inspect **File → Account → About PowerPoint**.
3. Confirm that the installed product is actually Office 2016. Version 16.0 alone is insufficient because Microsoft 365 also reports 16.0.
4. Record the product display name and version in the run report. Only use `-ConfirmOffice2016Installation` after this manual check.

## Frozen PPTX hash manifest

The v3 package's ten derived PPTX hashes are frozen in `tests/fixtures/r1_v3_pptx_sha256_2026-11-18.csv`. This manifest was calculated directly from the ten PPTX byte streams in the frozen v3 delivery ZIP, not copied from the source-PDF manifest. Use that tracked file unchanged for the v3 host run. If the PPTX files are intentionally revised, create a new versioned manifest; never overwrite this one.

Before running, verify the extracted ten PPTX files match the frozen manifest. The script checks exact base names, count and per-file SHA-256 before launching PowerPoint.
## Run

Open Windows PowerShell 5.1 (not PowerShell Core) and run:

```powershell
$input = 'C:\R1\pptx'
$output = 'C:\R1\office2016-roundtrip'
New-Item -ItemType Directory -Force -Path $output | Out-Null

powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File '.\windows\Test-PowerPoint2016RoundTrip.ps1' `
  -InputDirectory $input `
  -OutputDirectory $output `
  -ExpectedFileCount 10 `
  -ExpectedSha256Manifest '.\tests\fixtures\r1_v3_pptx_sha256_2026-11-18.csv' `
  -RequireOffice2016 `
  -ConfirmOffice2016Installation
```

If the About dialog does not establish Office 2016, omit both confirmation switches and report the actual host identity. Do not relabel an unconfirmed version as Office 2016.

## Per-file behavior

For every PPTX the script:

1. Opens the original read-only.
2. Captures slide and ordered top-level shape snapshots, recursively including nested GroupItems.
3. Records shape type/name, z-order, position, size, rotation, text and font family.
4. Saves a new PPTX; it never overwrites the source.
5. Exports PDF and PNG from PowerPoint.
6. Closes and reopens the saved PPTX.
7. Repeats the structural snapshot and compares the before/after state.
8. Writes per-file input/output SHA-256 and a combined JSON report.

Before launching PowerPoint, the script checks the exact ten filenames and verifies every input PPTX SHA-256 against the frozen CSV manifest (`filename,sha256` columns), then preflights every expected output filename across the entire input batch. Any identity/hash mismatch or output collision aborts before the first deck is opened, preventing a substituted or mixed partial batch. The output directory must contain ten `_office_roundtrip.pptx`, ten `_office_roundtrip.pdf`, ten `_office_roundtrip.png`, and `office2016_roundtrip_report.json`.

## Acceptance interpretation

- `STRUCTURE_PASS`: PowerPoint opened, saved, exported and reopened the file, and the recorded structural snapshot remained equal. This is not a visual or scientific PASS.
- `FAIL`: an open/save/export/reopen or structural comparison failed. Preserve the output and report; do not overwrite the failure evidence.
- Manual visual review: compare each PowerPoint-exported PDF/PNG against its matching source crop and the frozen R1 v3 comparison. Inspect formula baselines, image clipping/masks, arrowheads, gradients, occlusion order and group children.
- Scientific acceptance: a domain reviewer separately verifies labels, equations, topology, data traces and causal/architectural relationships.

## Required return evidence

Return the complete `office2016_roundtrip_report.json`, all ten PowerPoint-exported PDFs (or a ZIP containing them), the ten PNG previews, and a screenshot of File → Account/About PowerPoint showing product identity. Keep the original inputs and their SHA-256 manifest unchanged.

Do not report the Office 2016 gate complete until all ten files have a host report and their exported renders have been visually reviewed. A green Windows parser CI job only proves script syntax.

The runner also validates the exact ten expected R1 deck base names before launching PowerPoint. This catches same-count substitutions (for example, nine correct decks plus one unrelated PPTX), which a count-only check cannot detect. The frozen source PDF SHA-256 manifest remains a separate source-integrity check; it must not be confused with the derived PPTX identity or hash.


If one deck fails during COM open/save/export/reopen, the script records a per-file `FAIL` entry (including exception type/message and any partial output paths) and continues with the remaining decks. At batch end it writes the combined report and exits non-zero if any file failed. Preserve all partial outputs and the report; do not rerun into the same output directory. Preflight failures (wrong count/name/hash or output collision) abort before PowerPoint starts and therefore do not produce a per-deck report.


If PowerPoint COM cannot start or the host identity check fails after input preflight, the runner writes a batch-level failure and adds `FAIL` entries for every deck not reached (`failure_scope=BATCH`, with no output paths). Completed per-deck entries are preserved. It then writes the ten-entry JSON report and exits non-zero. Input count/name/hash and output-collision preflight failures remain early aborts before host launch and are not represented as Office execution results.
