# R1 development experience — completing the original ten figures

## Scope and frozen evidence

This work continues the original ten-paper R1 development regression cohort. The ten original PDFs were recovered on 2026-11-18 and each SHA-256 matched `tests/fixtures/blind10_source_regions_2026-11-14.json`. The frozen first-pass artifacts and scores are not overwritten. Private source documents and derivative figures are not published in this repository.

The starting package contained nine PowerPoint candidates. Wind Turbine, attention-guided GIN and IIoT were full-figure pictures; HarnessMM had no candidate because its crop intersected caption text. The six remaining cases contained native vector objects, although counts of path objects do not establish semantic editability or scientific correctness.

## Lesson 1: inspect the selected figure, not the page inventory

The attention-guided GIN page contains vector drawing records outside the chosen figure. The actual frozen crop has **zero drawing records, one visible image and sixteen text spans**; those spans belong to caption text. Page-wide vector counts had incorrectly encouraged a native-import route.

The import runner now explicitly classifies this crop with the other three image-backed cases. A regression test first failed with `[False, True, False, False]` for the four known image-only cases, then passed with all four classified consistently. The other six still require native import. This classification only describes source-picture preservation; it does not count it as completed native reconstruction. The remedy for the figure itself is source-grounded semantic rebuilding.

## Lesson 2: technical render success and visual fidelity are separate facts

An old `visual_audit.json` can legitimately contain `status: PASS` alongside `requires_visual_review: true`: the comparison executed successfully, but its tiles raised a fidelity concern. The release classifier checks both fields. This is not a schema mismatch and must not be “fixed” by dropping the review flag or lowering thresholds.

The previous misleading interpretation is corrected here. Inspect source and candidate side by side, and retain model inspection separately from independent domain acceptance.

## Lesson 3: CI validates the code named by its commit

At the start of this run PR #20 was draft/open at `d722f68891910415ae2ad2d713d88278f7b892d8`. GitHub Actions run **851** (`44224881881`) succeeded for the Linux validation job and PowerShell syntax job. The optional OCR job was skipped. This is evidence about that exact code revision, not about the private ten-paper visual results, and the PowerShell syntax job does not execute PowerPoint 2016.

Before recording a newer success, fetch its exact head SHA and its workflow jobs. A branch-name query, an older run, an optional skipped job or a locally written report cannot stand in for fresh remote evidence.

## Working practices applied in this batch

- Restore one stable working copy and keep prior packages read-only. Do not repeatedly unpack over active fixes.
- Give each source and render a unique directory. Identically named `candidate.pptx` files must never share a PDF export directory.
- Store source hashes, original and revised crop coordinates, object inventories, actual render hashes and limitations together.
- For image-backed scientific figures, transcribe the observed labels and relationships before drawing; validate that contract independently of the drawing code.
- For source-visible numerical curves, preserve source pixels or record pixel digitization. Do not invent plausible waveforms or describe digitized traces as recovered raw observations.
- Deliver the full batch without asking the user to approve each small step. Keep unresolved external review facts explicit instead of silently promoting a candidate to accepted science.

## Lesson 4: image occurrence scope must match the crop

`audit_imported_pdf_figure.py` previously counted images from the page text dictionary. That inventory may contain off-crop images and omit a visible XRef. The audit now uses `collect_image_events`, the same crop-visible paint-occurrence collector as the importer. Repeated visible uses still count separately. An unresolved visible image explicitly fails the check; it must not disappear from the denominator.

The focused tests cover off-crop dictionary pollution, repeated occurrences, actual image removal and unresolved extraction. An image-count pass is still not an image-identity or perceptual-fidelity proof; the private source/candidate evidence and provenance checks remain necessary.

## Lesson 5: a missing source glyph is not permission to invent an operator

EvoOntology's problematic character was traced beyond text extraction to the embedded font and source content stream: character zero maps to glyph ID 0 (`.notdef`). The original PDF visibly renders a narrow empty rectangle. The correct fidelity action is to preserve that visible outline and record the unresolved mapping. It is not evidence for a minus sign, even if one might appear plausible from surrounding text.

Any localized glyph replacement keeps its source evidence in metadata and a separate review record. Hidden surrogate text must not be added merely to make the generic text counter pass. A generic audit exception remains visible until an independently justified source mapping exists.

## Completion evidence

The integrated batch report records the new per-figure results and remaining limitations after rendering. Only verified changes are added below; this document does not certify a result merely because a task has been started.

## Lesson 6: rotate the object bounds before checking the slide boundary

UCFNet's vertical classifier label exposed a second audit disagreement. Its raw OOXML text frame extended past the slide before its 270-degree rotation, while the rotated visible frame was entirely inside. The coarse candidate profiler inspected the unrotated box; the detailed text audit already inspected the rotated box.

The profiler now reuses the detailed audit's rotated-frame calculation, retaining its existing 0.72pt tolerance. Two synthetic regressions first failed: a valid 270-degree label was rejected, and a 45-degree label that crossed the upper edge was missed. Both now pass. This corrects false positives and false negatives without enlarging the canvas or weakening the boundary check.

## Lesson 7: native objects inherit theme effects unless explicitly neutralized

The first native diagram renders showed shadows not present in the source, even though the authoring code had not requested shadows. Default PowerPoint shape styles can carry effect references. The private native builders now explicitly remove inherited theme effects and use empty effect lists; deliberate source gradients remain. Visual inspection also caught a wrapped panel heading and formula frames that changed mathematical grouping, which were repaired locally rather than by shrinking the whole figure.

