# PPT-Skill — mature-case evidence matrix and adoption decisions (2026-11-16)

## Scope and evidence discipline

This matrix separates (1) what a cited project or paper actually reports, (2) the design pattern PPT-Skill can borrow, and (3) what still requires an independent PPT-Skill experiment. Reported benchmark gains are not transferred to this repository as expected results.

## Case-by-case verification

| Proposal | Source-grounded finding | Adoption decision / correction |
|---|---|---|
| Paper2Poster / PosterAgent | NeurIPS 2025 Datasets & Benchmarks paper. The pipeline has a Parser that builds a structured asset library, a Planner that aligns text/visual pairs in a binary-tree layout, and a Painter–Commenter visual feedback loop. The authors report an editable PPTX poster and 87% fewer tokens than the compared GPT-4o-based workflow. Author affiliations are University of Waterloo, University of Oxford and Vector Institute — **not CMU**. | Borrow structured intermediate assets, explicit layout planning and render-feedback separation. The paper does not specify a universal SVG + DrawingML dual-writer AST; that is our architecture adaptation, not a claimed Paper2Poster feature. |
| PPTAgent / PPTEval | EMNLP 2025. PPTAgent extracts slide functional types and content schemas from reference presentations, then uses an edit-based workflow and selected reference slides. PPTEval evaluates Content, Design and Coherence. | Borrow reference-slide retrieval/edit actions and the three-axis external evaluation mapping. Do not replace source-evidence and scientific-topology checks with aesthetic similarity. |
| Anthropic official pptx skill | The official `anthropics/skills` repository contains `skills/pptx/scripts/office/soffice.py` and `validate.py`, plus schema and validator directories. | Borrow headless LibreOffice rendering and OOXML/package validation. Make the pinned Linux renderer the canonical CI visual baseline; retain PowerPoint 2016 host round-trip as a separate compatibility acceptance test. |
| PosterGen | arXiv:2508.17188 describes a Layout Agent and a CSS-like box model. Its text-frame algorithm binary-searches the minimum textbox height using a simulated rendering/overflow check, then adds a newline-dependent correction. It explicitly requires WCAG 4.5:1 text contrast and uses headless LibreOffice to render final PNGs. | Borrow render-grounded height calibration, whitespace/margin/padding modelling and contrast checks. **The paper does not report using fontTools hmtx/OS/2 tables**; fontTools metrics will be our fast estimate, with LibreOffice used for calibration. |
| P2P / P2Peval | ICLR 2026. P2Peval reports 1,738 human-annotated checklist items and dual evaluation (fine-grained source fidelity plus universal/holistic quality); P2Pinstruct contains 30,000+ examples. | Borrow machine-checkable source checklists and separate objective fidelity from subjective visual quality. Our checklist must be derived from source claims and must not be self-authored from the generated slide alone. |
| DECKBench | KDD 2026 Datasets & Benchmarks. Official release reports 294 paper–slide pair URLs, a paper-to-slide task and a multi-turn editing task, user simulation personas, and slide-/deck-level metrics including faithfulness, text/figure similarity, layout quality, DTW and transition similarity. | Build an adapter and report comparable metric definitions on the common supported subset. Preserve our native-PPTX, scientific evidence and Office-host tests as additional dimensions; DECKBench's HTML/Reveal.js baseline is not a drop-in renderer. |
| ConvDeck | Accepted to Findings of EMNLP 2026. It places conversational refinement at both outline and slide stages, routing feedback to the stage that owns the decision. | Adopt stage-specific human gates and feedback capture at DeckSpec/outline, FigureSpec/topology and rendered Stage A. Treat the paper's reported satisfaction gains as its own evaluation, not a guaranteed PPT-Skill effect. |
| Template Deck Builder / ppt-master | The public `hugohe3/ppt-master` Create Template workflow confirms a template brief before authoring and distinguishes Brand, Style, Layout and Deck workspaces. Layout/Deck workspaces contain SVG prototypes plus a `design_spec.md` and can be validated before handoff. | Promote template/style bundles to first-class assets with explicit scope, schema and user approval. Do not copy a template's branding or sample content into scientific figures without source permission. |
| Aki2022 skills | The public `Aki2022/skills` repository currently exposes `own-pptx-build`, a template-based skill with `style-guide/tokens.json`, `template_v3.pptx`, and mandatory human approval gates in its ⓪–⑤ pipeline. The specific `style.yaml / template.crtx / processing/snapshot / timestamp.txt` combination in the recommendation was **not located in the current repository tree**. | Borrow the verified token/template bundle and approval-gate pattern. Treat the exact snapshot-file recipe as unverified until a concrete source path/commit is supplied. Implement our own content-addressed build snapshot from verified artifacts. |
| agent-slides v2 | The public `mpuig/agent-slides-v2` repository exposes Pydantic models, a machine-readable `contract` command, structured JSON errors, revision-conflict checks and staged/atomic file writes for batch mutations. The multi-file commit helper renames staged outputs sequentially, so the source does not prove rollback of every already-renamed file if a later rename fails. The often-quoted “160 tests” count was not independently confirmed from the current repository snapshot. | Adopt runtime schema introspection, strict validation, dry-run, structured errors and staged writes. For PPT-Skill, implement a true transaction journal or atomic directory swap for multi-artifact outputs rather than copying the rollback claim uncritically. |
| PASE | arXiv:2611.14019 (submitted 2026-11-10) separates natural-language skill strategy from linked executable programs and accepts/rejects patches using held-out validation. Its reported experiments are spreadsheet/TableQA tasks, not presentation generation. The paper says code/data will be released. | Adopt the separation and held-out patch-acceptance concept for Skill evolution. Do not treat the paper as direct evidence of improved PPT generation or a ready-to-vendor implementation. |

