"""Small FigureSpec authoring helper for source-figure fidelity trials."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import jsonschema

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"tools"))
from render_figure_spec import render  # noqa: E402
from scientific_ir import CONTRACTS,enrich_spec,validate_drawn_routes,validate_spec  # noqa: E402

SCHEMA=json.loads((ROOT/"specs/figure_spec_v76.schema.json").read_text(encoding="utf-8"))

class Figure:
    def __init__(self,folder:Path,id:str,w:float,h:float,claim:str,source_url:str,locator:str,
                 unverified=None,embedded_source_excerpt=False):
        self.folder=folder;self.id=id;self.w=w;self.h=h;self.e=[];self.edges=[];self.assets={}
        source=folder/"paper.pdf"
        assert source.exists()
        CONTRACTS[id]={"claim":claim,"archetype":"schematic_led_composite","output_mode":"presentation",
            "unverified":unverified or ["Source-composition study; no claim of pixel identity or journal acceptance."],
            "source":str(source.relative_to(ROOT)).replace("\\","/"),
            "source_locator":locator+"; SHA-256 "+hashlib.sha256(source.read_bytes()).hexdigest(),
            "evidence_status":"source_visible_redraw","evidence_scope":"Paper figure and caption; critical topology and visual grammar",
            "reuse":("Editable method redraw with a cited source-paper excerpt in a result image panel."
                     if embedded_source_excerpt else
                     "New editable scholarly redraw; original paper figure is not embedded.")}
    def add(self,type,**kw):
        z={"type":type,**kw};self.e.append(z);return z
    def text(self,s,x,y,w,h,size=10,align="center",color="#222222",bold=False,rotation=0,sid=None,font=None):
        z=dict(text=s,x=x,y=y,w=w,h=h,size=size,align=align,color=color,bold=bold)
        if rotation:z["rotation"]=rotation
        if sid:z["semantic_id"]=sid
        if font:z["font"]=font
        return self.add("text",**z)
    def rect(self,x,y,w,h,fill="#FFFFFF",stroke="#222222",sw=.8,sid=None,dash=False):
        z=dict(x=x,y=y,w=w,h=h,fill=fill,stroke=stroke,sw=sw,radius=0)
        if sid:z["semantic_id"]=sid
        if dash:z["dash"]=True
        return self.add("rect",**z)
    def ellipse(self,x,y,w,h,fill="#FFFFFF",stroke="#222222",sw=.8,sid=None):
        z=dict(x=x,y=y,w=w,h=h,fill=fill,stroke=stroke,sw=sw)
        if sid:z["semantic_id"]=sid
        return self.add("ellipse",**z)
    def polygon(self,points,fill="#FFFFFF",stroke="#222222",sw=.8,sid=None):
        z=dict(points=points,fill=fill,stroke=stroke,sw=sw)
        if sid:z["semantic_id"]=sid
        return self.add("polygon",**z)
    def line(self,x1,y1,x2,y2,color="#333333",sw=.9,arrow=False,dash=False,
             link=None,arrow_size=None,head_id=None):
        z=dict(x1=x1,y1=y1,x2=x2,y2=y2,color=color,sw=sw,arrow=arrow)
        if dash:z["dash"]=True
        if link:z["semantic_link"]=link
        if arrow_size is not None:z["arrow_size"]=arrow_size
        if head_id:z["head_id"]=head_id
        return self.add("line",**z)
    def route(self,a,b,points,color="#333333",sw=.9,dash=False,
              arrow_size=None,head_id=None):
        self.edges.append((a,b))
        for i,(p,q) in enumerate(zip(points[:-1],points[1:])):
            self.line(*p,*q,color=color,sw=sw,arrow=i==len(points)-2,dash=dash,
                      link=f"{a}__{b}",arrow_size=arrow_size,head_id=head_id)
    def image(self,path,x,y,w,h,sid=None):
        z=dict(path=str(path.relative_to(ROOT)).replace("\\","/"),x=x,y=y,w=w,h=h)
        if sid:z["semantic_id"]=sid
        return self.add("image",**z)
    def asset(self,path:Path,source_url:str,license:str,author:str,
              status="source_visible_redraw",scope=None,reuse=None):
        rel=str(path.relative_to(ROOT)).replace("\\","/")
        self.assets[rel]={"id":"asset_"+str(len(self.assets)+1),"source":rel,
            "source_file_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
            "source_locator":source_url+"; author "+author+"; license "+license,
            "status":status,
            "scope":scope or "Illustrative replacement image; not evidence for model operations",
            "reuse":reuse or license+"; photograph substituted with attribution recorded"}
    def finish(self,fixture_path:Path,font="Arial",allow_unchecked_first_pass=False):
        fixture=json.loads(fixture_path.read_text(encoding="utf-8"))
        expected={tuple(x) for x in fixture.get("required_edges",[])}
        if not expected and not allow_unchecked_first_pass:
            raise ValueError("Source-grounded method figure requires nonempty critical routes")
        assert fixture["figure_id"]==self.id
        assert set(self.edges)==expected,(self.id,set(self.edges)^expected)
        ids={e.get("semantic_id") for e in self.e}
        assert set(fixture.get("required_nodes",[]))<=ids
        spec=enrich_spec({"id":self.id,"title":self.id,"canvas":{"width_in":self.w,"height_in":self.h},
                          "style":{"font":font},"semantic_edges":[list(x) for x in self.edges],"elements":self.e})
        for path,record in self.assets.items():
            spec["evidence_records"].append(record)
            for e in spec["elements"]:
                if e["type"]=="image" and e["path"]==path:e["evidence_ref"]=record["id"]
        jsonschema.validate(spec,SCHEMA);validate_spec(spec)
        if expected:validate_drawn_routes(spec,expected)
        (self.folder/(self.id+".json")).write_text(json.dumps(spec,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        render(spec,self.folder/(self.id+".svg"),self.folder/(self.id+".pptx"))
        print(f"Rendered {self.id}: {len(self.e)} elements, {len(self.edges)} critical routes")
        return spec
