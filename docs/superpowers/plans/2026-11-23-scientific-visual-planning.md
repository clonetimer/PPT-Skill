# Scientific Visual Planning Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans for the integrated
> implementation, with independent bounded research, glyph work and final review.

**Goal:** Turn evidenced scientific objects into recognizable editable figures.
**Architecture:** FigurePlan → semantic glyphs → existing FigureSpec renderer.
**Tech Stack:** Python standard library, existing python-pptx renderer, LibreOffice
for observed preview export. No new mandatory layout engine.
**Spec:** ../specs/2026-11-23-scientific-visual-planning-design.md

## Global Constraints

- Preserve existing renderer outputs and source checks.
- Keep unknown scientific details explicit.
- Standalone figures do not inherit a slide-card template or forced 16:9 ratio.
- Publish synthetic regression cases only; keep user screenshot tests private.
- Test actual rendered output and report its renderer honestly.

## Review Focus

- Unknown head fusion/adjacency must not produce an asserted implementation.
- Valid-looking references to the wrong or modified source must be rejected.
- Opaque components remain valid when their evidence does not expose internals.
- Shared encoder branches and conditioning edges must survive in actual marks.
- Labels, long Chinese text and head count changes must retain usable geometry.

## Task 1: Evidence-linked planning and routing

Files: tools/scientific_figure_plan.py; tools/test_scientific_figure_plan.py.
Interfaces: plan_figure(brief,source_root) -> planned dict; PlanError(ValueError).

- [x] Write and observe failing tests for satellite GAT routing, source hashing,
  unknown kinds, evidence references, missing critical edges and unsupported
  implied operations. Check no mutation of the caller's input.
- [x] Implement deterministic route and glyph selection with explicit failures.
- [x] Run planning tests; document the real source-reading boundary.

## Task 2: Glyphs, compilation and semantic audit

Files: tools/scientific_figure_glyphs.py; tools/build_scientific_figure.py;
tools/test_scientific_figure_render.py.
Interfaces: draw_node(node) -> elements/ports/box; compile_figure(plan) -> spec;
audit_figure(plan,spec) -> {passed,errors,warnings}. Use the spec's node contract.

- [x] Add failing tests for head count, distinct tensors/merge marks, visible
  critical connectors and absence of embedded pictures in native examples.
- [x] Implement bounded glyph vocabulary and deterministic connector assembly.
- [x] Exercise head deletion and edge deletion mutation checks; render two
  synthetic examples and inspect exported PNG at delivery size.

## Task 3: Entry points and user regressions

Files: SKILL.md; docs/SCIENTIFIC_FIGURE_PLANNING.md; README.md;
examples/semantic_figures/*; .github/workflows/validate-assets.yml.

- [x] Use the actual old-skill response and supplied screenshots as baseline.
- [x] Put intent routing and a runnable recipe before style/library selection.
- [x] Run the private two-screenshot reconstructions, retaining visible facts
  and indicating unknown internals. Review the actual exported images.
- [x] Forward-test fresh-agent use; perform independent code/visual review.
- [x] Run required regression checks once after fixes and save results.

## Task 4: Delivery and installed-skill parity

- [x] Commit and push a focused feature branch and create a reviewable draft PR.
- [x] Update the user's installed scientific path with tested resources, retain
  existing defense material, validate and save the updated personal skill.
- [x] Verify saved paths and content; deliver PR, actual previews, limitations
  and the next substantive improvement rather than more unmeasured gates.

## Delivery record

- Draft PR: https://github.com/clonetimer/PPT-Skill/pull/22
- Local verification: 162 unittest cases across 12 suites plus one standalone polygon regression; 61 cases cover the new path.
- Two public synthetic examples and two private screenshot cases were built and inspected through LibreOffice PDF/PNG.
- Installed personal Skill: 12 changed resources saved and verified after reconciliation; original 10 library tests remain passing.
- User deliverable: portable private briefs, source screenshots, native PPTX, SVG, PDF/PNG and review records. Private artifacts are not committed here.
- Package version remains 7.6.0-dev; the new scientific component is independently marked 7.7.0-dev. PR checks carry the current CI outcome.
