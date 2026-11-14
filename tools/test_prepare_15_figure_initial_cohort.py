import tempfile,unittest
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches
from prepare_15_figure_initial_cohort import prepare
from fifteen_figure_review_packet import TASK_FILENAMES

def deck(path,label):
    p=Presentation();s=p.slides.add_slide(p.slide_layouts[6]);s.shapes.add_textbox(Inches(1),Inches(1),Inches(2),Inches(.5)).text=label;p.save(path)
class PrepareInitialCohortTests(unittest.TestCase):
    def test_c01_override_is_used_and_all_15_tasks_are_copied(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);initial=root/"initial";initial.mkdir();override=root/"first_pass.pptx";out=root/"cohort"
            for task,name in TASK_FILENAMES.items():deck(initial/name,task)
            deck(override,"C01 initial repair baseline")
            result=prepare(initial,out,{"C01_SEANet":override})
            self.assertEqual(result["population"],15)
            self.assertEqual(Presentation(out/TASK_FILENAMES["C01_SEANet"]).slides[0].shapes[0].text,"C01 initial repair baseline")
            self.assertEqual(len(list(out.glob("*.pptx"))),15)
if __name__=="__main__":unittest.main()
