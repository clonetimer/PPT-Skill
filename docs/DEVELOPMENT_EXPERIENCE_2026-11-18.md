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

## Lesson 11: inspect CI step timing before treating dependency wait as test work

The last successful run, #851, took 43 minutes 12 seconds to install its rendering dependencies. Its log reports 164 MB fetched in 42 minutes 31 seconds, averaging 64.2 kB/s from the regional EC2 Ubuntu mirror. The 61.2 MB CJK font package alone occupied roughly 16 minutes; the 43 MB LibreOffice core package occupied roughly 12.6 minutes. Package-index refresh took seconds, and the actual validation work was much shorter.

The workflow now points the hosted runner's existing Ubuntu mirror-list file at the official HTTPS archive and applies three download retries plus 30-second HTTP/HTTPS connection/data timeouts. It keeps all rendering dependencies, fonts, tests and acceptance gates. The shell block and YAML were checked, and all workflow fields outside that block were compared unchanged. A timeout is not a total download deadline, and a different mirror is not proof of faster CI: the next run's observed timing and exact head SHA remain the evidence.

The mirror change was measured in run **#855** at `b454b40a630275afabc3f8938b9b2c5c3fc9ce76`: the installation step finished in **48 seconds** (07:04:25–07:05:13 UTC), compared with 43m12s in #851. That run then failed a new test assertion, so the faster installation is not recorded as a green overall CI result.

## Lesson 12: assert source preservation across extraction-library versions

The local private rendering environment uses PyMuPDF 1.26.6. CI installs newer dependencies and used PyMuPDF 2.1, where a mode-6 fill/stroke/clipping text call produced two extracted dictionary spans instead of one. The importer still rejected unsupported paint; the regression test had incorrectly hard-coded a span count of one.

The test now independently reads the raw source PDF, requires the intended label to exist, and requires all source audits to retain the complete observed label Counter. An empty candidate must still fail, and the importer must still reject the source. This preserves the missing-label protection without assuming an internal extraction count. No production acceptance threshold is changed. The private regeneration requirements pin the versions actually used for the delivered figures; no PyMuPDF 2.1 private rendering result is claimed.

## Lesson 13: turn a verified figure repair into the default generation path

The delivered batch needed 35 private picture-clip corrections: 31 PINN images, one EvoOntology image and three UCFNet images. The shared source-image collector previously intersected only the image rectangle and page rectangle. A circular, compound or nested source clip could therefore expose pixels that the source paper hid, despite correct picture counts and source image hashes.

`pdf_image_clips.py` now recovers the original image occurrence and clip chain from MuPDF's source SVG, then replays only that source image through the original paths. The existing PDF importer and structural audit use the corrected collector; the command-line entrypoint is unchanged. Source vectors, text and connectors are not rasterized. Unsupported composition remains an explicit unresolved-image failure.

Two details were essential for reuse. EvoOntology contains local `use` references as well as direct `image` elements, and mask/defs resources must not be counted as page paints. Also, the raw alpha-bearing pixels must remain separate from the page-cropped pixels: placing an already cropped soft-mask image back at its original bounds would stretch or crop it twice. Occurrence order, geometry, decoded pixels and source-mask placement are verified together. A curved clip can change pixels without changing the bounding rectangle, so a changed-bounds-only shortcut is insufficient.

The first fixed-576-dpi implementation would have reduced a dense 1000-pixel local image to 640 pixels. A failing regression exposed that loss. Rendering now uses at least 576 dpi while retaining a higher original pixel density, subject to the same allocation limits. Provenance records the actual density and original/final hashes. The decision preserves source detail; it is not recovery of any underlying numerical measurements.

