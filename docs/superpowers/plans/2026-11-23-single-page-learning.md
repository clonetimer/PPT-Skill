# Single-page academic slide implementation

User scope: a single editable academic slide; learn from existing implementations and improve the Skill. Continue on the existing draft PR branch; no approval pause or model download.

1. Inspect AutoPresent / SlideCoder source and original GAT Figure 1 / equations / author code. Keep scientific sources distinct from layout-method references.
2. Add a thin invisible-region composer over the existing FigureSpec renderer. Preserve aspect ratio, IDs, sources, single-page output, and scope local revisions to a named region. Cross-region lines remain explicit dependencies.
3. Author one new GAT mechanism slide. Render the actual PPTX, inspect it, record any observed issue, revise only affected regions, and retain the first and final renders.
4. Add focused transform/local-revision tests, independently review the produced page, document the runnable path, and update the installed Skill with the same utility and example.
5. Publish to the existing draft PR and sync the installed personal Skill. This demonstrates one bounded example; it does not claim model-weight inference, fine-tuning, general scientific understanding, or a benchmark win.
