import tempfile,unittest
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches
from prepare_15_figure_initial_cohort import prepare
from fifteen_figure_review_packet import TASK_FILENAMES,TASK_COMPANION_FILENAMES

def deck(path,label):
    p=Presentation();s=p.slides.add_slide(p.slide_layouts[6]);s.shapes.add_textbox(Inches(1),Inches(1),Inches(2),Inches(.5)).text=label;p.save(path)
class PrepareInitialCohortTests(unittest.TestCase):
    def test_c01_and_deck_overrides_are_used_and_all_15_tasks_are_copied(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);initial=root/"initial";initial.mkdir();override=root/"first_pass.pptx";out=root/"cohort"
            for task,name in TASK_FILENAMES.items():deck(initial/name,task)
            deck(override,"C01 initial repair baseline")
            deck_override=root/"deck_first_pass.pptx";deck(deck_override,"DECK01 initial baseline")
            for task,names in TASK_COMPANION_FILENAMES.items():
                for name in names:deck(initial/name,task+" companion initial")
            result=prepare(initial,out,{"C01_SEANet":override,"DECK01":deck_override})
            self.assertEqual(result["population"],15)
            self.assertEqual(Presentation(out/TASK_FILENAMES["C01_SEANet"]).slides[0].shapes[0].text,"C01 initial repair baseline")
            self.assertEqual(Presentation(out/TASK_FILENAMES["DECK01"]).slides[0].shapes[0].text,"DECK01 initial baseline")
            self.assertEqual(len(list(out.glob("*.pptx"))),16)
            self.assertTrue((out/"Q08_wine_strip.pptx").is_file())
            self.assertEqual(len(result["companions"]),1)
if __name__=="__main__":unittest.main()