Private development replay used the same original PDF hashes and new output directories, without the old image-clip payload. PINN has 31 clipped pictures, EvoOntology 72 clipped occurrences among 74 pictures, and UCFNet three clipped pictures. All three have zero unresolved image events. The first replay's 31 PINN assets matched the private repairs exactly, but fresh EvoOntology visual inspection subsequently exposed a sub-point image-renderer defect shared by the old private script (Lesson 15). That initial equality is preserved only as historical evidence, not as proof of correct source fidelity. The corrected replay is checked against the original PDF, including tiny symbols and narrow strips. The additional EvoOntology clips and higher source density are recorded as explicit changes. The existing unresolved source glyph is separately preserved; its meaning and generic text-audit exception remain unresolved.

## Lesson 14: reject expensive paths before parsing and allocation

Independent review found that a post-parse path-count check was too late. With a configured limit of ten, a 50,002-command test path had already produced 50,003 recorded operations and about 11.1 MB of Python allocations before rejection. The fix checks path-data length and streamed token count before fontTools builds its token list, then uses a bounded recording pen during command expansion. The same review probe now rejects with zero recorded operations. Raster allocation is independently limited to 16 million pixels per image and 64 million per page.

The final focused local check is **78 tests across six suites**, including **13 image-clip tests**, plus compilation and whitespace checks. The review also compared a nonconstant-alpha image with the actual source PDF rendering under full-page and partial-crop/XRef-fallback conditions: maximum premultiplied RGBA channel difference was two, with no pixels differing by more than five. Group opacity, Multiply blend, image rotation and unsupported multi-child clip geometry were explicitly rejected; nested clips, ColorKey masks and Decode inversion were exercised.

A separate bare `unittest discover` attempt ran 488 tests but had 19 environment/fixture errors and four skips: the archive-based local checkout lacks generated C01 prerequisites/history, a `libreoffice` command alias and a WOFF2 decoder, and some test modules assume standalone process setup. That exploratory invocation is not recorded as passing. Its complete failures are retained in the private continuation evidence; the repository's ordered CI workflow is the integration gate. No model check is promoted to independent human scientific approval or actual PowerPoint 2016 execution.


## Lesson 15: inspect tiny real symbols after every image-rendering change

The first real EvoOntology preview exposed a missing case in the synthetic tests: two 111-by-22-pixel three-dot source images are placed at less than one PDF point in height. In PyMuPDF 1.26.6, an isolated PDF MediaBox with either extent below one point became a one-by-one-point page. The renderer returned a 24-by-24 image, which stretched into one black oval when placed at the original rectangular bounds. Image counts, alpha checks and the source identity checks had all passed. The failed preview was preserved and not promoted.

A new real-PDF regression first reproduced the 24-pixel result. The isolated renderer now scales the complete PDF coordinate system so both page extents are at least two points, then applies the inverse scale during rasterization. It verifies actual pixel dimensions against the requested geometry, allowing only one pixel of rounding, and records both sizes. Allocation reserves that rounding margin before rendering. The regression now retains all three separate dots and the source aspect ratio. This is why fresh source/candidate rendering remains necessary even after the structural checks pass.

The same sub-point check found 13 narrow PINN picture pieces affected by the old private helper. Both the new importer and the batch regeneration are corrected together; a legacy candidate is not used as the sole truth when it shares the same renderer failure. The earlier complete delivery remains frozen as historical evidence, with the corrected batch version carrying fresh renders and explicit source comparisons.

## Lesson 16: text extraction order is not source paint order

EvoOntology's conspicuous white CSV letters initially looked like a font-size error. Source tracing showed that their font size was correct: the PDF paints the letters first and then covers most of them with an image icon. The importer appended all text after every vector and image, exposing letters that the source had occluded. A second CSV consisted of three source drawing calls at different vertical positions, which the reading-order text dictionary merged into a horizontal word. Resizing that word would have hidden the real defects.

SkillSmith exposed the complementary failure. Its first badge is painted as a black A, a blue circle and a white A. The raw text dictionary omitted the white A at the nearly identical position. The old importer retained the black underprint and put it on top. Later badges retained their white letters but still exposed the wrong black layer. Source-label counts derived from the same dictionary could not detect the missing paint occurrence.

