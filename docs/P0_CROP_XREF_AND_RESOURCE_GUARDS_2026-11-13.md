# P0 crop/XRef recovery and dense-PDF resource guard — 2026-11-13

**Scope:** P0-01 (#11) and P0-02 (#12), from the frozen ten-paper unfamiliar-figure benchmark. Reference first-pass implementation SHA: `47f034548aa05d617ad12bfec86efee70d5d2bd8`. Updated implementation is in Draft PR #10, not main.

## Reproducible root cause

Four cropped figure pages have visible PDF `fill-image` paint events and valid XRef image occurrences returned by `page.get_image_info(xrefs=True)`, but zero image blocks in `page.get_text("dict")`. The original importer paired only image text-dictionary blocks with `fill-image` events and emitted blank PPTX slides.

The new `tools/pdf_source_assets.py` reconciles the PDF painter log with image XRef occurrences, retains source paint order, crops to the true visible page rectangle, records XRef and asset hashes, excludes off-page images, and avoids duplicate block/XRef placement. Missing visible image resources and fully empty output now raise explicit errors instead of silently generating an ostensibly successful slide.

## Real crop regression (local, source files not committed)

| Case | Old | New native vectors / text / picture | Recovered XRef | Off-page image events | Actual rendered SSIM (source PDF vs LibreOffice PPTX-PDF) |
|---|---|---|---:|---:|---:|
| Wind turbine | Blank | 0 / 0 / 1 | 1 | 0 | 0.8746 |
| Attention-guided GIN | Blank | 0 / 0 / 1 | 1 | 0 | 0.8441 |
| HarnessMM | Blank | 0 / 0 / 1 | 1 | 0 | 0.9122 |
| IIoT digital twin | Blank | 0 / 0 / 1 | 1 | 1 | 0.9131 |

All four imported source images are independently placed PowerPoint **picture objects**, not native editable components. They are explicitly classified as `source_picture_only`. This is an honest recovery of visual content; it does **not** count as strict 21/24 or as native-editable scientific-figure reconstruction.

**GIN nuance:** 367 stroke draw records are present in the source PDF, but they are outside the selected crop's visible region; they must not be transplanted into the target slide. The corresponding author figure is within the XRef picture. **IIoT nuance:** the second image paint event is completely outside the selected crop; it must be excluded.

The SSIM scores are scikit-image SSIM on page-matched RGB PDF rasterizations at 1.5× PDF scale. They are diagnostic visual similarity measures, **not** scientific-accuracy or PowerPoint 2016 host scores; differences include resampling, antialiasing and slide fonts.

## Dense figure regression

The selected Agent Distillation figure crop has **831** PDF graphics paths containing **127,713** source path items, including dense nested contours. `page.get_bboxlog()` and `page.get_drawings(extended=True)` complete rapidly; the expensive step is constructing thousands of PowerPoint freeforms from these items.

`tools/pdf_import_budget.py` now establishes default preflight budgets:

| Guard | Default |
|---|---:|
| Source drawing groups | 10,000 |
| Source path items | 100,000 |
| Estimated output vertices | 250,000 |
| Elapsed seconds | 60 |

The known Agent Distillation crop exits in approximately 0.5 seconds with `RESOURCE_LIMIT: source_segments 127713 > 100000`; no partial PPTX is written. This is a **controlled rejection**, not successful editable reconstruction. The same code still converts small ordinary vector PDFs.

## CI and verification

- [GitHub Actions #135 — PASS](https://github.com/clonetimer/PPT-Skill/actions/runs/43456864596) on `21278aaf`.
- Crop/XRef tests: 5/5; import budget tests: 5/5; existing importer tests: 12/12; existing audit/Office/first-pass/generalization tests also PASS.
- Local frozen source tests: 4/4 formerly blank inputs become nonempty; source/converted PDFs and side-by-side diff images inspected.
- The target Windows Office 2016 COM round trip **has not been run**.
- The frozen blind-cohort strict first-shot success remains **0/10**; this is a development-set fix and cannot be used to claim a new holdout first-pass score.

## Known constraints and next gates

- Rasterized author source figures cannot become individual editable science nodes merely from XRef recovery. P1-02 defines source-aware mixed/native reconstruction.
- Rotated or skewed placed pictures are currently surfaced as visual-review warnings; complete arbitrary affine transformation fidelity is not yet certified.
- P0-03 (#13) is next: source-referenced text geometry, formula glyphs and collision debugging.
- P0-04 (#14) must separate `source_picture_only`, hybrid native/bitmap, fully native vector and unsupported routes in strict release statuses, with scientific review never implied by OOXML checks.
- No author PDFs, source images or derived figure presentations are pushed to this public repository.
