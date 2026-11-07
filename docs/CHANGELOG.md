# Changelog

## V7.6.0-dev — Scientific evidence and data channels
- Migrated five existing FigureSpecs to an evidence-linked contract with typed elements and stable IDs.
- Added directed-route checks and negative mutations for the C01 critical diagnosis topology.
- Added six reproducible UCI Iris charts with row-level lineage, statistics definitions, SVG/PPTX/PDF outputs and validation, including paired ablation and trend/interval cases.
- Added a CC0 quantitative-phase image plus raw-pixel histogram, with source hash, processing log, calibration and scale-bar checks.
- Added CI build and validation for the new examples. Independent domain and final-size review remains pending.
- Added a Nature two-column publication-size Q03 demonstrator with the same rows/statistics as the presentation panel, final-size PDF geometry and embedded-font checks; CI now verifies committed PowerPoint export records and SVG/PPTX/PDF labels without forging a Linux exporter claim.
- Recorded observed PDF font names and embedding for all nine Windows-exported research figures, including Type 0 composite fonts, and checked them against the requested font family.
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
- Added UCI Wine as a second real dataset and an analytical-chemistry benchmark task. Its 178 source-linked points reproduce to SVG, native PPTX and PowerPoint PDF, with both axes disclosing that the source does not report physical units. The shared data loader and scatter placement now have cross-dataset evidence; other chart kinds remain Iris-only.
- Added a dataset-independent ChartSpec validator for sample counts, axes, source/derived fields, category coverage and bootstrap definitions, with mutation checks on both Iris and Wine.

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
