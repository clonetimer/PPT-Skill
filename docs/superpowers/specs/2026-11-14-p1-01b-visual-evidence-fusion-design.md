# P1-01B Visual Evidence Fusion for Raster and Nested Panels

**Date:** 2026-11-14  
**Status:** Implementation baseline; design decisions are maintainer defaults for this continuation.

## Intent

Extend SourceLayout so the ten-paper development cohort's raster-backed and nested figure structures can be proposed from visual evidence, while retaining the existing PyMuPDF-native inventory, source hashes, conservative human review, and FigureSpec safety boundary.

The immediate problem is not figure-page localization: the crop manifest is already hash- and caption-verified. The remaining gap is internal panel evidence when labels or boundaries are embedded in raster images, nested, or absent from the PDF's vector drawing records.

## Goals

1. Add an opt-in visual backend based on official PaddleOCR components:
   - PP-DocLayout-S for broad visual-region proposals.
   - PP-OCRv6 small detection/recognition for panel-marker candidates embedded in raster content.
   - ONNX Runtime inference where supported.
2. Convert every model coordinate back to the exact selected PDF crop in PDF points; retain model name, version, score, DPI, image dimensions, and warnings as provenance.
3. Fuse proposals with the existing PDF drawing/text/image inventory, geometric enclosures, raster gutters, and alignment evidence.
4. Produce explicit parent/child region hierarchy, marker-to-region hypotheses, and conservative source-object ownership assignments.
5. Keep all model output review-only. Only a human reviewer may accept, reject, or split candidates. A panel acceptance is a source-layout fact, not a scientific edge or causal relation.
6. Keep the default extractor free of PaddleOCR and model-weight dependencies.
7. Preserve compatibility with existing SourceLayout 1.0.0 review files and existing native-only workflows.

## Non-goals

- Do not infer directed graph edges, causal relationships, or scientific meaning from visual geometry or OCR alone.
- Do not move FigureSpec scientific nodes/connectors. Existing reviewed-geometry bindings remain limited to decorative frames/visual containers.
- Do not make the visual model mandatory or download weights during ordinary extraction.
- Do not vendor or import figcrop source code or its AGPL-licensed PP-DocLayoutV2 weights.
- Do not recompute the frozen ten-paper strict first-pass score. The ten papers remain development inputs.
- Do not claim Office 2016 or visual-fidelity acceptance from schema tests or model detections.

## Approaches

### A. Integrate figcrop directly

Rejected for this repository increment. Its ownership/contact-graph and paint-order concepts are relevant, but the project is AGPL-3.0-only and its bundled PP-DocLayoutV2 weights are separately identified as AGPL-3.0. Directly vendoring it would create a license decision unrelated to the technical goal. The repository is also marked Alpha.

### B. Official PaddleOCR models plus the existing PyMuPDF pipeline — selected

Use PaddleOCR's Apache-2.0 PP-DocLayout-S and PP-OCRv6 small models as optional proposal engines. Keep PyMuPDF as the source-of-truth extractor. Implement the evidence fusion and source-object ownership logic inside PPT-Skill, without copying third-party implementation code.

Trade-offs: optional model installation and first-run weight download are required; detections remain proposals and may miss or over-segment scientific subpanels. This is preferable to coupling the project to an AGPL tool or pretending a general document detector is a scientific panel parser.

### C. Continue pure geometric heuristics

Rejected as the sole path. It remains useful as one evidence source, but cannot reliably recover panel labels embedded in raster images or internal regions with no vector boundaries.

## Architecture

### 1. Optional backend boundary

Add `tools/source_layout_vision.py` with a stable, model-independent result contract. The PaddleOCR adapter is loaded only when `--vision-backend paddleocr` is requested. The default remains `none`.