The shared collector therefore starts with `get_texttrace()` occurrences and their source sequence numbers. Raw character records supply layout, font metrics and effective size only when the glyph correspondence is unique. They never decide whether a source occurrence exists. Run splitting respects different baselines, backward advances, synthetic spaces and explicit advance gaps. Ligature expansions are matching evidence, not permission for global Unicode normalization. Multi-codepoint ToUnicode continuations remain tied to their source glyph. The importer then orders the actual text, vector and picture elements together. A later full-page white fill must also remain an occluding object; only the initial white page background can be omitted.

Real-PDF regressions reproduced both the visible failures and the previous false audit passes before the integration changed. Hidden, fully off-crop and unsupported paints remain distinct. This replaces the earlier dictionary-centered occurrence model described in Lesson 10; source clipping checks still fail closed.

## Lesson 17: source glyph fill and stroke are separate evidence

UCFNet's multiplication and addition operators use fill-and-stroke text. A substituted font-only text box loses the source glyph contour, stroke and placement. The bounded repair recovers the embedded glyph path and source matrix, captures the actual MuPDF text-stroke state, and emits native filled polygons. Different fill and stroke colors remain separate paint layers. Identical opaque colors can use the union contour. This is native outline editability, not ordinary character editing.

Two plausible shortcuts failed actual rendering checks. `texttrace.linewidth` retained a previous path's width in the source and was not the text stroke width. MuPDF's SVG normalizes stroke width using text scale; it did not reproduce a strongly anisotropic stroke transformation either. A real-PDF fixture showed about 7.6% painted-region error, still present at higher resolution. The implementation did not loosen the 2.5% fixture threshold or adjust the glyph by eye. It reads the actual stroke device state and explicitly rejects non-similarity stroke transforms. UCFNet's three operators use a supported similarity stroke transform with anisotropic glyph text matrices.

The supported subset is deliberately small: opaque fill/stroke, verified source occurrences, a closed single straight contour, bounded points and path data, supported joins and clips. Curves, multiple contours, ambiguous repeated matches, transparent knockout composition and unsupported transforms produce explicit errors. Ordinary text remains native text. The source `.notdef` glyph remains an unresolved mapping; restoring its visible shape never establishes a mathematical meaning.

## Lesson 18: an audit must inspect the painted result, not its declaration

The strengthened text and structural audits derive expected occurrence identities and order from the original PDF, inspect actual slide shape order, and compare native text or outline geometry and style against source-derived references. Removing a stroke, changing an outline vertex or color, deleting a badge letter, merging vertical CSV, or reordering shapes must fail even when the candidate metadata claims the correct source sequence. Ordinary font color and opacity are also checked directly against source values so a shared authoring/reference defect cannot silently certify them.

Collector failure retains the diagnostic source-label denominator and a failed status; it does not become an empty successful comparison. Unbound nontext shapes make the ordering conclusion unverified. A preserved legacy source-glyph outline can consequently leave a generic audit exception. The real figure's visual evidence, source hash, original outline XML and explicit exception remain together rather than adding hidden text or modifying provenance merely to obtain PASS.

For an already repaired delivery, replace only the affected text events and preserve established nontext native objects and media. Compare the preserved XML/media, render the actual new PPTX in an isolated directory, and inspect source/old/new views before updating the complete batch. Synthetic checks establish the mechanism; the real rendered figure establishes whether the user's visible defect was repaired. Font substitution, mixed-baseline typography and character spacing remain separate limits until directly measured and repaired.

## Lesson 19: preserving source word positions can expose a wrong font fallback