## Priority translation to PPT-Skill

### P0 — deterministic engineering substrate

1. **Canonical Figure AST + independent writers.** Current FigureSpec is already a typed JSON element list, but the production renderer still interleaves SVG and python-pptx emission in one loop. Introduce an immutable, backend-neutral AST and separate SVG/DrawingML writer APIs. Migrate by parity-tested vertical slices; do not replace existing V7/V8 render paths until object and visual parity are demonstrated.
2. **Canonical LibreOffice renderer.** Pin the CI runner family, LibreOffice/Poppler versions, locale, fonts and font-file hashes. Produce PDF/PNG plus a content-addressed render record in Linux. PowerPoint 2016 remains a separate host compatibility gate, not the only visual source of truth.
3. **Text metrics and render-calibrated fit.** Use fontTools hmtx/OS/2 for a fast estimate, then use a headless render probe/binary search for final textbox-height calibration. Preserve authored font sizes by default; expand within a declared layout budget or fail with a suggested fix rather than silently shrinking text. Enforce WCAG 4.5:1 for ordinary text, with the applicable large-text exception documented.

### P1 — measurable scientific and external fidelity

4. Dataset records in FigureSpec: source URI, SHA-256, selected columns, filters, aggregation, units, missing-value policy, bootstrap seed/resamples and expected statistics.
5. A source-derived, machine-checkable fidelity checklist for each task; keep checklist authoring independent from the generated slide.
6. DECKBench/PPTEval adapter with explicit protocol/version and comparable-subset reporting. Add Paper2Poster PaperQuiz-style comprehension checks where source paper and generated slide pair are available.
7. Three user gates: DeckSpec/storyline; FigureSpec/topology/evidence; Stage-A visual candidate. Stage B remains locked until Stage A approval; final PPTX requires its own final acceptance.

### P2 — reliability and reuse

8. Per-build immutable snapshot: source specs, template/style bundle, font manifest, renderer profile, dependency versions, output hashes, audit logs and repair diffs.
9. Agent-safe CLI with runtime JSON schemas, Pydantic validation, dry-run, atomic writes/rollback and stable structured errors.
10. Template library for defense, group meeting and conference styles. A C01 two-panel method layout may seed a *layout archetype*, but must be separated from C01's scientific content and validated on unseen figures.
11. Programmatic Skill evolution: procedural logic in versioned modules; natural-language Skill docs explain intent; patches are accepted only when regression and held-out benchmark scores improve.

## External sources

- Paper2Poster / PosterAgent (NeurIPS 2025): https://arxiv.org/abs/2505.21497 ; https://github.com/Paper2Poster/Paper2Poster
- PPTAgent / PPTEval (EMNLP 2025): https://aclanthology.org/2025.emnlp-main.728/
- Anthropic official pptx skill: https://github.com/anthropics/skills/tree/main/skills/pptx
- PosterGen: https://arxiv.org/abs/2508.17188
- P2P / P2Peval (ICLR 2026): https://proceedings.iclr.cc/paper_files/paper/2026/hash/1fe6f635fe265292aba3987b5123ae3d-Abstract-Conference.html
- DECKBench (KDD 2026): https://arxiv.org/abs/2602.13318 ; https://github.com/morgan-heisler/DeckBench
- ConvDeck (Findings of EMNLP 2026): https://arxiv.org/abs/2609.00226
- ppt-master: https://github.com/hugohe3/ppt-master
- Aki2022 skills: https://github.com/Aki2022/skills
- agent-slides: https://github.com/mpuig/agent-slides-v2
- PASE: https://arxiv.org/abs/2611.14019