- Layout model: `PP-DocLayout-S`.
- OCR models: `PP-OCRv6_small_det` and `PP-OCRv6_small_rec`.
- Preferred engine: `onnxruntime`, where supported by the installed PaddleOCR release.
- Initial supported optional runtime: Python 3.11 or 3.12. The base project must remain usable without this runtime.
- Model weights are cached by PaddleOCR; no model binary is committed to Git.
- Use a bounded rasterization DPI (default 180) and maximum image dimension to prevent uncontrolled memory use.

### 2. Coordinate contract

The model receives a rasterized image of the exact selected figure region. All output coordinates are mapped back to PDF points using the actual raster width/height and the selected PDF region, not an assumed nominal DPI. Invalid, non-finite, or out-of-region detections are discarded with diagnostics.

### 3. Evidence fusion

The fusion layer combines:
- native PDF text spans and panel-marker OCR;
- layout model boxes for figure/image/table/algorithm-like regions;
- source PDF drawing rectangles and stroke geometry;
- dominant image XRef bounds and low-ink gutters;
- repeated alignment and spacing;
- source-object containment and overlap.

Each visual candidate records its evidence references, model score, heuristic evidence score, candidate type, parent region, and review status. The evidence score is explicitly a heuristic, not a calibrated probability.

Candidate hierarchy is derived from strict containment. Duplicate/near-identical detections are merged only when their geometry and class evidence justify it. Objects that overlap multiple candidate regions or have ambiguous ownership remain unresolved; no forced assignment is allowed.

### 4. Review and downstream use

Extend the review candidate index to include visual regions, OCR-anchored region hypotheses, and visual alignment groups. A human may accept a visual region as a panel only after recording a rationale and source locator. OCR markers alone and raster gutters cannot be promoted to panels.

Accepted regions/panels are compiled through the existing hash-locked constraints pipeline. Existing FigureSpec geometry bindings may target only decorative frames/visual containers. Scientific nodes, labels, and semantic edges remain unchanged.

Route selection remains advisory. This increment records panel-level ownership evidence; P1-01C/P1-02 will consume only human-accepted facts for panel-specific native/mixed/raster route decisions.

## Schema and compatibility

- Bump SourceLayout schema to `1.1.0` with optional `visual_evidence`, `visual_region_candidates`, `ocr_panel_markers`, `panel_hypotheses`, `visual_alignment_groups`, and `source_object_ownership`.
- Keep review schema at `1.0.0`; validate SourceLayout 1.0.0 and 1.1.0 inputs.
- Existing fields and statuses remain semantically unchanged. With `vision_backend=none`, no model-dependent evidence is emitted and existing detection results must remain equivalent apart from the SourceLayout schema version.
- Keep unknown topology and direction explicitly unknown.

## Verification and acceptance

1. Pure tests cover pixel-to-PDF mapping, OCR marker parsing, false-positive rejection, region deduplication, nested hierarchy, alignment grouping, and ambiguous object ownership.
2. Adapter tests cover missing optional dependencies, model initialization errors, normalized result parsing, and provenance recording without requiring model weights in CI.
3. Review tests cover human-only acceptance, candidate snapshot integrity, split geometry bounds, and raster-gutter restrictions.
4. Schema tests validate both SourceLayout 1.0.0 and 1.1.0 fixtures.
5. CI runs all tests without installing PaddleOCR or downloading models.
6. A separate local development replay on the ten-paper cohort produces contact sheets and a candidate audit. Human-reviewed precision/recall are reported separately from the frozen 0/10 strict first-pass baseline.
7. The PR remains Draft until independent scientific review and real PowerPoint 2016 host validation are complete.

## Next stages

- **P1-01B (this design):** optional visual proposals, embedded panel-marker OCR, evidence fusion, nested hierarchy, ownership, and review integration.
- **P1-01C:** consume only accepted panel facts in FigureSpec drafting and panel-level route selection; add structure-aware layout/reflow without moving science nodes blindly.
- **P1-02:** evidence-based native/vector, mixed, and raster reconstruction routing with independent acceptance evidence.