The first trace-based SkillSmith replay restored the badges but introduced a visible caption collision. The collector retained all five source word origins and their gaps; it had not dropped spaces. The source font was `NimbusRomNo9L-Regu`, an older Nimbus Roman PostScript name that the existing family mapper did not recognize. LibreOffice substituted Noto Sans. Its wider `Figure` reached 150.822pt while the next run began at 149.868pt, despite the source having a 2.491pt gap. Appending guessed spaces or moving the next word would have obscured the cause.

The existing serif-family mapping now recognizes the bounded `NimbusRomNo9L` and `NimbusRoman` aliases and maps them to Times New Roman. The alias regression failed before the change. A fresh actual PPTX export then used Liberation Serif in this Linux environment: `Figure` ended at 147.278pt and the next run began at 149.868pt, restoring a positive 2.590pt gap. The two other previously colliding caption gaps also became positive. The wrong-font render remains as a negative example. This repair establishes the caption result on the recorded export host; it does not claim universal exact typography or Microsoft Office execution.

## Lesson 20: verify that extraction APIs actually share their paint sequence

The first UCFNet source-order audit reported vectors and images at the same sequence number. Independent inspection found six empty path paints in bboxlog. The local line-art extractor returns before incrementing its counter for those paths, while bboxlog and texttrace still count them. Its later drawing numbers therefore drift from the actual source paint sequence. The image collector was already using the correct bboxlog indices. Relaxing the audit's tie ordering would have hidden a real source-order defect.

A minimal real PDF made the consequence visible: an empty stroke, then red text, then an opaque white cover. The old drawing sequence put the cover at the text's sequence; the importer placed the text on top, and the first shared audits falsely passed. The new common vector-event collector reconciles the ordered drawing records with all nonempty bboxlog path paints. It verifies paint types, complete bounds from the actual path items and total occurrence coverage. Original drawing numbers remain stable object IDs only. It does not guess an offset from the source file or library version. Zero-width hairlines are retained; only invalid/reversed empty-path bounds are omitted from that correspondence.

The six real vector-source scans all reconciled. Five had unchanged drawing order; UCFNet required corrected source numbers. Checking all path points also avoided a second extraction discrepancy: a drawing's convenience `rect` can omit an endpoint of a later subpath. These points remain present in its native line/curve/rectangle/quad records.

The line-art extractor can also merge identical fill and stroke paths across an intervening text or image paint. Such a merged record cannot be emitted faithfully as one shape. The collector explicitly rejects this case; only proven-empty intervening paths are harmless. Import, audit and private replay use the same verified source map, while the audit still examines the candidate's actual shape order. This closes the new counterexample without promoting metadata, weakening the audit or changing the original scientific content.

## Text-paint continuation verification

Before cross-version CI, the targeted local run passed **131 tests across ten suites**, followed by compilation of all twelve changed Python files and a whitespace check. The source-order negative explicitly moves the actual white cover before the red text: both source audits fail after candidate metadata is forged and again after it is removed. The result does not depend on whether a newer MuPDF version has already fixed its line-art counter. A separate actual native PPTX-to-LibreOffice export retains a blue glyph interior and red stroke ring, confirming that the PowerPoint custom geometry preserves the hole; the local renderer result is not a Microsoft PowerPoint-host test.

Final private replay re-rendered EvoOntology, SkillSmith and UCFNet with source and production-module hashes checked before and after generation. All three retain their pre-existing nontext XML and image media exactly. SkillSmith and UCFNet pass the strengthened structural and text audits. EvoOntology retains the original unmapped source glyph as native geometry, and both raw audits remain FAIL. Its text audit also records one introduced bounding-box overlap: the central white S/V source quads overlap by 2.141pt, while minimal textbox padding increases this to 2.278pt, crossing the unchanged 2.16pt threshold. Both letters and the overlap region precede the covering icon image. The raw warning is retained; it is not erased because the source image occludes the affected area. The final source-order correction also restores the UCF fusion-gradient column's outline, which its picture had covered in the earlier rendering. Remaining ordinary-text baseline and mixed-font differences stay in the visual-review record. The complete versioned ten-figure delivery and new exact-head CI evidence are recorded separately; the previous v1/v2 packages stay frozen.


