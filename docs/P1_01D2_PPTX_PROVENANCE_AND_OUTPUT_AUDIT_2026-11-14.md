# P1-01D2 PPTX Provenance Annotation and Output Audit

The existing PDF importer now writes a stable SourceLayout object ID into each imported PowerPoint shape's name and non-visual description metadata:

- PDF vector drawing: `draw_<seqno>`
- PDF image paint event: `image_<seqno>`
- PDF text span: `text_<block>_<line>_<span>`

This annotation does not change geometry, styling, source paint order, or scientific interpretation.

## Audit command

```powershell
python tools/audit_source_composition_pptx.py .\qa\source_composition_manifest.json .\qa\imported_figure.pptx --output .\qa\source_composition_pptx_audit.json
```

The audit compares the composition manifest with the actual PPTX and checks:
- missing, unexpected, or duplicated source object IDs;
- picture, editable text, and editable vector object classes;
- source paint order for objects with native PDF order indices;
- malformed or absent shape provenance metadata.

A passing audit verifies structural provenance and object-class preservation only. It does not verify pixel similarity, glyph fidelity, scientific topology, Office 2016 host rendering, or semantic correctness. Those remain independent acceptance gates.
