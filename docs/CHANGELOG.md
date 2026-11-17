- Extended Blind10 batch-runner tests to prove that one paper's importer exception does not abort the other nine and that source-picture-only routing is explicitly limited to Wind Turbine, HarnessMM and IIoT while the remaining seven require native editable import.
- Verified the Blind10 post-P0 batch runner increment with CI #842: Linux validation and compile passed; Windows PowerShell parser passed; optional PP-DocLayoutV3/PP-OCRv6 inference remained skipped. Recorded that mocked CI is not a substitute for the private-source ten-PDF execution.
- Added a frozen Blind10 post-P0 batch runner with per-paper output isolation, immutable output-directory protection, source-picture-only routing for image-backed source crops, per-case exception capture and explicit separation of technical status from scientific/Office acceptance. Added mocked regression coverage and CI integration.
- Added fail-closed regression tests for Blind10 source admission (missing source, hash mismatch, invalid crop/page and missing caption) and wired them into the main validation workflow. Recorded the evidence boundary: source preflight is not figure-reproduction acceptance; the inspected ten-paper cohort remains development regression only. See `docs/DEVELOPMENT_EXPERIENCE_2026-11-17.md`.

# Changelog

- Corrected FigureAST corpus result classification: contrast/text-fit preflight findings now produce REVIEW rather than a false clean PASS; rendered calibration/parity failures remain FAIL. Corpus summaries report PASS, REVIEW and FAIL/ERROR separately. Recorded the U-Net rotated-dimension-label calibration gap as unresolved rather than weakening text matching.

- Corrected the literature-corpus provenance boundary: source PDFs excluded from Git are represented by canonical arXiv URLs plus ingest-time SHA-256 records (format-checked, not falsely claimed as recomputed in CI); the committed CLIP CC0 replacement asset remains byte-hash verified.

- Preserved source identity for legacy Mamba/Swin FigureSpecs that intentionally omit a top-level id: corpus IDs remain external experiment keys, while existing paper metadata and canonical source hashes are validated without mutating the original specs.

- Added a six-paper source-backed FigureAST corpus (Mamba, Swin, GAT, CLIP, ResNet, U-Net). Core semantic/source-provenance tests remain hard gates; legacy-vs-AST visual parity is a non-blocking experiment with retained per-paper artifacts. The legacy baseline is rebuilt from the same FigureSpec before comparison, and CLIP's CC0 replacement image is explicitly disclosed.

