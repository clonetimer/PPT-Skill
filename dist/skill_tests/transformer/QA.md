# Transformer diagram trial QA

- Source: Vaswani et al. (2017), *Attention Is All You Need*, Figures 1–2 and §§3.1–3.5; scope and exclusions in `SOURCE.md`.
- Deliverable: two-slide 16:9 editable PPTX, one PDF, two SVG figures and two PNG previews.
- Both FigureSpecs passed V7.6 schema, evidence-hash and visible-route checks against the separate `expected_topology.json`.
- Three topology tests passed, including mutations that remove the encoder→cross-attention K/V route and the attention V→weighted-sum route from both the drawing and its self-declared edges.
- Text and arrow contrast preflight passed for both slides.
- Final combined PPTX strict audit: two slides, 100 and 71 native objects; zero raster pictures, out-of-bounds objects, text-box intersections and theme shadows. Minimum text size 9.3 pt.
- Windows PowerPoint exported a two-page PDF and 1600 × 900 PNG previews; both previews were visually inspected.
- Still needed for any release claim: independent technical review and actual projection-distance inspection. This is a development example, not a verified journal-production figure.
