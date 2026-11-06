# V7.5 draft: academic presentation planning

The canonical planning artifact is a DeckSpec containing ordered SlideSpecs. A FigureSpec describes a figure's scientific content and geometry. A SourceStyleSpec describes the visual evidence behind a style choice; a StyleSpec converts those anchors into usable typography, color and surface rules. A page layout describes placement. Keep these decisions independent: changing a layout or style must not change a scientific edge, formula, or number.

## Plan the deck before drawing

1. Record the research topic, audience, duration, delivery format, and source inventory. Mark missing sources explicitly.
2. Write one defensible claim per slide. For each claim, list the source and evidence status. Do not turn an unverified claim into a result slide.
3. Order the slides as a research argument: problem, gap, objective, approach, experiment, results, limitations, contribution. Omit roles the source cannot support.
4. Set a slide budget from presentation time. Split a topic when it needs different evidence, a different figure type, or more than one main claim. Merge only when the audience must compare the pieces together.
5. Choose a layout from the slide role and content geometry. Use a composite page for related figures plus a short reading guide; use separate overview and detail pages when labels or relationships become cramped.
6. Keep the on-slide text short. Put definitions, assumptions, caveats, transitions, and citation detail in speaker notes. Notes must not hide an unsupported on-slide claim.
7. Build figures from FigureSpecs, then apply SourceStyleSpec and page layout. Render SVG and native PPTX from the same frozen spec.
8. Export the complete deck to PDF in PowerPoint or a documented alternative. Inspect every slide at presentation size, then run structural and semantic checks.

## Contracts

| Artifact | Required decisions | Validation |
|---|---|---|
| DeckSpec | audience, time, slide count, narrative, delivery, style reference | slide count and references |
| SlideSpec | role, claim, evidence, layout, on-slide text, notes, figure reference | evidence status and source paths |
| FigureSpec | nodes, connections, formula/data, geometry, evidence boundary | topology plus visual review |
| SourceStyleSpec | 5–7 anchors with dimension, evidence, weight/confidence | source traceability and consistency |
| StyleSpec | source style reference, typography, color, density, surface | references and allowed values |

`specs/deck_spec_v75.example.json` shows the first three-slide contract and `specs/deck_spec_v75.schema.json` defines its typed structure. Its C01 method page points to the V7.4 composite FigureSpec. This is a planning example, not a complete research defense; no result or conclusion is fabricated from absent performance data.

## Page roles and layout choices

The first page-role catalog is research question, prior work and gap, framework, method, experiment/data, result, ablation/reliability, and conclusion/contribution. These are semantic roles, not locked designs. Each role may use a single figure, figure plus annotations, comparison, asymmetric mixed media, or overview/detail arrangement. Select by the evidence and reading path, not by a fixed theme.

## QA decision

Scientific relation, data/formula accuracy, source status, readability, and clipping are hard gates. The weighted score in the project proposal may help compare passing decks, but a high average cannot offset a hard-gate failure. Automated object and geometry checks do not prove scientific correctness; the source-to-figure review remains a separate human check.
