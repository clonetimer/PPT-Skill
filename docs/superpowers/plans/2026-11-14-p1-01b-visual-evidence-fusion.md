# P1-01B Visual Evidence Fusion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add optional visual region and OCR panel-marker evidence to SourceLayout, fuse it with native PDF objects, and expose the resulting nested candidates to the existing human-review workflow.

**Architecture:** Keep PyMuPDF as the source-of-truth inventory and add a lazy-loaded PaddleOCR adapter. A pure evidence-fusion module maps model coordinates into the selected PDF crop, builds nested region candidates and marker hypotheses, and assigns source objects only when containment is unambiguous. All model-derived output remains review-only.

**Tech Stack:** Python 3.11/3.12 optional environment, PyMuPDF, Pillow, PaddleOCR 3.x, ONNX Runtime, jsonschema, unittest.

**Spec:** `docs/superpowers/specs/2026-11-14-p1-01b-visual-evidence-fusion-design.md`

## Global Constraints

- Default extraction uses `vision_backend="none"`; no model dependency or download is required for existing workflows.
- Optional layout model: `PP-DocLayout-S`; optional OCR models: `PP-OCRv6_small_det` and `PP-OCRv6_small_rec`.
- Use ONNX Runtime where supported; do not commit model weights.
- All model coordinates must map to the exact selected crop in PDF points using actual raster dimensions.
- Every model-derived region, OCR marker, hierarchy, and ownership assignment remains review-only.
- OCR markers alone, raster gutters, and model boxes cannot authorize semantic panels, directed edges, or causal relations.
- Preserve SourceLayout 1.0.0 review compatibility; new output uses schema 1.1.0.
- No source PDF mutation; source SHA-256, page index, and crop remain provenance anchors.
- Do not modify scientific FigureSpec nodes/connectors through geometric panel bindings.
- The frozen ten-paper strict first-pass baseline remains 0/10 and is not recomputed.

## Review Focus

- **Raster coordinate drift:** non-integer scale and rounded pixmap dimensions must map back to the exact PDF crop.
- **Nested duplicate detections:** overlapping parent/child layout boxes must retain hierarchy rather than flatten or duplicate panels.
- **OCR false positives:** ordinary prose letters, axis labels, and legend text must not become panel labels without punctuation/anchor evidence.
- **Ambiguous source ownership:** objects crossing boundaries or contained by multiple candidates must remain unresolved.
- **Optional-runtime failure:** default mode must work without PaddleOCR; explicitly requested model mode must fail with a useful installation/model diagnostic.

---

### Task 1: Pure visual evidence normalization and fusion

**Files:**
- Create: `tools/source_layout_vision.py`
- Create: `tools/test_source_layout_vision.py`

**Interfaces:**
- `map_raster_bbox_to_pdf(bbox_px, raster_size, figure_region_pt) -> list[float]`
- `normalize_layout_detections(raw_result, raster_size, figure_region_pt) -> list[dict]`
- `normalize_ocr_detections(raw_result, raster_size, figure_region_pt) -> list[dict]`
- `fuse_visual_evidence(layout_candidates, ocr_markers, layout_elements, image_assets, figure_region_pt) -> dict`

- [ ] **Step 1: Write failing coordinate and parsing tests**
  - `test_map_raster_bbox_uses_actual_raster_dimensions`
  - `test_layout_detections_map_to_pdf_points_and_discard_out_of_crop_boxes`
  - `test_ocr_parser_accepts_parenthesized_panel_labels`
  - `test_ocr_parser_keeps_bare_letters_as_low_confidence_candidates`
  - `test_ocr_parser_rejects_words_and_axis_text`
- [ ] **Step 2: Run `python tools/test_source_layout_vision.py` and verify the expected missing-function failures.**
- [ ] **Step 3: Implement pure mapping and normalization functions.**
- [ ] **Step 4: Add fusion tests**
  - `test_visual_regions_deduplicate_same_class_boxes_but_keep_nested_boxes`
  - `test_nested_regions_receive_smallest_containing_parent`
  - `test_ocr_marker_anchors_only_to_smallest_containing_visual_region`
  - `test_source_objects_with_ambiguous_ownership_remain_unassigned`
  - `test_source_object_ownership_records_source_order_and_overlap_ratio`
- [ ] **Step 5: Implement hierarchy, marker hypotheses, alignment groups, and conservative ownership.**
- [ ] **Step 6: Run the focused test file and commit.**

### Task 2: Optional PaddleOCR backend

**Files:**
- Modify: `tools/source_layout_vision.py`
- Create: `requirements-vision.txt`
- Create: `tools/test_source_layout_vision_backend.py`

**Interfaces:**
- `run_paddleocr_backend(image_path, *, layout_model="PP-DocLayout-S", ocr_det_model="PP-OCRv6_small_det", ocr_rec_model="PP-OCRv6_small_rec") -> dict`
- The function imports PaddleOCR lazily and returns normalized raw detections plus model/runtime provenance.

