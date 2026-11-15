"""FigureSpec semantic contract and rendered-output audit tests."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from audit_figure_spec import audit_figure_spec_semantics, audit_figurespec_output
from render_figure_spec import render


def build_spec(path: Path, *, edge="a__b", declared=True):
    spec = {
        "schema_version": "7.6.0-dev",
        "id": "semantic-audit-test",
        "canvas": {"width_in": 5.0, "height_in": 2.0},
        "style": {"font": "Arial"},
        "figure_contract": {
            "claim": "A feeds B",
            "archetype": "schematic_led_composite",
            "output_mode": "publication",
            "unverified": [],
        },
        "evidence_records": [{
            "id": "e1", "source": "paper", "source_file_sha256": "a" * 64,
            "source_locator": "Figure 1", "status": "source_visible_redraw",
            "scope": "method flow", "reuse": "derivative_redraw_only",
        }],
        "semantic_edges": [["a", "b"]] if declared else [],
        "elements": [
            {"id": "a", "type": "rect", "x": .4, "y": .5, "w": 1, "h": .6,
             "fill": "#EEEEEE", "stroke": "#333333", "semantic_id": "a",
             "semantic_role": "scientific_object", "evidence_ref": "e1"},
            {"id": "b", "type": "rect", "x": 3, "y": .5, "w": 1, "h": .6,
             "fill": "#EEEEEE", "stroke": "#333333", "semantic_id": "b",
             "semantic_role": "scientific_object", "evidence_ref": "e1"},
            {"id": "edge", "type": "line", "x1": 1.4, "y1": .8, "x2": 3, "y2": .8,
             "semantic_link": edge, "semantic_role": "connector", "evidence_ref": "e1"},
            {"id": "label-a", "type": "text", "x": .5, "y": .68, "w": .8, "h": .2,
             "text": "A", "size": 10, "semantic_role": "scientific_label", "evidence_ref": "e1"},
            {"id": "label-b", "type": "text", "x": 3.1, "y": .68, "w": .8, "h": .2,
             "text": "B", "size": 10, "semantic_role": "scientific_label", "evidence_ref": "e1"},
        ],
    }
    path.write_text(json.dumps(spec), encoding="utf-8")
    return spec


class FigureSpecReleaseAuditTests(unittest.TestCase):
    def test_declared_semantic_edge_matches_native_connector_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "spec.json"
            build_spec(path)
            report = audit_figure_spec_semantics(path)
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["declared_edge_count"], 1)
            self.assertEqual(report["represented_edge_count"], 1)

    def test_missing_semantic_edges_are_review_not_implicit_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "spec.json"
            build_spec(path, declared=False)
            report = audit_figure_spec_semantics(path)
            self.assertEqual(report["status"], "NEEDS_REVIEW")
            self.assertIn("SEMANTIC_RELATION_AUDIT_MISSING", report["blockers"])

    def test_wrong_connector_link_fails_even_if_declared_edge_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "spec.json"
            build_spec(path, edge="a__wrong")
            report = audit_figure_spec_semantics(path)
            self.assertEqual(report["status"], "FAIL")
            self.assertEqual(report["missing_edges"], [["a", "b"]])

    def test_unknown_evidence_reference_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "spec.json"
            spec = build_spec(path)
            spec["elements"][0]["evidence_ref"] = "missing"
            path.write_text(json.dumps(spec), encoding="utf-8")
            report = audit_figure_spec_semantics(path)
            self.assertEqual(report["status"], "FAIL")
            self.assertIn("UNKNOWN_EVIDENCE_REFERENCE", report["blockers"])

    def test_rendered_pptx_retains_all_source_spec_texts_and_pictures(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_path = root / "spec.json"
            build_spec(spec_path)
            spec = json.loads(spec_path.read_text())
            svg, pptx = root / "spec.svg", root / "spec.pptx"
            render(spec, svg, pptx)
            report = audit_figurespec_output(spec_path, pptx)
            self.assertEqual(report["structure"]["status"], "PASS")
            self.assertEqual(report["text_geometry"]["status"], "PASS")
            self.assertEqual(report["text_geometry"]["missing_text"], [])

    def test_missing_pptx_label_fails_rendered_output_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_path = root / "spec.json"
            build_spec(spec_path)
            spec = json.loads(spec_path.read_text())
            svg, pptx = root / "spec.svg", root / "spec.pptx"
            render(spec, svg, pptx)
            from pptx import Presentation
            deck = Presentation(pptx)
            shape = next(s for s in deck.slides[0].shapes if getattr(s, "has_text_frame", False) and s.text.strip())
            shape.text = "CORRUPTED"
            deck.save(pptx)
            report = audit_figurespec_output(spec_path, pptx)
            self.assertEqual(report["text_geometry"]["status"], "FAIL")
            self.assertTrue(report["text_geometry"]["missing_text"])


if __name__ == "__main__":
    unittest.main()
