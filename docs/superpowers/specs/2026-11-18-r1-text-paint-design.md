# R1 source text paint fidelity

## Goal and authority

Continue the already authorized complete ten-figure R1 delivery. Correct visible source-correspondence defects and record reusable development lessons. The user has explicitly opted out of per-case approval and asked for uninterrupted batch work. Preserve frozen v1/v2 and raw failed evidence.

## Observed defects

- EvoOntology's large white CSV text is intentionally painted before its image icon. Appending every textbox after vectors/images exposes text that the source image covers.
- Three vertically placed C/S/V text operations become a single horizontal dictionary span; the current importer and both source audits accept that wrong result.
- SkillSmith's first white badge A is absent from `get_text('dict')` but present in text paint traces. A raw-text inventory is not a complete paint inventory.
- UCFNet's three SimSun operators use fill and stroke. Keeping only substituted font text loses the actual source appearance.
- UCFNet also contains empty path paints. The local line-art extractor omits them without advancing its drawing sequence, while texttrace and bboxlog count them. Trusting the reported drawing sequence can move an occluder before the text it should cover.

## Decision

Use text paint traces as the occurrence and order ledger, shared with source audits. Keep raw dictionary data only as uniquely justified layout/Unicode assistance. Combine native text, paths and pictures by source paint order. Preserve ordinary editable text when its source paint is supported. Recover the three source fill/stroke operators through verified native glyph contours, with a deliberately bounded straight-contour support domain.

Reconcile the ordered vector records with bboxlog's nonempty path paints using paint type, complete path-item bounds and full occurrence coverage. Existing drawing sequence values remain stable object IDs, not ordering authority. A merged fill/stroke vector spanning another visible paint is explicitly unsupported; it cannot be represented faithfully by one native object.

Shrinking or deleting white CSV would change source content. Reordering raw dictionary text alone would still omit trace-only labels. Rasterizing an entire figure would violate the native-object goal. These alternatives are excluded by the established task, not presented as user decisions.

## Constraints

- Preserve every supported visible text occurrence, including repeated same-position paints; no set deduplication.
- Split different baselines/paint operations and preserve explicit geometric gaps. Do not globally normalize ligatures or infer missing mathematical operators.
- Preserve the known Evo NUL/`.notdef` mapping as unresolved. Keep the existing source outline in the private candidate and retain raw audit failures.
- Ignore non-painting text only with clipping-safe evidence. Unsupported paint, ambiguous correspondence, unsupported outline geometry and malformed/nonfinite data fail explicitly.
- Only an explicit figure-region crop makes crossing glyphs a crop-edge rejection; whole-page inherited source overflow remains separately reported.
- Candidate source-order metadata alone is not proof: audits inspect actual shape order, source identities and native outline geometry/style.
- Reuse the current Python/PyMuPDF/DrawingML project; no authoring-platform migration, new benchmark or unrelated AST/CI work.
- Keep private PDFs, extracted source glyph assets and derivative figures out of public Git.

## Source API evidence

PyMuPDF documents `get_bboxlog()` indices as the paint sequence shared by `get_drawings()` and `get_texttrace()`. It also distinguishes trace text from generated spaces in ordinary extraction: https://pymupdf.readthedocs.io/en/latest/functions.html#Page.get_texttrace . Local real-PDF fixtures and the original paper files are the implementation oracle; library documentation does not replace visual replay.

The empty-path counterexample demonstrates a local extraction implementation discrepancy with that documented shared-sequence model. The ordered source-path reconciliation must therefore be checked against actual source geometry and must not infer a version-specific offset or accept candidate metadata as its proof.

## Completion evidence

New real-PDF negative regressions must fail before integration and pass after it. Re-run the affected import/audit suites and the ordered remote CI at the actual new public head. Freshly render changed real candidates, verify source-relative fixes and object/image preservation, then produce one complete ten-figure version with unchanged cases carried forward byte-for-byte. Disclose remaining font/baseline limits and lack of actual Office 2016 execution.
