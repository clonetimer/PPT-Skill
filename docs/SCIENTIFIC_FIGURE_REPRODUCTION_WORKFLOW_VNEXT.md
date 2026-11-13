# Scientific figure reproduction workflow — development

## Two distinct routes

**Source-visible PDF import:** preserves a paper author's vector paths, labels, paint order, photo objects and layout, but does not automatically infer a semantic FigureSpec.

**FigureSpec scientific reconstruction:** starts with source-grounded scientific relations and a manually verified FigureContract / ScientificIR, then generates editable objects. It may intentionally relayout the paper and is not a pixel-level source copy.

Run the same technical gates on both routes, while preserving the different scientific evidence classes. Every result includes source hashes and a manifest, and explicitly marks scientific review and Office 2016 host inspection as separate requirements.

## One-command pipeline

~~~bash
python tools/reproduce_research_figure.py source.pdf --output dist/figure-recovery --mode import --render-host auto

python tools/reproduce_research_figure.py source.pdf --output dist/figure-figurespec --mode figurespec --figure-spec figure_specs/figure.json --render-host auto
~~~

Outputs include candidate_editable.pptx, source_preflight.json, quality_report.json, office2016_ooxml_preflight.json and delivery_manifest.json. If LibreOffice is installed, a rendered PDF and comparison PNG are also generated. Without an export host, visual review remains pending. FigureSpec mode does not run literal PDF text-span parity; it requires independent scientific topology verification.

## Real Windows PowerPoint 2016 evidence

On a Windows computer with PowerPoint 2016, put the PPTX files in a dedicated input folder and run:

~~~powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\windows\Test-PowerPoint2016RoundTrip.ps1 -InputDirectory 'C:\PPT-Figures\input' -OutputDirectory 'C:\PPT-Figures\office2016_qa' -RequireOffice2016
~~~

The script opens the files, saves new PPTX copies, exports PDFs/PNGs, reopens saved files, compares slide object counts/text, records font families and SHA-256 values. Version 16.0 alone does not establish Office 2016 because Microsoft 365 also uses it. MSI installations without an identifiable product marker require manual About PowerPoint inspection.

STRUCTURE_PASS means only COM open/save/reopen structural preservation. It does not certify glyph rendering, line clipping, image crop, readability or scientific accuracy; manually compare the exported PNG/PDF to the source figure.

## Cross-family testing and real first-shot metrics

tools/test_unseen_figure_families.py constructs three deterministic, *synthetic* PDF fixtures: a multi-panel ablation/trend/error-bar composition, a colored graph with hyperedge enclosures, and a statistical observations/box/whisker composition. Passing the importer and object audit demonstrates cross-grammar converter regression only. It is **not** a measured first-shot success rate on independently sourced scholarly articles.

For a genuine held-out paper set, freeze all input PDFs, software hashes, source-derived scientific edge and number contracts, rubric and output host BEFORE first export. Save first-attempt outputs and independent review scores without replacing them. First-pass rate is the number passing full science, visual, editing, rights and final-size gates on the initial output divided by the frozen hold-out sample count. Iterative corrections must never be counted as a first-pass pass.

## Release boundary

Technical-pass status alone cannot grant scientific or Office 2016 runtime approval. Keep independent domain/final-size and target-host checks as release gates.
