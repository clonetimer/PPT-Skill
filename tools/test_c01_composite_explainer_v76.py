import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from pptx import Presentation

from build_c01_composite_explainer_v76 import build
from validate_c01_composite_explainer_v76 import validate
from scientific_ir import ROOT


@unittest.skipUnless(shutil.which("libreoffice") and shutil.which("pdftoppm"),
                     "LibreOffice and Poppler are required for the two-slide C01 explainer")
class C01CompositeExplainerTests(unittest.TestCase):
    def test_two_slide_enlarged_companion_preserves_both_editable_panels(self):
        subprocess.run([sys.executable,str(ROOT/"tools/build_c01_fbg_v74.py")],check=True)
        subprocess.run([sys.executable,str(ROOT/"tools/build_c01_seanet_v74.py")],check=True)
        build()
        result=validate()
        self.assertEqual(result["status"],"PASS")
        self.assertEqual(result["slide_count"],2)
        deck=Presentation(ROOT/"dist/C01_composite_explainer_v76.pptx")
        self.assertIn("Graph Construction (Time-Frequency Graph)",
                      "\n".join(s.text for s in deck.slides[0].shapes if s.has_text_frame))
        self.assertIn("fault class",
                      "\n".join(s.text for s in deck.slides[1].shapes if s.has_text_frame))
        self.assertTrue((ROOT/"dist/accepted_repairs/C01_composite_explainer_v76.pptx").is_file())


if __name__=="__main__":
    unittest.main()
