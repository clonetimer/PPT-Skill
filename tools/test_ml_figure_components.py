"""Behavior checks for parameterized ML research-figure components."""
from __future__ import annotations

import unittest

from ml_figure_components import (
    ResidualLayer, addition_junction, crop_concat_pair, encoder_wedge,
    feature_map_strip, similarity_matrix, vector_fanout,
    residual_variant, token_strip, multihead_neighbor_bundle,
    multihead_self_loop, vector_math_label,
)


class Recorder:
    def __init__(self):self.elements=[]
    def add(self,kind,*args,**kwargs):self.elements.append((kind,args,kwargs))
    def rect(self,*a,**k):self.add("rect",*a,**k)
    def ellipse(self,*a,**k):self.add("ellipse",*a,**k)
    def polygon(self,*a,**k):self.add("polygon",*a,**k)
    def text(self,*a,**k):self.add("text",*a,**k)
    def line(self,*a,**k):self.add("line",*a,**k)


class TestComponents(unittest.TestCase):
    def setUp(self):self.c=Recorder()

    def test_feature_map_state_and_ports(self):
        item=feature_map_strip(self.c,sid="map",x=1,y=2,w=.2,h=1,
            channels=128,spatial_size="64×64",fill="#88AADD",stroke="#223344",
            label_color="#666666",dimension_side="right")
        self.assertEqual(item.port("bottom"),(1.1,3))
        self.assertLess(item.visual_bounds[0],item.bounds[0])
        self.assertLess(item.visual_bounds[1],item.bounds[1])
        self.assertEqual([e[1][7] if e[0]=="rect" else e[2].get("sid")
                          for e in self.c.elements if (e[0]=="rect" and len(e[1])>7) or e[2].get("sid")],
                         ["map","map_channels","map_dimension"])
        with self.assertRaises(ValueError):
            feature_map_strip(self.c,sid="bad",x=0,y=0,w=0,h=1,channels=1,
                spatial_size="1×1",fill="#FFFFFF",stroke="#111111",label_color="#111111")

    def test_crop_concat_has_two_distinct_input_ports(self):
        pair=crop_concat_pair(self.c,sid="L",x=2,y=1,h=1.2,channels_per_half=96,
            spatial_size="80×80",fill="#7799BB",stroke="#224466",label_color="#777777")
        self.assertNotEqual(pair.port("crop_in"),pair.port("upsample_in"))
        self.assertEqual(pair.port("crop_in"),(2,1.6))
        self.assertEqual(pair.port("upsample_in"),(2.14,2.2))
        self.assertLess(pair.visual_bounds[1],pair.bounds[1])
        fills=[e[1][4] for e in self.c.elements if e[0]=="rect"]
        self.assertEqual(fills,["#FFFFFF","#7799BB"])

    def test_encoder_and_addition_shapes(self):
        wedge=encoder_wedge(self.c,sid="encoder",x=1,y=1,w=1.2,h=1.4,
            label="Encoder",fill="#E4D8EB",stroke="#9974A8",taper=.25)
        add=addition_junction(self.c,sid="sum",x=3,y=1.2,diameter=.6,stroke="#111111")
        self.assertEqual(wedge.port("input"),(1,1.7))
        self.assertEqual(add.port("shortcut_in"),(3.6,1.5))
        points=self.c.elements[0][1][0]
        self.assertNotEqual(points[0][1],points[1][1])
        with self.assertRaises(ValueError):
            encoder_wedge(self.c,sid="bad",x=0,y=0,w=1,h=1,label="bad",
                          fill="#FFFFFF",stroke="#111111",taper=.5)

    def test_matrix_supports_variable_visible_members(self):
        matrix=similarity_matrix(self.c,sid="batch",x=2,y=2,cell_w=.4,cell_h=.5,
            indices=["1","2","…","n"],row_header_x=1.5,column_header_y=1.4,
            image_fill="#D9ECD7",image_stroke="#8DBB83",
            text_fill="#E4D8EB",text_stroke="#9974A8",
            match_fill="#D8E7FB",grid_stroke="#969696")
        cells=[e for e in self.c.elements if e[0]=="rect" and
               (e[1][7] or "").startswith("batch_cell_")]
        self.assertEqual(len(cells),16)
        self.assertEqual(sum(e[1][4]=="#D8E7FB" for e in cells),4)
        self.assertIn("row_3",matrix.ports)
        self.assertIn("column_3",matrix.ports)
        with self.assertRaises(ValueError):
            similarity_matrix(self.c,sid="bad",x=2,y=2,cell_w=.4,cell_h=.5,
                indices=["1","2","2","n"],row_header_x=1.5,column_header_y=1.4,
                image_fill="x",image_stroke="x",text_fill="x",text_stroke="x",
                match_fill="x",grid_stroke="x")

    def test_fanout_trunk_reaches_terminal_member(self):
        targets=[(2,2),(2,2.5),(2,3),(2,3.5)]
        vector_fanout(self.c,source=(.5,2.7),targets=targets,
                      trunk=1.6,orientation="right",color="#111111")
        lines=[e for e in self.c.elements if e[0]=="line"]
        self.assertEqual(sum(e[2].get("arrow",False) for e in lines),4)
        self.assertEqual(lines[1][1],(1.6,2,1.6,3.5))
        self.assertEqual(lines[-1][1],(1.6,3.5,2,3.5))

    def test_residual_variant_and_hostile_geometry(self):
        layers=[ResidualLayer("conv3×3",1.3,"#F0BD96"),
                ResidualLayer("dropout",1.3,"#E59DA5"),
                ResidualLayer("conv3×3",1.3,"#F0BD96")]
        item=residual_variant(self.c,sid="wide",x=.5,y=.5,layers=layers,
            layer_stroke="#555555",line_color="#111111",shortcut_fill="#D1D1D1",
            layer_gap=.20)
        self.assertIn("add",item.ports)
        self.assertLess(item.visual_bounds[1],item.bounds[1])
        self.assertEqual(sum(e[0]=="rect" for e in self.c.elements),3)
        self.assertEqual(sum(e[0]=="ellipse" for e in self.c.elements),1)
        for bad in (1.0,float("nan")):
            with self.assertRaises(ValueError):
                residual_variant(Recorder(),sid="bad",x=0,y=0,layers=layers,
                    layer_stroke="#555555",line_color="#111111",shortcut_fill="#D1D1D1",
                    panel_width=bad,layer_gap=.20)
        with self.assertRaises(ValueError):
            residual_variant(Recorder(),sid="bad",x=0,y=0,layers=layers,
                layer_stroke="#555555",line_color="#111111",shortcut_fill="#D1D1D1",
                layer_height=.05,layer_gap=.20)
        with self.assertRaises(ValueError):
            feature_map_strip(Recorder(),sid="bad",x=0,y=0,w=.2,h=1,channels=1.5,
                spatial_size="1×1",fill="#FFFFFF",stroke="#111111",label_color="#666666")
        with self.assertRaises(ValueError):
            encoder_wedge(Recorder(),sid="bad",x=0,y=0,w=.1,h=1,label="Encoder",
                          fill="#FFFFFF",stroke="#111111",taper=.2)
        with self.assertRaises(ValueError):
            encoder_wedge(Recorder(),sid="bad",x=0,y=0,w=1,h=.3,label="Encoder",
                          fill="#FFFFFF",stroke="#111111",taper=.1)
        with self.assertRaises(ValueError):
            encoder_wedge(Recorder(),sid="bad",x=0,y=0,w=2,h=2,
                          label="one\ntwo\nthree\nfour",fill="#FFFFFF",
                          stroke="#111111",taper=.1)
        with self.assertRaises(ValueError):
            addition_junction(Recorder(),sid="bad",x=0,y=0,diameter=.1,
                              stroke="#111111")
        with self.assertRaises(ValueError):
            similarity_matrix(Recorder(),sid="bad",x=2,y=2,cell_w=.01,cell_h=.5,
                indices=["1","2","…","n"],row_header_x=1.5,column_header_y=1.4,
                image_fill="x",image_stroke="x",text_fill="x",text_stroke="x",
                match_fill="x",grid_stroke="x")
        for panel_width,layer_width in ((2.9,2.04),(10,9)):
            bad_layers=[ResidualLayer("conv3×3",layer_width,"#F0BD96")]*2
            with self.assertRaises(ValueError):
                residual_variant(Recorder(),sid="bad",x=0,y=0,layers=bad_layers,
                    layer_stroke="#555555",line_color="#111111",shortcut_fill="#D1D1D1",
                    panel_width=panel_width)
        with self.assertRaises(ValueError):
            similarity_matrix(Recorder(),sid="bad",x=2,y=2,cell_w=.4,cell_h=.20,
                indices=["1","2","…","n"],row_header_x=1.5,column_header_y=1.4,
                image_fill="x",image_stroke="x",text_fill="x",text_stroke="x",
                match_fill="x",grid_stroke="x")
        invalid=Recorder()
        with self.assertRaises(ValueError):
            similarity_matrix(invalid,sid="bad",x=2,y=2,cell_w=.4,cell_h=.5,
                indices=["1","q","…","n"],row_header_x=1.5,column_header_y=1.4,
                image_fill="x",image_stroke="x",text_fill="x",text_stroke="x",
                match_fill="x",grid_stroke="x")
        self.assertEqual(invalid.elements,[])

    def test_matrix_instances_have_unique_semantic_ids(self):
        def make(sid):
            similarity_matrix(self.c,sid=sid,x=2,y=2,cell_w=.4,cell_h=.5,
                indices=["1","2","…","n"],row_header_x=1.5,column_header_y=1.4,
                image_fill="#D9ECD7",image_stroke="#8DBB83",
                text_fill="#E4D8EB",text_stroke="#9974A8",
                match_fill="#D8E7FB",grid_stroke="#969696")
        make("first");make("second")
        ids=[e[1][7] for e in self.c.elements if e[0]=="rect" and len(e[1])>7]
        self.assertEqual(len(ids),len(set(ids)))

    def test_coordinates_and_multidigit_batch_indices(self):
        with self.assertRaises(ValueError):
            feature_map_strip(Recorder(),sid="bad",x=float("nan"),y=0,w=.2,h=1,
                channels=16,spatial_size="32×32",fill="#FFFFFF",
                stroke="#111111",label_color="#666666")
        with self.assertRaises(ValueError):
            vector_fanout(Recorder(),source=(0,0),targets=[(2,1),(float("inf"),2)],
                          trunk=1,orientation="right",color="#111111")
        similarity_matrix(self.c,sid="long_batch",x=2,y=2,cell_w=.4,cell_h=.5,
            indices=["1","10","…","n"],row_header_x=1.5,column_header_y=1.4,
            image_fill="#D9ECD7",image_stroke="#8DBB83",
            text_fill="#E4D8EB",text_stroke="#9974A8",
            match_fill="#D8E7FB",grid_stroke="#969696")
        labels=[e[1][0] for e in self.c.elements if e[0]=="text"]
        self.assertIn("T₁₀",labels)

    def test_token_strip_and_multihead_graph_paths(self):
        strip=token_strip(self.c,sid="memory",x=1,y=1,count=5,box=.2,gap=.05,
                          fill="#FFFFFF",stroke="#111111",ellipsis_index=3)
        self.assertEqual(strip.port("top_0"),(1.1,1))
        self.assertEqual(len([e for e in self.c.elements if e[0]=="rect"]),4)
        self.assertIn("memory_ellipsis",[e[2].get("sid") for e in self.c.elements])
        before=len(self.c.elements)
        bundle=multihead_neighbor_bundle(self.c,sid="n2_to_n1",source=(1,3),
            target=(3,3),source_radius=.3,target_radius=.3,
            colors=["#2266CC","#228822","#AA22CC"])
        lines=[e for e in self.c.elements[before:] if e[0]=="line"]
        self.assertEqual(len(lines),48)
        self.assertEqual(sum(e[2].get("arrow",False) for e in lines),3)
        self.assertGreater(bundle.port("source")[0],1)
        before=len(self.c.elements)
        loop=multihead_self_loop(self.c,sid="self",center=(4,3),node_radius=.3,
                                 colors=["#2266CC","#228822","#AA22CC"])
        self.assertEqual(loop.port("start"),(4+.3*.28,3-.3*.96))
        self.assertEqual(sum(e[2].get("arrow",False) for e in self.c.elements[before:]),3)
        with self.assertRaises(ValueError):
            multihead_neighbor_bundle(Recorder(),sid="bad",source=(0,0),target=(.2,0),
                source_radius=.3,target_radius=.3,colors=["red","blue"])

    def test_group_outline_and_math_vector_label(self):
        group=token_strip(self.c,sid="batch",x=1,y=1,count=4,box=.2,gap=.05,
                          fill="#FFFFFF",stroke="#111111",group_outline=True)
        self.assertEqual(group.port("group_left"),(.94,1.1))
        self.assertEqual(self.c.elements[0][1][7],"batch_group")
        label=vector_math_label(self.c,sid="h1",text="h₁",x=2,y=2,w=.4,h=.25)
        self.assertEqual(label.visual_bounds[1],label.bounds[1])
        self.assertEqual(self.c.elements[-4][2].get("sid"),"h1")


if __name__=="__main__":unittest.main()