- Fixed the V8 committed-manifest content-lock drift by refreshing the FigureSpec SHA-256 from the final committed source file (the topology hash and semantic fields were already current). The validator now names exact stale source-lock fields and writes a machine-readable failure report; CI uploads it at the first manifest gate. Reduced redundant feature-push runs, enabled PR-base validation for feat/*, concurrency cancellation and manual dispatch; related source, lock, test, workflow and experience updates are delivered as one commit.

## V7.6.0-dev — Scientific evidence and data channels
- Rechecked C01 against the author-lab graphical abstract, added explicit band-pass and OCF-effect labels, replaced the star aggregation sketch with connected frequency-band layers, and drew the total-graph-to-SEANet input route. The publisher high-resolution image was not directly accessible; earlier claims of publisher-image inspection are retracted. PowerPoint refreshes every deck PNG alongside PDF export.
- Corrected C01's EA and lower-readout routing and restored Dense classification using the author-lab source image and public abstract. Preserved the author-lab visible IR layer label while disclosing the unresolved SR wording in the public abstract. Added source-like pooling quadrilaterals, visible-route checks, editable output squares and explicit source-evidence boundaries.
- Split independent review into separately distributable initial and reconciliation archives; the initial packet contains no benchmark expectations, FigureSpecs or review template, and CI uploads the stages as separate artifacts.
- Recorded canonical hashes of all direct builder, renderer, data-contract, PowerPoint export and render-audit sources; render-record validation now rejects a stale generation pipeline across Windows/Linux line endings.
- Required quantitative data-lineage fields in the FigureSpec schema and checked the embedded chart and source metadata against the exact hashed ChartSpec; mismatched statistics or sample counts now fail mutation tests.
- Bound each quantitative FigureSpec to a canonical ChartSpec content hash and the independent review template to each raw ChartSpec file hash; stale chart configurations now fail validation and release review.
- Migrated five existing FigureSpecs to an evidence-linked contract with typed elements and stable IDs.
- Added directed-route checks and negative mutations for the C01 critical diagnosis topology.
- Added six reproducible UCI Iris charts with row-level lineage, statistics definitions, SVG/PPTX/PDF outputs and validation, including paired ablation and trend/interval cases.
- Added a CC0 quantitative-phase image plus raw-pixel histogram, with source hash, processing log, calibration and scale-bar checks.
- Added CI build and validation for the new examples. Independent domain and final-size review remains pending.
- Added a glyph-level PDF text-fit calibration gate for the independent-paper FigureAST corpus, including per-codepoint fallback-font resolution, glyph-outline bounds, page-wide character matching, explicit multiline baseline matching and whitespace-loss-safe token boundaries. Added regression coverage for adjacent text boxes, fallback subscripts, floor/ceiling symbols, multiline labels and partial-word false matches; CI preserves calibration diagnostics on failure.
- Passed the cross-paper FigureAST + LibreOffice + glyph-calibration gate on Mamba Figure 1 and Swin Figure 2: 57/27 AST nodes, 70/56 native PPTX shapes, zero picture objects, zero changed pixels, 24/24 text matches and zero rendered text overflow in CI #752. Kept the legacy renderer as production default pending broader primitive/corpus gates and real Office 2016 host validation.
- Added advisory pre-build FigureSpec text-fit and WCAG contrast estimates to the independent-paper AST pilot, recording the binary-searched minimum frame height and additional height required without mutating authored geometry. The search ceiling now scales with text length and selected font line height, avoiding missing recommendations for long labels in narrow boxes.
- Calibrated pre-build height estimates against rendered glyph ink: single-line demand now uses selected glyph-outline extents while multi-line demand retains inter-baseline spacing. The Mamba/Swin pilot reports 0/24 estimated text overflows, 0 contrast failures and 24/24 post-render text matches with zero actual overflow.
- Replaced the C01 B₃/B_N continuation glyph with three editable native ellipse marks after CI showed that the fallback glyph could not fit the constrained topology gap without violating the presentation minimum text size. Kept the topology-gap test and strict rendered-glyph calibration as independent gates.
- Darkened only the four C01 frequency-band text labels to meet the 4.5:1 normal-text contrast target while preserving the band hue families and leaving graph fills/signal traces unchanged. Added direct contrast regression checks for V4.1 and V8, and refreshed the Image-first source-figure hash lock.
- Restored source fidelity in the C01 class-output region: removed five unsupported C₁–C₅ text labels, retained and centered the five source-visible squares, and bound the unlabeled-output rule into the topology contract and regression test.
- Applied the same unlabeled-output correction to C01 Image-first V8: removed the builder-generated C₁–C₅ annotations, kept the five source-visible squares and separate caption, refreshed the topology and Image-first source-figure content lock, and added a regression test. Restored the V4.1 caption to the 9.5 pt presentation minimum by widening and aligning its frame instead of shrinking type.
- Added exact parity coverage between the V8 builder output and its committed FigureSpec; the builder now emits the unlabeled-output contract, and the Image-first workflow manifest lock is regenerated from the updated figure and topology hashes.
- Refreshed SHA-256 in every active C01 FigureSpec EvidenceRecord after updating the shared source record, and documented the required source-file → hash → all-dependent-FigureSpecs update order. The scientific IR provenance validator remains fail-closed.
- Added a Nature two-column publication-size Q03 demonstrator with the same rows/statistics as the presentation panel, final-size PDF geometry and embedded-font checks; CI now verifies committed PowerPoint export records and SVG/PPTX/PDF labels without forging a Linux exporter claim.
- Recorded observed PDF font names and embedding for all ten Windows-exported research figures, including Type 0 composite fonts, and checked them against the requested font family.
- Added coordinate audits that recompute raw-point positions, summary markers and ablation bar heights from source rows and statistics; displaced points and bars now fail negative tests.
- Added a release-readiness command that requires independent per-task review evidence and current artifact hashes; development CI tests the gate with synthetic data but does not fabricate reviewer approval.
- Checked chart text against the colored shape underneath it, including confusion-matrix cells and ablation bars; a low-contrast cell mutation now fails.
- Clarified SKILL.md routing, output-mode boundaries and a seven-step workflow with explicit stop conditions for unsupported claims and unreleased review gates.
- Audited displayed bootstrap whisker endpoints against computed intervals for presentation and publication figures; moved-endpoint mutations now fail.
- Verified that I01's drawn scale bar, histogram bar geometry and printed threshold summary match the raw image and declared calibration; scale-bar and histogram mutations now fail.
- Added a portable, unfilled 15-task review bundle generator for independent source and final-size inspection.
- CI now uploads that unfilled bundle as a separate artifact after all automated figure checks.
- Render records now hash canonical SVG XML and PPTX member payloads, so CI detects geometry or style drift while ignoring ZIP timestamp/order noise.
- Stratified benchmark tasks by five disciplines and required each task's independent reviewer to declare matching field expertise.
- Bound release reviews to every required visual artifact, including PDFs and accessibility previews, rather than only the editable PPTX; missing or changed outputs block release.
- Added explicit numeric-axis domains, zero policies and zoom reasons to six chart contracts; validation rejects missing transformation logs and source values clipped by declared axes.
- Separated Q01's 48 coincident Iris observations with bounded, disclosed display-only offsets; all 150 native points now have distinct visible centers while retaining unmodified source values.
- Separated close raw points in Q02, Q03, Q03P and Q06 with bounded, disclosed offsets and geometry checks; moved Q03 summary marks beside each group so they do not cover observations.
- Excluded Q06's five summary markers from the raw-point packing area; geometry validation now rejects a summary marker covering any raw observation.
- Split the independent review bundle into first-stage source/render inspection and second-stage benchmark/spec reconciliation; the release gate now requires task-level initial-review evidence instead of claiming complete version blindness.
- Anchored all six independent-review scores with concrete criteria and blocked release when any dimension scores below the declared floor, even if the reviewer marks the task passed.
- Declared Q04 prediction/actual labels and Q05 feature-set/accuracy measures as derived fields with source columns, units and calculation rules; missing or inconsistent derivations now fail contract validation.
- Bound Q04/Q05 to a structured leave-one-out 1-NN algorithm contract, including tie handling, feature scaling and exact compared feature sets; builder and output checks now consume those fields. A hand-computed tie fixture and frozen Iris confusion/accuracy values detect algorithm drift.
- Added source-file hashes and local locators to every FigureSpec EvidenceRecord; validation now catches stale local evidence while distinguishing a hashed evidence ledger from publisher artwork that is not redistributed.
- Rechecked Nature's current main-figure guide and made figure class, maximum height, guide-check date and preferred submission format explicit in the publication target; the Q03 demonstrator remains pending actual-size and editorial review. The publication caption is now a hash-locked review artifact.
- Validated Q01's visible legend against source-group labels, colors and native symbol shapes, and checked visible category/numeric ticks on all six Iris charts and Q03P against their coordinates; label swaps now fail negative tests instead of silently misidentifying observations.
- Expanded the second-stage independent-review packet to include the source data, chart specifications, builders and validators, so reproducibility can be checked from the extracted archive.
- Added a 3:1 project preflight for essential chart marks and lines on white plots; darkened Q06 raw observations from 2.18:1 to 3.51:1 against the background, with a low-contrast mutation test.
- Extended the 3:1 preflight to the visible arrows in the five schematic FigureSpecs, with a low-contrast C01 connector mutation test.
- Added a requirement-by-requirement V7.6 completion audit that distinguishes machine-verified clauses from independent final-size review still needing evidence.
- Compared the five migrated figures' labels against their pre-V7.6 committed FigureSpec/SVG files and the three committed C01 PPTX files; stabilized text-source hashes across Windows and Linux checkouts.
- Added UCI Wine as a second real dataset and an analytical-chemistry benchmark task. Its 178 source-linked points reproduce to SVG, native PPTX and PowerPoint PDF, with both numeric axes disclosing that the source does not report physical units. The shared data loader, scatter and distribution placement now have cross-dataset evidence; four other chart kinds remain Iris-only.
- Added a dataset-independent ChartSpec validator for sample counts, axes, source/derived fields, category coverage and bootstrap definitions, with mutation checks on both Iris and Wine.
- Reused the categorical beeswarm placement for a second UCI Wine distribution figure. Both Wine plots preserve all 178 source rows in SVG/PPTX/PowerPoint PDF; the single Q07 benchmark task hashes both figures and both FigureSpecs without exposing specs in the first-stage blind packet.

## V7.5.0-dev — Deck planning and V7.4 source closure
- Added DeckSpec, SlideSpec and SourceStyleSpec planning contracts and validation.
- Committed a reproducible V7.4 composite FigureSpec, SVG, PPTX and PowerPoint-exported PDF.
- Added C01 semantic path checks and CI build/audit coverage for the composite.
- Fixed the shared renderer's grid branch so PPTX grid shapes are emitted alongside SVG grid geometry.
- Kept the branch as a draft prototype pending source overlay and independent review.

## V7.3.0 — C01 source-matched FigureSpec
- Located the author-published FBG-SEANet graphical abstract.
- Rebuilt the two source panels as editable vector slides.
- Removed unsupported frequency-response waveforms and invented downstream classifier/representation boxes from V7.2.
- Restored the GCN/pooling main path and parallel EA/SR path converging at the summation node.
- Added editable sensor, graph, trapezoid, polyline and ellipse primitives.
- Added C01 build and validation scripts.
- Recorded source boundaries and remaining pixel-overlay / Windows PowerPoint validation gaps.

## V7.2 — C01 decomposition and scientific-boundary cleanup
- Split C01 into frequency-band graph construction and graph-level representation slides.
- Separated the EA branch from the GCN/pooling/SR path.
- Added explicit evidence boundaries for unverified graph topology and EA fusion.

## V7.1.1 — FigureSpec dual-render pilot
- Fixed state-description overlaps and default theme shadows.
- Replaced the 40×40 rectangle matrix with line geometry.
- Added deterministic FigureSpec rendering for B01 and F07.