## Lesson 21: a new extraction representation can be a real compatibility defect

Remote CI run #862 at `83aa86aa01bc7a60d1466cdf24ff64546eeb05f3` failed the new Type3 test under PyMuPDF 2.1 / MuPDF 1.28.6. An isolated local installation reproduced the issue without changing the private rendering environment. The same source PDF draws a black rectangle mapped to Unicode A. Version 1.26.6 exposes the native rectangle path plus an ignore-text record; version 2.1 exposes a visible Type3 text record and no drawing path. Accepting that new record as an ordinary A would lose the visible source glyph. This was a production fidelity defect, not merely an outdated expected span count.

The collector now uses actual font resources, verified `/Subtype /Type3`, source `/Name` and XRef identity to reject visible Type3 programs that it cannot reconstruct as native source geometry. It retains the older proven ignore-text/native-path representation. Independent real-PDF probes caught two initial gaps: `/BaseFont` can differ from the actual `/Name`, and an unresolved direct Type3 dictionary cannot be authorized by an unrelated ordinary font with the same name. The bounded fix does not implement a Type3 interpreter. If a direct Type3 font cannot be verified and visible logical text remains, the source is explicitly unsupported, even if that resource might be unused. Diagnostic source labels remain in the failed audit denominator.

The same version comparison showed that newer bboxlog omits empty paths as well. Three drawing tests had assumed fixed numeric indices from the old ledger. They now require the observed source text-before-cover relation, exact nonempty path occurrence correspondence and preservation of a zero-width hairline. They do not change the production drawing map, weaken geometry tolerances or skip the real paint-order negative.

Final focused validation passes **136 tests across ten suites in each of PyMuPDF 1.26.6 and 2.1**. A separate relevant integration check passes **45 tests across eight suites under 2.1**. These are repeated validation across versions, not 317 independent tests. The source-event records and statistics for the three delivered revisions are unchanged under the pinned private 1.26.6 environment. The failed remote run, wrong-glyph example and independent nine-variant review remain recorded; final publication requires a fresh successful run at the corrected public head.

## Lesson 22: compare the same source-defined ordered subset at integration boundaries

Run #864 passed the new text-paint and drawing-event suites, then failed the existing reviewed-import pipeline test. The three source objects, their identities and their classes were all preserved. Its older composition manifest assigned no paint sequence to the two text objects, so the expected ordered subset contained only the enclosing vector. The audit selected its actual subset using the candidate's own nonempty sequence metadata. The repaired importer now supplies real text sequences, making that side include three objects. The mismatch was reproducible in both supported PDF-library environments; it was not another extraction-version failure.

Both the composition audit and its quality metric must project the actual slide shape order onto the source manifest's sequenced identity set. Candidate metadata must not decide which source obligations enter the comparison. Objects without a source sequence remain explicitly outside this particular order check; missing, unexpected, duplicated and incorrectly classified objects remain separate failures. The strengthened original-PDF text audit independently checks cross-class text paint order. These distinct scopes must remain visible rather than silently expanding an older manifest's claim.

An integration fix needs both sides of the behavior: a correct candidate with richer sequence metadata must pass the same established source contract, while actually reversing sequenced shapes must still fail when candidate sequence values are removed or forged. The original pipeline assertion remains unchanged. The real failed PDF, candidate and reports are retained as negative evidence. This also explains why focused importer tests cannot replace the ordered CI pipeline: consumers of new provenance can fail even when the produced figure is correct.

An audit-only compatibility repair does not justify regenerating unchanged figures. Preserve the recorded generation commit and production-module hashes, verify that those modules are byte-identical at the final public commit, and bind the delivered artifacts to that evidence. Fresh exports are needed when the authoring path or artifact bytes change, not to replace an otherwise valid historical record with a more convenient commit label.

