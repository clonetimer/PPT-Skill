import tempfile,unittest
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches
from fifteen_figure_review_packet import compare,TASKS,build_packet

def deck(p,text="Label"):
 prs=Presentation();s=prs.slides.add_slide(prs.slide_layouts[6]);sh=s.shapes.add_textbox(Inches(1),Inches(1),Inches(2),Inches(.5));sh.text=text;prs.save(p)
class ReviewPacketTests(unittest.TestCase):
 def test_identical_pptx_is_never_counted_as_repaired(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);a=p/"a.pptx";b=p/"b.pptx";deck(a);b.write_bytes(a.read_bytes())
   r=compare(a,b);self.assertTrue(r["byte_identical"]);self.assertEqual(r["changed_objects"],0)
 def test_changed_text_has_object_diff(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);a=p/"a.pptx";b=p/"b.pptx";deck(a,"Before");deck(b,"After")
   r=compare(a,b);self.assertFalse(r["byte_identical"]);self.assertGreater(r["changed_objects"],0)
 def test_exact_task_filenames_do_not_confuse_q03_with_nature_variant(self):
  from fifteen_figure_review_packet import TASK_FILENAMES
  self.assertEqual(TASK_FILENAMES["Q03"],"Q03_iris_mean_ci.pptx")
  self.assertEqual(TASK_FILENAMES["Q03P"],"Q03_iris_mean_ci_nature.pptx")
  self.assertEqual(len(TASK_FILENAMES),15)
 def test_packet_tracks_all_fifteen_without_fabricating_reviews(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);a=p/"initial";b=p/"final";o=p/"out";a.mkdir();b.mkdir()
   for task in TASKS:deck(a/(task+".pptx"))
   result=build_packet(a,b,o)
   self.assertEqual(result["population"],15);self.assertEqual(result["summary"]["missing"],15)
   self.assertTrue(all(t["final_review_status"]=="pending" for t in result["tasks"]))
if __name__=="__main__":unittest.main()
