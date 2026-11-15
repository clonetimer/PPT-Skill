"""Source-grounded radar consistency regression without publisher artwork."""
from __future__ import annotations

import csv
import json
import math
from zipfile import ZipFile
from lxml import etree
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_source_grounded_radar import DEFAULT_SERIES, read_source_table, source_axis, audit_radar, shape_stroke
from correct_source_grounded_radar import corrected_candidate

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "tests/fixtures/mmgraph_f2_table3.csv"
MANIFEST = ROOT / "tests/fixtures/mmgraph_f2_radar_manifest.json"


def make_synthetic_radar(out: Path):
    source = read_source_table(CSV)
    config = json.loads(MANIFEST.read_text(encoding="utf-8"))
    deck = Presentation()
    deck.slide_width = Inches(8.12)
    deck.slide_height = Inches(3.6944)
    sl = deck.slides.add_slide(deck.slide_layouts[6])
    for chart, cx, cy in zip(config["radars"], [5.20689, 6.96548], [1.16753, 1.16583]):
        axes = [source_axis(row, source) for row in chart["axes"]]
        for key, color in DEFAULT_SERIES:
            pts = []
            for k, row in enumerate(axes):
                angle = math.radians(-90 + 40*k)
                radius = .5431 * row[key] / row["mmgraph_agent"]
                pts.append((cx+radius*math.cos(angle), cy+radius*math.sin(angle)))
            first = pts[0]
            builder = sl.shapes.build_freeform(
                round(first[0]*10000), round(first[1]*10000), scale=Inches(1)/10000
            )
            builder.add_line_segments(
                [(round(x*10000), round(y*10000)) for x, y in pts[1:]+[first]],
                close=False,
            )
            # The real F2 export contains two overlaid editable path objects
            # per radar series; retain that z-order duplication in the fixture.
            for _copy in range(2):
                builder = sl.shapes.build_freeform(
                    round(first[0]*10000), round(first[1]*10000), scale=Inches(1)/10000
                )
                builder.add_line_segments(
                    [(round(x*10000), round(y*10000)) for x, y in pts[1:]+[first]],
                    close=False,
                )
                shape = builder.convert_to_shape()
                shape.fill.background()
                shape.line.width = Pt(.4)
                shape.line.color.rgb = RGBColor.from_string(color)
    deck.save(out)


class RadarSourceConsistencyTests(unittest.TestCase):
    def test_non_destructive_audit_and_single_vertex_correction(self):
        """Reject a hidden source audit bug that adds blue outlines to thousands
        of unrelated shapes whenever a corrected PPTX is saved.
        """
        def shape_nodes(path):
            with ZipFile(path) as package:
                xml = package.read("ppt/slides/slide1.xml")
            root = etree.fromstring(xml)
            ns = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
            return [etree.tostring(node) for node in root.xpath("//p:spTree/*", namespaces=ns)]
        with TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source.pptx"
            corrected = root / "corrected.pptx"
            make_synthetic_radar(source)
            deck = Presentation(source)
            deck.slides[0].shapes.add_textbox(
                Inches(.2), Inches(.2), Inches(1.5), Inches(.3)
            ).text = "UNRELATED TEXT MUST STAY UNCHANGED"
            deck.save(source)
            before = shape_nodes(source)
            test_deck = Presentation(source)
            tree_before = bytes(test_deck.slides[0].shapes._spTree.xml, "utf-8")
            for shape in test_deck.slides[0].shapes:
                shape_stroke(shape)
            self.assertEqual(
                tree_before,
                bytes(test_deck.slides[0].shapes._spTree.xml, "utf-8"),
                "A supposedly read-only audit must not insert <a:ln> nodes",
            )
            with CSV.open(encoding="utf-8") as handle:
                data = list(csv.DictReader(handle))
            next(row for row in data if row["dataset"] == "We-Math2.0")["grpo_qwen"] = "30.00"
            modified = root / "modified.csv"
            with modified.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(data[0]))
                writer.writeheader()
                writer.writerows(data)
            result = corrected_candidate(source, modified, MANIFEST, corrected)
            after = shape_nodes(corrected)
            self.assertEqual(result["output_status"], "PASS")
            self.assertEqual(result["correction_count"], 2)
            self.assertEqual(len(before), len(after))
            changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
            self.assertEqual(len(changed), 2, f"Only the two overlaid target curve paths may change: {changed}")


    def test_all_18_axes_9_models_pass_with_source_values(self):
        with TemporaryDirectory() as folder:
            candidate = Path(folder)/"synthetic.pptx"
            make_synthetic_radar(candidate)
            result = audit_radar(candidate, CSV, MANIFEST)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["source_dataset_count"], 23)
            self.assertEqual(len(result["charts"]), 2)
            self.assertTrue(all(len(c["checks"]) == 9 for c in result["charts"]))

    def test_corrupt_source_table_triggers_radar_failure(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            candidate = root/"synthetic.pptx"
            make_synthetic_radar(candidate)
            with CSV.open(encoding="utf-8") as handle:
                data = list(csv.DictReader(handle))
            next(x for x in data if x["dataset"] == "We-Math2.0")["grpo_qwen"] = "30.00"
            mutated = root/"mutated.csv"
            with mutated.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(data[0]))
                writer.writeheader()
                writer.writerows(data)
            result = audit_radar(candidate, mutated, MANIFEST)
            self.assertEqual(result["status"], "FAIL")
            self.assertFalse(next(
                s for s in result["charts"][1]["checks"] if s["series"] == "grpo_qwen"
            )["passed"])

    def test_text_only_six_average_means_before_division(self):
        source = read_source_table(CSV)
        config = json.loads(MANIFEST.read_text(encoding="utf-8"))
        average = source_axis(config["radars"][0]["axes"][3], source)
        self.assertAlmostEqual(average["mmgraph_agent"], 20.44, places=2)
        self.assertAlmostEqual(average["std_gpt"], 10.9416666667, places=6)
        self.assertAlmostEqual(average["std_gpt"]/average["mmgraph_agent"], .5353065884, places=5)


if __name__ == "__main__":
    unittest.main()