## Lesson 8: retaining image bytes does not prove retaining their visible pixels

Fresh inspection of PINN exposed source images whose clipping masks had not survived import. The same source asset bytes could still pass a provenance/count check while exposing image regions the paper did not show. Repairs must follow the source clip geometry and preserve each local image, with a derivation record; a whole-figure screenshot is not a native fix. The generic importer still requires explicit visual review for complex clipping and cannot be certified by asset counts alone.


## Lesson 9: cross-checking the paper must not silently rewrite its figure

An independent source comparison found that the GIN figure repeats a projection input where the paper body uses the next indexed input. The first native transcription had followed the body equation. For a source-visible reproduction, preserve the literal figure and record the figure/body discrepancy separately. Do not silently turn a reproduction into a corrected interpretation. The same independent check caught a summation neighborhood index placed above instead of below its operator. Native editability alone does not protect mathematical meaning.

## Lesson 10: transparent PDF text can be an invisible duplicate of visible outlines

The Agent Distillation source has six non-painting Unicode spans over an equation whose visible glyphs are already vector paths. Reproducing those spans as opaque text duplicated the equation. SkillSmith also has two non-painting Type3 text overlays. The verified repair keeps the visible source paths and omits only overlays whose paint traces establish that they do not draw.

The first attempted fix used `span.alpha == 0` alone. Independent review rejected that rule with a real ReportLab counterexample: PDF text rendering modes 2 and 6 can have transparent fill and an opaque stroke. The dictionary still reports alpha zero and the same character flags as ordinary fill text. Dropping that run caused a missing visible label to pass all three source checks. Green tests of ordinary transparent text had not covered the dangerous case.

The importer, crop-edge guard, structural source-label comparison, text-geometry collector and source profile now share `TextVisibility`. It matches glyph paint traces using font, size, character identity, origin and geometry. Only complete non-painting evidence permits omission. A visible stroke, missing trace, partial match or unresolved clip-only mode blocks import and remains required by the audits. Missing alpha, white text and every nonzero alpha remain visible candidates. Type3 glyph baselines may lie outside their bounds, so matching uses the glyph ink box rather than assuming the baseline is inside it. Raw source-layout extraction remains unchanged.

Synthetic regressions retain both sides: transparent fill-only and Type3 overlays do not become visible; modes 2 and 6 with visible strokes must be rejected, and an empty candidate must fail source audits. Missing and incomplete paint evidence also fails closed. This is a narrow overlay correction, not certification of every PDF text rendering mode or arbitrary transparency composition.

Follow-up review found a second counterexample: transparent text in modes 4, 5 and 6 still clips later artwork. MuPDF's paint traces report zero opacity, while its extended drawing list does not expose the text clipping path. The helper now also parses PDF operators in the page and reachable Form streams using `pypdf.ContentStream`. Any `Tr` outside modes 0–3, or a stream that cannot be parsed, blocks omission. This deliberately allows conservative rejection of an unrelated clipping run. Regression fixtures cover all four clip modes in direct and nested Form content, and verify that the source really displays a glyph-shaped clipped fill. Operator parsing avoids mistaking strings or comments for rendering instructions.

This matters beyond one label: restoring the appearance requires reasoning about paint operations, not merely preserving extracted Unicode. Source vectors, text and picture assets are separate paint layers; duplicate hidden accessibility text must not be promoted into visible scientific content.

## Code review and local validation

The first independent review covered the crop-image, routing and rotation corrections and passed 60 focused tests. A later review found the zero-alpha visible-stroke counterexample described above. The correction was held locally until the new negative tests reproduced that false-pass path and the shared paint-aware implementation fixed it. Updated test logs and the follow-up review belong to the final delivery evidence; the earlier review is not presented as approval of code added afterward.

Image identity, complex clipping, PDF shading paints and perceptual correspondence remain separate checks. Source asset counts and unit tests cannot certify them. Likewise a model's visual review is not a human scientific approval or a PowerPoint runtime test.

## Verified local batch result

The integrated private package now contains all ten one-slide PPTX candidates and ten freshly exported PDF previews. Four image-backed figures were rebuilt as native semantic objects; six vector-source figures were repaired at the source-glyph, shading, image-clip or crop level. Each original PDF hash and each final PPTX-to-PDF render binding was rechecked. All ten have native vector objects, zero full-page picture objects and zero rotated-frame boundary violations. All ten pass the conservative OOXML compatibility preflight; this is not an Office-host result.

The final focused local validation is **136 tests across 12 suites**, with zero failures, plus Python compilation and whitespace checks. Follow-up independent code review passed **91 tests**, checked **24 actual PDF text-clipping combinations** (direct/nested, whole-page/crop), and tested operator-versus-string/comment parsing; no remaining blocker was reported for the changes under review. The new remote CI result must be tied to the committed head and is recorded in the delivery evidence after push.

These are native/partly raster technical reproductions with documented source-correspondence reviews, not a claim that every glyph is an ordinary editable text box. PINN's text remains native outline paths. Local photographs, icons and source shading/image pieces remain pictures where documented. EvoOntology's unmapped glyph is preserved as its source outline with the generic text-audit exception retained. The raw mixed-baseline text-calibration failures also remain in the private evidence. No independent human acceptance, new blind benchmark score or actual Office 2016 execution is inferred.
