"""Independent source-derived topology checks for new-paper generalization trials."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TRIALS = ROOT / "dist" / "skill_tests" / "generalization"


def _spec(name: str) -> dict:
    return json.loads((TRIALS / name).read_text(encoding="utf-8"))


def _texts(spec: dict) -> set[str]:
    return {e["text"] for e in spec["elements"] if e["type"] == "text"}


def _has_line(spec: dict, x1: float, y1: float, x2: float, y2: float, *, color: str | None = None) -> bool:
    for e in spec["elements"]:
        if e["type"] != "line":
            continue
        if all(abs(e[k] - v) < 1e-6 for k, v in (("x1", x1), ("y1", y1), ("x2", x2), ("y2", y2))):
            if color is None or e.get("color") == color:
                return True
    return False


class GeneralizationTopologyTests(unittest.TestCase):
    def test_mamba_selective_ssm_keeps_source_critical_nodes_and_routes(self):
        spec = _spec("Mamba_Figure1.json")
        text = _texts(spec)
        required = {
            "hₜ₋₁", "hₜ", "A", "Bₜ", "Cₜ", "Δₜ", "xₜ", "yₜ",
            "Project", "Selection Mechanism", "GPU SRAM", "GPU HBM",
        }
        self.assertTrue(required.issubset(text), f"missing labels: {sorted(required - text)}")

        channels = [
            e for e in spec["elements"]
            if e["type"] == "line"
            and abs(e.get("x1", 0) - 1.14) < 1e-6
            and abs(e.get("x2", 0) - 10.62) < 1e-6
            and e.get("color") == "#D8752A"
        ]
        self.assertEqual(len(channels), 4, "four visible state channels must connect h(t-1) to h(t)")
        self.assertTrue(all(e.get("arrow") for e in channels))

        # Source-grounded parameter and feature routes.
        self.assertTrue(_has_line(spec, 4.2, 2.1, 5.14, 2.1, color="#D8752A"))
        self.assertTrue(_has_line(spec, 6.35, 2.95, 7.42, 2.95, color="#D8752A"))
        self.assertTrue(_has_line(spec, 3.82, 3.5, 5.15, 3.32, color="#6D7A80"))
        self.assertTrue(_has_line(spec, 3.57, 4.19, 5.31, 4.19, color="#4A83D2"))
        self.assertTrue(_has_line(spec, 5.31, 4.19, 5.31, 3.48, color="#4A83D2"))

        self.assertTrue(any(e["type"] == "polyline" and e.get("points") == [[2.32, 2.88], [2.78, 2.88], [2.78, 3.15], [3.48, 3.15]] for e in spec["elements"]))
        self.assertTrue(any(e["type"] == "polyline" and e.get("points") == [[7.76, 3.15], [8.3, 3.15], [8.3, 2.88], [8.8, 2.88]] for e in spec["elements"]))

    def test_swin_shifted_windows_keep_patch_and_window_topology(self):
        spec = _spec("Swin_Figure2.json")
        text = _texts(spec)
        required = {
            "Layer l · Regular windows", "Layer l+1 · Shifted windows",
            "Shift by\n(2, 2)", "Local window\nfor self-attention", "A patch",
        }
        self.assertTrue(required.issubset(text), f"missing labels: {sorted(required - text)}")

        grids = [e for e in spec["elements"] if e["type"] == "grid"]
        self.assertEqual(len(grids), 2)
        self.assertTrue(all(e["rows"] == 8 and e["cols"] == 8 for e in grids))
        self.assertAlmostEqual(grids[0]["w"], grids[0]["h"], places=6)
        self.assertAlmostEqual(grids[1]["w"], grids[1]["h"], places=6)

        # Regular layer: two-by-two 4×4 patch windows.
        for x in (1.1, 2.78, 4.46):
            self.assertTrue(any(e["type"] == "line" and e.get("color") == "#C74B4B" and abs(e.get("x1", -1)-x)<1e-6 and abs(e.get("x2", -1)-x)<1e-6 for e in spec["elements"]))
        for y in (1.35, 3.03, 4.71):
            self.assertTrue(any(e["type"] == "line" and e.get("color") == "#C74B4B" and abs(e.get("y1", -1)-y)<1e-6 and abs(e.get("y2", -1)-y)<1e-6 for e in spec["elements"]))

        # Shifted layer: nine clipped windows created by the half-window offset.
        for x in (6.45, 7.29, 8.97, 9.81):
            self.assertTrue(any(e["type"] == "line" and e.get("color") == "#C74B4B" and abs(e.get("x1", -1)-x)<1e-6 and abs(e.get("x2", -1)-x)<1e-6 for e in spec["elements"]))
        for y in (1.35, 2.19, 3.87, 4.71):
            self.assertTrue(any(e["type"] == "line" and e.get("color") == "#C74B4B" and abs(e.get("y1", -1)-y)<1e-6 and abs(e.get("y2", -1)-y)<1e-6 for e in spec["elements"]))


if __name__ == "__main__":
    unittest.main()
