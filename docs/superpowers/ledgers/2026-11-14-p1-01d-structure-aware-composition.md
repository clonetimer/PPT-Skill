# P1-01D Execution Ledger

- Reused the existing PDF importer rather than building a second importer.
- Added a source-object inventory and route-to-object composition manifest.
- Kept image, vector, and text treatments separate for mixed regions.
- Preserved PDF source order and recorded text spans without paint-order indices separately.
- Added shared-boundary object detection; multi-region objects are recorded once and block execution.
- Added hash consistency checks across SourceLayout, human review, and route evidence.
- Added deterministic regression tests and wired them into standard CI.
- Actual PPTX provenance annotations and expected-vs-actual output audit are deferred to P1-01D2.
- No FigureSpec or scientific topology changes; execution authorization remains false.
