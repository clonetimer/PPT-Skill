"""Execute the first non-destructive C01-SEANet repair case."""
from __future__ import annotations
import argparse,hashlib,json,shutil
from pathlib import Path
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from render_figure_spec import render
from local_repair_loop import run_repair_loop

ROOT=Path(__file__).resolve().parents[1]
INITIAL_SPEC=ROOT/"tests/fixtures/C01_SEANet_graph_level_initial_v73.json"
FINAL_SPEC=ROOT/"figure_specs/c01/C01_SEANet_graph_level.json"
TARGET_ID="el_0052"
TARGET_TEXT="fault class"

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def _cnvpr(shape):
    nodes=[n for n in shape._element.iter() if n.tag.endswith("}cNvPr")]
    if not nodes:raise ValueError("SHAPE_HAS_NO_CNVPR")
    return nodes[0]
def _box(shape):
    if shape.width<=0 or shape.height<=0:return None
    return [shape.left.pt,shape.top.pt,shape.left.pt+shape.width.pt,shape.top.pt+shape.height.pt]
def _class(shape):
    if shape.shape_type==MSO_SHAPE_TYPE.PICTURE:return "image"
    if shape.has_text_frame and shape.text.strip():return "text"
    return "vector"
def _annotate_and_manifest(pptx_path,spec_path,manifest_path):
    spec=json.loads(Path(spec_path).read_text(encoding="utf-8"))
    target=next((e for e in spec["elements"] if e.get("id")==TARGET_ID),None)
    if not target or target.get("text")!=TARGET_TEXT or target.get("align")!="center":
        raise ValueError("INITIAL_SPEC_TARGET_PRECONDITION_FAILED")
    prs=Presentation(pptx_path)
    if len(prs.slides)!=1:raise ValueError("C01_SEANET_EXPECTS_SINGLE_SLIDE")
    shapes=list(prs.slides[0].shapes)
    matches=[s for s in shapes if s.has_text_frame and s.text.strip()==TARGET_TEXT]
    if len(matches)!=1:raise ValueError("TARGET_TEXT_NOT_UNIQUE")
    target_shape=matches[0]
    expected=[target["x"]*72,target["y"]*72,(target["x"]+target["w"])*72,(target["y"]+target["h"])*72]
    actual=_box(target_shape)
    if actual is None or any(abs(a-b)>0.1 for a,b in zip(actual,expected)):
        raise ValueError("TARGET_GEOMETRY_DOES_NOT_MATCH_FIGURE_SPEC")
    records=[]
    for index,shape in enumerate(shapes):
        cls=_class(shape);sid=TARGET_ID if shape is target_shape else f"pptx_shape_{index:03d}"
        shape.name=sid
        _cnvpr(shape).set("descr",json.dumps({"source_object_id":sid,"source_order":index,
            "object_class":cls,"provenance":"figure_spec_repair_case"},sort_keys=True,separators=(",",":")))
        treatment={"text":"editable_text","vector":"editable_vector","image":"picture_asset"}[cls]
        item={"source_object_id":sid,"source_order":index,"object_class":cls,"kind":cls,
              "treatment":treatment,"bbox_pt":_box(shape)}
        if cls=="text":
            item["text"]=shape.text
            item["font_size_pt"]=[float(r.font.size.pt) for p in shape.text_frame.paragraphs for r in p.runs if r.font.size]
        records.append(item)
    prs.save(pptx_path)
    manifest={"schema_version":"1.0.0","status":"COMPOSITION_PLAN_READY",
      "source":{"filename":Path(spec_path).name,"sha256":sha(spec_path),"page_index":0,
                "figure_region_pt":[0.0,0.0,float(spec["canvas"]["width_in"])*72,float(spec["canvas"]["height_in"])*72]},
      "provenance":{"figure_spec_sha256":sha(spec_path),"source_kind":"editable_figure_spec_baseline"},
      "composition_units":[{"unit_id":"C01_SEANet","scope":"figure","recommended_route":"native_vector","objects":records}],
      "policy":{"execution_authorized":False,"scientific_relations_verified":False,"each_source_object_represented_once":True}}
    Path(manifest_path).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return manifest

def _alignments(shape):
    if not shape.has_text_frame:return []
    out=[]
    for p in shape.text_frame.paragraphs:
        v=p.alignment
        out.append(None if v is None else int(v))
    return out

