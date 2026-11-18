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

The output directory must contain ten `_office_roundtrip.pptx`, ten `_office_roundtrip.pdf`, ten `_office_roundtrip.png`, and `office2016_roundtrip_report.json`.

## Acceptance interpretation

- `STRUCTURE_PASS`: PowerPoint opened, saved, exported and reopened the file, and the recorded structural snapshot remained equal. This is not a visual or scientific PASS.
- `FAIL`: an open/save/export/reopen or structural comparison failed. Preserve the output and report; do not overwrite the failure evidence.
- Manual visual review: compare each PowerPoint-exported PDF/PNG against its matching source crop and the frozen R1 v3 comparison. Inspect formula baselines, image clipping/masks, arrowheads, gradients, occlusion order and group children.
- Scientific acceptance: a domain reviewer separately verifies labels, equations, topology, data traces and causal/architectural relationships.

## Required return evidence

Return the complete `office2016_roundtrip_report.json`, all ten PowerPoint-exported PDFs (or a ZIP containing them), the ten PNG previews, and a screenshot of File → Account/About PowerPoint showing product identity. Keep the original inputs and their SHA-256 manifest unchanged.

Do not report the Office 2016 gate complete until all ten files have a host report and their exported renders have been visually reviewed. A green Windows parser CI job only proves script syntax.