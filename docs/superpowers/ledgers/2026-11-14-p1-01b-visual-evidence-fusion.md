# P1-01B Visual Evidence Fusion — Execution Ledger

**Plan:** [2026-11-14-p1-01b-visual-evidence-fusion.md](../plans/2026-11-14-p1-01b-visual-evidence-fusion.md)  
**Design:** [2026-11-14-p1-01b-visual-evidence-fusion-design.md](../specs/2026-11-14-p1-01b-visual-evidence-fusion-design.md)  
**Working branch:** `feat/mmgraph-agent-figure-fidelity-20261113`  
**Review:** [Draft PR #10](https://github.com/clonetimer/PPT-Skill/pull/10)

## Preflight and design decisions

- Existing P1-01 already produces hash/caption-grounded figure crops and native PDF object inventories. P1-01B therefore adds internal visual evidence rather than replacing the existing source parser.
- Official model check selected PaddleOCR's PP-DocLayoutV3 (Apache-2.0, approximately 132 MB) with PP-OCRv6 small detection/recognition and ONNX Runtime. The third-party PP-DocLayout-S adapter and figcrop's AGPL implementation/weights are not vendored.
- The base workflow remains model-free. Explicitly selecting `--vision-backend paddleocr` is required to load models.
- Model outputs are candidates only. Source PDF objects remain the authoritative geometry/paint-order inventory; OCR alone cannot create a confirmed panel or semantic edge.

## Task status

### Task 1 — Pure visual evidence normalization and fusion

**Implemented.**

- Raster pixel boxes map to the selected PDF-point crop using actual raster dimensions.
- Layout detections and OCR tokens are normalized into stable candidate records.
- Nested regions, OCR-to-region hypotheses, horizontal/vertical alignment groups, and conservative source-object ownership are generated.
- Objects crossing sibling regions are assigned only to the enclosing container; ambiguous or uncontained ownership remains unresolved.
- Deterministic tests cover coordinate drift, malformed boxes, marker parsing, nesting, alignment, and ownership.

### Task 2 — Optional PaddleOCR backend

**Implemented.**

- Lazy-loaded official PaddleOCR models and ONNX Runtime adapter.
- Model initialization and inference failures are explicit; no silent fallback.
- Optional dependencies are isolated in `requirements-vision.txt`; model weights are not committed.
- CI uses mocked model classes and does not download model weights.

### Task 3 — SourceLayout integration

**Implemented; validation is in the current CI sequence.**

- Added `vision_backend`, DPI, and maximum-raster-side options to the extractor and CLI.
- The exact selected crop is rasterized with bounded dimensions, then model coordinates are mapped back to the same PDF region.
- SourceLayout output is version 1.1.0 and records model/runtime provenance, region proposals, OCR markers, hypotheses, alignment groups, and source-object ownership.
- Existing version 1.0.0 schema/review inputs remain accepted.

### Task 4 — Human review integration

**Implementation added; CI verification remains the gate.**

- Visual regions, label-anchored hypotheses, and alignment groups are exposed as review candidates.
- Raw OCR markers are intentionally not review candidates.
- Human review is required to accept a visual region as a panel.
- Alignment groups cannot be accepted as a single panel.
- Visual region splitting creates geometric child regions only.

### Task 5 — Documentation and cohort replay

**Documentation added; local model replay remains a separate validation activity.**

- README and P1-01B user guide describe the optional environment, CLI, output interpretation, and review boundary.
- CI tests remain deterministic and model-free.
- The ten-paper cohort is a development set after the original blind test; any replay must report human-reviewed candidate precision/recall separately and must not rewrite the frozen strict first-pass result.

## Acceptance boundary

- Passing deterministic CI does not prove PP-DocLayoutV3 inference quality on the ten papers.
- No strict blind-test score improvement is claimed; frozen first-pass baseline remains **0/10**.
- Actual model-weight inference, human-reviewed ten-paper replay, independent scientific review, and native PowerPoint 2016 host round-trip remain separate release gates.
