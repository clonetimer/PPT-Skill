import tempfile,unittest
from pathlib import Path
from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches
from fifteen_figure_review_packet import compare,TASKS,build_packet,TASK_FILENAMES,TASK_FINAL_FILENAMES,TASK_COMPANION_FILENAMES

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
        self.assertEqual(TASK_FILENAMES["DECK01"],"DECK01_c01_defense.pptx")
        self.assertEqual(TASK_FINAL_FILENAMES["DECK01"],"DECK01_c01_defense_v76.pptx")
        self.assertEqual(TASK_COMPANION_FILENAMES["Q07"],("Q08_wine_strip.pptx",))
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


    def test_c01_composite_v74_initial_is_compared_with_v75_final(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);initial=root/"initial";final=root/"final";out=root/"out"
            initial.mkdir();final.mkdir()
            deck(initial/"C01_composite_defense_slide_v74.pptx","initial")
            deck(final/"C01_composite_defense_slide_v75.pptx","repaired")
            result=build_packet(initial,final,out)
        row=next(x for x in result["tasks"] if x["task_id"]=="C01_composite")
        self.assertEqual(row["status"],"REPAIR_COMPARISON_READY")
        self.assertEqual(row["initial"],"C01_composite_defense_slide_v74.pptx")
        self.assertEqual(row["final"],"C01_composite_defense_slide_v75.pptx")
        self.assertIn("figure_spec_diff",row["diff"])
        self.assertGreater(row["diff"]["figure_spec_diff"]["added"],0)


    def test_deck01_v75_initial_is_compared_with_v76_repair_and_deck_spec_diff(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);initial=root/"initial";final=root/"final";out=root/"out"
            initial.mkdir();final.mkdir()
            deck(initial/"DECK01_c01_defense.pptx","initial")
            deck(final/"DECK01_c01_defense_v76.pptx","repaired")
            result=build_packet(initial,final,out)
        row=next(x for x in result["tasks"] if x["task_id"]=="DECK01")
        self.assertEqual(row["status"],"REPAIR_COMPARISON_READY")
        self.assertEqual(row["initial"],"DECK01_c01_defense.pptx")
        self.assertEqual(row["final"],"DECK01_c01_defense_v76.pptx")
        self.assertIn("deck_spec_diff",row["diff"])
        self.assertGreater(row["diff"]["deck_spec_diff"]["changed_fields"],0)

    def test_packet_tracks_all_fifteen_without_fabricating_reviews(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);initial=root/"initial";final=root/"final";out=root/"out"
            initial.mkdir();final.mkdir()
            for task in TASKS:deck(initial/TASK_FILENAMES[task])
            for names in TASK_COMPANION_FILENAMES.values():
                for name in names:deck(initial/name)
            result=build_packet(initial,final,out)
        self.assertEqual(result["population"],15)
        self.assertEqual(result["summary"]["missing"],15)
        self.assertTrue(all(row["final_review_status"]=="pending" for row in result["tasks"]))
        self.assertTrue(all(row["diagnosis_status"] in {"NO_CONFIRMED_DEFECT","REPAIR_EXECUTED"} for row in result["tasks"]))
        self.assertTrue(all(row["diagnosis_note"] for row in result["tasks"]))


    def test_diagnosed_no_repair_tasks_are_marked_identical_not_repaired(self):
        from pathlib import Path
        import json
        from scientific_ir import ROOT
        ledger=json.loads((ROOT/"specs/15_figure_diagnostic_ledger_v76.json").read_text(encoding="utf-8"))
        no_repair={task for task,row in ledger["tasks"].items() if row["status"]=="NO_CONFIRMED_DEFECT"}
        repaired={task for task,row in ledger["tasks"].items() if row["status"]=="REPAIR_EXECUTED"}
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);initial=root/"initial";final=root/"final";out=root/"out"
            initial.mkdir();final.mkdir()
            for task in TASKS:
                first=initial/TASK_FILENAMES[task]
                last=final/TASK_FINAL_FILENAMES[task]
                deck(first,task+" initial")
                if task in no_repair:
                    last.write_bytes(first.read_bytes())
                else:
                    deck(last,task+" repaired")
            for task,names in TASK_COMPANION_FILENAMES.items():
                for name in names:
                    first=initial/name;last=final/name
                    deck(first,task+" companion")
                    last.write_bytes(first.read_bytes())
            result=build_packet(initial,final,out)
        rows={row["task_id"]:row for row in result["tasks"]}
        self.assertEqual(set(rows),set(TASKS))
        self.assertEqual(result["summary"]["no_repair_applied"],len(no_repair))
        self.assertEqual(result["summary"]["comparison_ready"],len(repaired))
        self.assertEqual(result["summary"]["missing"],0)
        for task in no_repair:
            self.assertEqual(rows[task]["status"],"NO_REPAIR_APPLIED")
            self.assertTrue(rows[task]["diff"]["byte_identical"])
            self.assertEqual(rows[task]["final_review_status"],"pending")
        self.assertEqual(rows["Q07"]["diff"]["companion_missing"],[])
        self.assertEqual(rows["Q07"]["diff"]["companion_artifacts"][0]["filename"],"Q08_wine_strip.pptx")
        for task in repaired:
            self.assertEqual(rows[task]["status"],"REPAIR_COMPARISON_READY")
            self.assertFalse(rows[task]["diff"]["byte_identical"])


    def test_object_rename_is_a_modified_object_not_remove_plus_add(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);before=root/"before.pptx";after=root/"after.pptx"
            deck(before,"same text");deck(after,"same text")
            prs=Presentation(before);prs.slides[0].shapes[0].name="source_object";prs.save(before)
            prs=Presentation(after);prs.slides[0].shapes[0].name="repaired_object";prs.save(after)
            result=compare(before,after)
        self.assertEqual(result["changed_objects"],1)
        self.assertEqual(result["object_diff"][0]["kind"],"modified")
        self.assertEqual(result["object_diff"][0]["fields"]["name"],
                         {"before":"source_object","after":"repaired_object"})

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