The final bounded integration check passes **34 tests across three suites in each of PyMuPDF 1.26.6 and 2.1**: the unchanged twenty-test reproduction pipeline, six composition-audit tests and eight quality-metric tests. The originally failed candidate and manifest pass re-audit without changing either file. Their original failure reports remain. The thirty-three later unique suites in the mandatory CI test step were also exercised from an isolated tracked-source snapshot: 220 tests passed initially; twelve text-layout tests passed after supplying the local WOFF2 decoder in a separate dependency directory. The four original missing-decoder errors are retained as environment evidence, not rewritten as an initially clean run. Only a new successful remote workflow validates the corrected public head.

## Lesson 23: a portable replay must load the dependencies it verified

The private batch's regeneration wrapper accepted an explicit repository root and checked its tool hashes, but a frozen replay module still inserted an older workspace-relative tools path during import. That path could shadow the verified dependency after the wrapper had adjusted `sys.path`. An isolated stale sibling repository containing a deliberately failing module reproduced the wrong import; a path-looking command line was not sufficient evidence of portable regeneration.

The wrapper now preloads its required public modules from the verified directory and checks their actual `__file__` locations before loading the frozen replay core. The same isolated probe then rebuilt the UCF case successfully. The final packaged entrypoint also rebuilt all three updated figures from frozen v2 inputs and the original source PDFs. Every internal PPTX member, native object XML and physical object order matched the active run04 deliverables. Outer archive timestamps can differ, so byte comparisons distinguish package-container hashes from internal member equality. No new PDF export is attributed to these regeneration checks; the delivered PDF bindings remain tied to the delivered PPTX hashes. The wrapper change is private delivery code, and no source PDF or private font is added to the public repository.


## Lesson 24: a host round-trip must compare ordered per-shape geometry, not only aggregate counts

The first PowerPoint COM acceptance script recorded slide shape counts, type counts, sorted text inventories, font-family sets and slide dimensions. Sorting text made the inventory robust to COM enumeration noise, but it also meant that a reordered pair of text objects could pass. Equal shape counts and type counts likewise cannot detect a moved, resized or rotated object.

The Office round-trip snapshot now records each top-level shape in collection order with its z-order index, name, type, left/top/width/height in points rounded to 0.01pt, rotation, text content and font family. The existing sorted text and aggregate inventories remain for readable diagnostics; the ordered per-shape snapshot is an additional structural contract. After SaveAs and reopen, the script compares this sequence and reports a dedicated ordered shape geometry/text/font snapshot difference.

This check remains deliberately scoped: it does not prove pixel-identical rendering, inspect every nested group child or certify scientific topology. The exported PDF/PNG still requires visual comparison, and the COM test must run on the actual target Windows host. Windows CI only parses the PowerShell script; it does not execute PowerPoint. Do not describe the new comparison as an Office 2016 runtime pass until a real host report is returned.

Validation to record against the new exact head: PowerShell parser CI, a synthetic reordered/moved-shape negative on a Windows PowerPoint host, and the ten-file batch round-trip report. Preserve all failed host reports rather than overwriting them.


## Lesson 25: top-level group equality does not prove nested object preservation

After adding ordered top-level shape snapshots to the PowerPoint COM round-trip check, a remaining blind spot was identified: a grouped diagram can reopen with the same single top-level group, while a child path, label, or connector inside that group is missing or reordered. The snapshot now recursively records GroupItems in their collection order, with a stable group path, type, geometry, rotation, text, font family, and nested children. Failure to enumerate a group is an explicit error rather than a silently empty child list.

The comparison therefore covers top-level z-order and nested group structure after SaveAs/reopen. It remains a structural host check, not a pixel comparison or scientific-topology proof; source-relative PDF/PNG comparison and human review remain separate. Windows CI parses the script only. A real PowerPoint COM run is still required to validate COM behavior and the ten delivered decks on the target Office installation.