def compare_reference(repaired,reference):
    a=Presentation(repaired);b=Presentation(reference)
    if len(a.slides)!=1 or len(b.slides)!=1:raise ValueError("REFERENCE_EXPECTS_ONE_SLIDE")
    aa=list(a.slides[0].shapes);bb=list(b.slides[0].shapes);m=[]
    if len(aa)!=len(bb):m.append({"field":"shape_count","repair":len(aa),"reference":len(bb)})
    for i,(x,y) in enumerate(zip(aa,bb)):
        fields={}
        for k in ("left","top","width","height","rotation"):
            if getattr(x,k)!=getattr(y,k):fields[k]={"repair":getattr(x,k),"reference":getattr(y,k)}
        if (x.text if x.has_text_frame else None)!=(y.text if y.has_text_frame else None):
            fields["text"]="mismatch"
        if _alignments(x)!=_alignments(y):fields["alignment"]={"repair":_alignments(x),"reference":_alignments(y)}
        if x.has_text_frame and y.has_text_frame:
            xf=[(r.text,r.font.name,r.font.size.pt if r.font.size else None,r.font.bold,r.font.italic) for p in x.text_frame.paragraphs for r in p.runs]
            yf=[(r.text,r.font.name,r.font.size.pt if r.font.size else None,r.font.bold,r.font.italic) for p in y.text_frame.paragraphs for r in p.runs]
            if xf!=yf:fields["font_runs"]="mismatch"
        if fields:m.append({"shape_index":i,"fields":fields})
    return {"status":"PASS" if not m else "FAIL","shape_count":len(aa),"mismatches":m}

def run_case(output_dir,accepted_output=None):
    output_dir=Path(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):raise ValueError("REPAIR_CASE_OUTPUT_DIR_MUST_BE_EMPTY")
    output_dir.mkdir(parents=True,exist_ok=True)
    initial_spec=json.loads(INITIAL_SPEC.read_text(encoding="utf-8"))
    initial_svg=output_dir/"initial.svg";initial_pptx=output_dir/"initial_unannotated.pptx"
    render(initial_spec,initial_svg,initial_pptx);initial_hash=sha(initial_pptx)
    annotated=output_dir/"annotated_first_pass.pptx";shutil.copy2(initial_pptx,annotated)
    manifest=output_dir/"composition_manifest.json";_annotate_and_manifest(annotated,INITIAL_SPEC,manifest)
    plan={"schema_version":"1.0.0","repair_case":"C01_SEANet_first_local_repair",
      "rounds":[{"round":1,"rationale":"The fault-class label is visually left-shifted relative to the output glyph. Right-aligning the existing text to its text-box right edge improves alignment without changing text, font, size, geometry, or scientific topology.",
        "operations":[{"source_object_id":TARGET_ID,"operation":"set_alignment","expected_text":TARGET_TEXT,
                       "expected_alignment":"center","alignment":"right"}]}]}
    plan_path=output_dir/"repair_plan.json";plan_path.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    history=run_repair_loop(annotated,plan_path,manifest,output_dir/"rounds",max_rounds=1)
    if history["accepted_rounds"]!=1 or history["rejected_rounds"]!=0:raise RuntimeError("C01_REPAIR_ROUND_NOT_ACCEPTED")
    repaired=Path(history["final_path"])
    final_spec=json.loads(FINAL_SPEC.read_text(encoding="utf-8"))
    reference_svg=output_dir/"final_reference.svg";reference_pptx=output_dir/"final_reference.pptx"
    render(final_spec,reference_svg,reference_pptx)
    parity=compare_reference(repaired,reference_pptx)
    if parity["status"]!="PASS":raise RuntimeError("REPAIRED_PPTX_DIFFERS_FROM_FINAL_FIGURE_SPEC")
    if accepted_output:
        Path(accepted_output).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(repaired,accepted_output)
    diff=history["repair_history"][0]["object_diff"]
    summary={"case":"C01_SEANet","status":"REPAIR_EXECUTED_AND_AUDITED","target_source_object_id":TARGET_ID,
      "target_text":TARGET_TEXT,"initial_unannotated_sha256":initial_hash,
      "annotated_first_pass_sha256":history["first_pass_sha256"],"final_repaired_sha256":history["final_sha256"],
      "accepted_rounds":history["accepted_rounds"],"rejected_rounds":history["rejected_rounds"],
      "quality_status":history["final_quality_status"],"object_diff":diff,"spec_parity":parity,
      "scientific_topology_changed":False,"font_or_geometry_changed":False,"human_final_review":"PENDING",
      "source_limit":"Repair manifest is based on the editable FigureSpec baseline, not the publisher PDF; quality audit proves no unintended PPTX regressions, not source-image fidelity."}
    (output_dir/"repair_case_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (output_dir/"object_diff.json").write_text(json.dumps(diff,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return summary

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--output-dir",type=Path,required=True);p.add_argument("--accepted-output",type=Path)
    a=p.parse_args();r=run_case(a.output_dir,a.accepted_output);print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