- [ ] **Step 1: Write tests for missing dependency, missing model/runtime, and normalized backend output.**
- [ ] **Step 2: Run focused tests and verify the optional-dependency failures are explicit and actionable.**
- [ ] **Step 3: Implement lazy model construction and inference with ONNX Runtime; cache model instances per process.**
- [ ] **Step 4: Add optional requirements only; do not alter base requirements or CI install steps.**
- [ ] **Step 5: Run backend adapter tests without PaddleOCR installed and commit.**

### Task 3: Integrate visual evidence into SourceLayout

**Files:**
- Modify: `tools/extract_source_layout.py`
- Modify: `specs/source_figure_layout.schema.json`
- Modify: `tools/test_source_layout_extraction.py`
- Create: `tools/test_source_layout_vision_integration.py`

**Interfaces:**
- Extend `extract_source_layout(..., vision_backend="none", vision_dpi=180, vision_max_side=3000)`.
- CLI adds `--vision-backend {none,paddleocr}`, `--vision-dpi`, and `--vision-max-side`.
- Output adds `panel_detection.visual_region_candidates`, `ocr_panel_markers`, `panel_hypotheses`, `visual_alignment_groups`, `source_object_ownership`, and `visual_evidence`.
- Output schema version becomes `1.1.0`; schema accepts the 1.1.0 output while review code continues to accept 1.0.0 source layouts.

- [ ] **Step 1: Write integration tests with injected deterministic model outputs; no model weights in CI.**
- [ ] **Step 2: Verify the tests fail because the extractor has no vision options/evidence fields.**
- [ ] **Step 3: Render only the selected PDF region to a bounded temporary raster and call the optional backend.**
- [ ] **Step 4: Fuse visual evidence with existing PDF-native layout elements and preserve source hashes/crop coordinates.**
- [ ] **Step 5: Update the versioned JSON schema and add 1.0.0/1.1.0 compatibility fixtures.**
- [ ] **Step 6: Run source-layout extraction, schema, and vision integration tests; commit.**

### Task 4: Human review of visual candidates

**Files:**
- Modify: `tools/source_layout_review.py`
- Modify: `tools/test_source_layout_review.py`
- Modify: `tools/test_source_layout_split_review.py`
- Modify: `tools/source_layout_constraints.py` only if a new candidate type requires explicit validation.

**Interfaces:**
- `_candidate_index(layout)` includes visual regions, label-anchored panel hypotheses, and visual alignment groups.
- Human `accept_panel` may accept a visual region or label-anchored region hypothesis, never an OCR marker alone or a raster gutter.
- `split_region` may split a bounded visual region into geometric children; children remain geometric regions, not semantic panels.

- [ ] **Step 1: Write failing tests for template coverage, OCR-only rejection, human-only visual acceptance, assistant-triage restrictions, and visual-region splitting.**
- [ ] **Step 2: Run the focused review tests and verify expected failures.**
- [ ] **Step 3: Extend candidate indexing and validation while preserving all-or-nothing review semantics and candidate snapshots.**
- [ ] **Step 4: Verify existing 1.0.0 review fixtures still validate.**
- [ ] **Step 5: Run review, constraints, and FigureSpec geometry tests; commit.**

### Task 5: Documentation, cohort replay, and release evidence

**Files:**
- Modify: `README.md`
- Create: `docs/P1_01B_VISUAL_EVIDENCE_FUSION_2026-11-14.md`
- Modify: `.github/workflows/validate-assets.yml` only to add deterministic tests; do not install PaddleOCR in CI.

- [ ] **Step 1: Document default mode, optional installation, model cache behavior, CLI examples, and evidence limits.**
- [ ] **Step 2: Add deterministic vision tests to Linux CI without model downloads.**
- [ ] **Step 3: Run all source-layout tests, all PDF reproduction tests, FigureSpec validators, and the full repository workflow.**
- [ ] **Step 4: Run a separate local ten-paper development replay when the PDFs are available; produce contact sheets and human-reviewed candidate audit. Do not update the frozen 0/10 baseline.**
- [ ] **Step 5: Record CI, model/runtime versions, and limitations in the Draft PR; commit.**

---

## Completion Criteria

- Default no-model workflow remains usable and produces no fabricated visual approval.
- Optional backend produces bounded, provenance-linked visual proposals and OCR marker candidates.
- Nested hierarchy and source-object ownership are deterministic and preserve unresolved ambiguity.
- Human review is mandatory before a model-derived region can become a confirmed source panel.
- SourceLayout 1.0.0 review compatibility and all existing native import safeguards remain intact.
- Full Linux CI passes; Windows PowerShell syntax checks pass.
- No claim of strict blind-test improvement is made.
