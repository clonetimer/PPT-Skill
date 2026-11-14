import tempfile,unittest
from pathlib import Path
from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches
from fifteen_figure_review_packet import compare,TASKS,build_packet,TASK_FILENAMES,TASK_FINAL_FILENAMES

def deck(path,text="Label"):
    prs=Presentation()
    slide=prs.slides.add_slide(prs.slide_layouts[6])
    shape=slide.shapes.add_textbox(Inches(1),Inches(1),Inches(2),Inches(.5))
    shape.text=text
    prs.save(path)

class ReviewPacketTests(unittest.TestCase):
    def test_identical_pptx_is_never_counted_as_repaired(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);a=root/"a.pptx";b=root/"b.pptx"
            deck(a);b.write_bytes(a.read_bytes())
            result=compare(a,b)
        self.assertTrue(result["byte_identical"])
        self.assertEqual(result["changed_objects"],0)

    def test_changed_text_has_object_diff(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);a=root/"a.pptx";b=root/"b.pptx"
            deck(a,"Before");deck(b,"After")
            result=compare(a,b)
        self.assertFalse(result["byte_identical"])
        self.assertGreater(result["changed_objects"],0)

    def test_exact_task_filenames_do_not_confuse_q03_with_nature_variant(self):
        self.assertEqual(TASK_FILENAMES["Q03"],"Q03_iris_mean_ci.pptx")
        self.assertEqual(TASK_FILENAMES["Q03P"],"Q03_iris_mean_ci_nature.pptx")
        self.assertEqual(TASK_FILENAMES["C01_SEANet"],"C01_SEANet_graph_level_v73.pptx")
        self.assertEqual(TASK_FINAL_FILENAMES["C01_SEANet"],"C01_SEANet_graph_level_v74.pptx")
        self.assertEqual(TASK_FILENAMES["C01_composite"],"C01_composite_defense_slide_v74.pptx")
        self.assertEqual(TASK_FINAL_FILENAMES["C01_composite"],"C01_composite_defense_slide_v75.pptx")
        self.assertEqual(len(TASK_FILENAMES),15)


    def test_c01_seanet_v73_initial_is_compared_with_v74_final(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);initial=root/"initial";final=root/"final";out=root/"out"
            initial.mkdir();final.mkdir()
            deck(initial/"C01_SEANet_graph_level_v73.pptx","initial")
            deck(final/"C01_SEANet_graph_level_v74.pptx","repaired")
            result=build_packet(initial,final,out)
        row=next(x for x in result["tasks"] if x["task_id"]=="C01_SEANet")
        self.assertEqual(row["status"],"REPAIR_COMPARISON_READY")
        self.assertEqual(row["initial"],"C01_SEANet_graph_level_v73.pptx")
        self.assertEqual(row["final"],"C01_SEANet_graph_level_v74.pptx")
        self.assertIn("figure_spec_diff",row["diff"])
        self.assertGreater(row["diff"]["figure_spec_diff"]["added"],0)
        self.assertGreater(row["diff"]["figure_spec_diff"]["modified"],0)

    def test_packet_tracks_all_fifteen_without_fabricating_reviews(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);initial=root/"initial";final=root/"final";out=root/"out"
            initial.mkdir();final.mkdir()
            for task in TASKS:deck(initial/(task+".pptx"))
            result=build_packet(initial,final,out)
        self.assertEqual(result["population"],15)
        self.assertEqual(result["summary"]["missing"],15)
        self.assertTrue(all(row["final_review_status"]=="pending" for row in result["tasks"]))

    def test_alignment_only_repair_is_included_in_object_diff(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);initial=root/"initial.pptx";final=root/"final.pptx"
            deck(initial,"fault class");deck(final,"fault class")
            initial_prs=Presentation(initial)
            initial_prs.slides[0].shapes[0].text_frame.paragraphs[0].alignment=PP_ALIGN.CENTER
            initial_prs.save(initial)
            prs=Presentation(final)
            prs.slides[0].shapes[0].text_frame.paragraphs[0].alignment=PP_ALIGN.CENTER
            prs.slides[0].shapes[0].text_frame.paragraphs[0].alignment=PP_ALIGN.RIGHT
            prs.save(final)
            result=compare(initial,final)
        self.assertEqual(result["changed_objects"],1)
        self.assertEqual(result["object_diff"][0]["fields"]["paragraph_alignments"],{"before":[2],"after":[3]})

if __name__=="__main__":
    unittest.main()
