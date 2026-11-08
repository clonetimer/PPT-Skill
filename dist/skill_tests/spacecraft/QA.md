# SC01 spacecraft subsystem mechanism: development QA

Scope: a notional solar-powered, three-axis-stabilized satellite bus with propulsion. This is a **functional interface diagram**, not a flown spacecraft schematic. Source and configuration limits are in `SOURCE.md`. The NASA 1974 Figure 2-9 reference supplies only the visual grammar; current subsystem functions are grounded in the NASA 2026 SmallSat material and NASA spacecraft-bus descriptions.

- SourceStyleSpec: six source-visible anchors in `source_style.json`; dashed regions, orthogonal labeled routing, small component glyphs and external interfaces were checked against the NASA diagram preview.
- FigureSpec: 127 editable drawing elements and 30 source-derived required relations, including solar→PCDU→bus, ground↔transceiver, payload→storage→downlink, ADCS feedback, payload heat→radiator→space, and commanded propellant→thruster→orbital Δv.
- The independent topology fixture and four omission mutations passed. Schema, source-ledger hash, ScientificIR and visible-route geometry checks passed.
- Strict PPTX audit: one slide, 162 native PowerPoint objects; zero picture objects, inherited theme shadows, out-of-bounds objects or overlapping text boxes. Minimum label size is 8.8 pt; text and arrow contrast preflight passed.
- Windows PowerPoint exported a PDF and 1920×1098 PNG preview. The preview was visually inspected.

Limits: power/command lines cross without electrical junctions; the legend states that convention. No bus voltage, protocol, pointing accuracy, heat load, propellant or Δv value is specified. Propulsion and exact ADCS components are configuration-dependent. This is a presentation-profile development figure; independent aerospace review and actual-size projection check have not occurred.
