from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from figurelib import Figure
from ml_figure_components import encoder_wedge, similarity_matrix

F=Figure(HERE,"MLC01_clip_overview",16,6.45,
  "CLIP Figure 1: paired contrastive pretraining, classifier synthesis from label text, and zero-shot prediction",
  "https://proceedings.mlr.press/v139/radford21a/radford21a.pdf","Figure 1, PDF page 2",
  ["The dog photograph is a CC0 replacement, not the paper's original photograph.",
   "Layout and scientific visual grammar are source-based; exact typeface and photograph are not pixel-identical."])
F.asset(HERE/"dog_cc0.jpg","https://commons.wikimedia.org/wiki/File:Golden-retriever-dog.jpg",
        "CC0 1.0","Karen Arnold")
black="#303030"; gray="#969696"; purple="#e4d8eb"; ps="#9974a8"; green="#d9ecd7"; gs="#8dbb83"; blue="#d8e7fb"

def txt(t,x,y,w,h,size=10,**kw):return F.text(t,x,y,w,h,size=size,**kw)
def rect(x,y,w,h,fill="#ffffff",stroke=gray,sid=None,sw=.7):return F.rect(x,y,w,h,fill,stroke,sw,sid)
def arrow(x1,y1,x2,y2,sw=.8):F.line(x1,y1,x2,y2,color=black,sw=sw,arrow=True)
def enc(x,y,w,h,label,kind,sid):
    return encoder_wedge(F,sid=sid,x=x,y=y,w=w,h=h,label=label,
                         fill=purple if kind=="text" else green,
                         stroke=ps if kind=="text" else gs,
                         taper=.28 if kind=="text" else .27)

txt("(1) Contrastive pre-training",.22,.18,7.4,.36,15,align="left")
txt("(2) Create dataset classifier from label text",8.08,.18,7.7,.36,15,align="left")
txt("(3) Use for zero-shot prediction",8.08,3.35,7.7,.36,15,align="left")

# The paper's stacked cards/images represent a batch; every scientific mark remains editable.
for d in [(.17,.17),(.11,.11),(.05,.05),(0,0)]:
    rect(.25+d[0],1.0+d[1],1.44,.69,"#ffffff",gray,sw=.75)
txt("A golden\nretriever",.35,1.11,1.28,.47,9,font="Courier New",sid="caption_batch")
enc(2.1,.79,1.3,1.45,"Text\nEncoder","text","train_text_encoder")
F.route("caption_batch","train_text_encoder",[(1.69,1.35),(2.1,1.35)],black)
for i in range(3,-1,-1):
    F.image(HERE/"dog_cc0.jpg",.47+i*.055,4.03+i*.05,.76,.72,sid="image_batch" if i==0 else None)
enc(2.1,3.93,1.3,1.45,"Image\nEncoder","image","train_image_encoder")
F.route("image_batch","train_image_encoder",[(1.40,4.48),(2.1,4.48)],black)

# Purple text embeddings are columns, green image embeddings are rows.
tx=5.13; ty=2.1; cw=.55; ch=.55; mx=5.13; my=2.86
matrix=similarity_matrix(F,sid="train_matrix",x=mx,y=my,cell_w=cw,cell_h=ch,
    indices=["1","2","3","…","n"],row_header_x=4.47,column_header_y=ty,
    image_fill=green,image_stroke=gs,text_fill=purple,text_stroke=ps,
    match_fill=blue,grid_stroke=gray,cell_prefix="matrix_cell",text_vectors_id="train_text_vectors",
    image_vectors_id="train_image_vectors")
F.route("train_text_encoder","train_text_vectors",[(3.40,1.40),(7.60,1.40),(7.60,1.86),(5.405,1.86),(5.405,2.10)],black)
for j in (1,2,4):
    cx=tx+(j+.5)*cw
    F.line(cx,1.86,cx,2.10,color=black,sw=.75,arrow=True)
F.route("train_image_encoder","train_image_vectors",[(3.4,4.65),(4.17,4.65),(4.17,3.135),(4.47,3.135)],black)
F.line(4.17,4.65,4.17,5.335,color=black,sw=.75)
F.line(4.17,4.785,4.47,4.785,color=black,sw=.75,dash=True)
for i in (1,2,4):
    cy=my+(i+.5)*ch
    F.line(4.17,cy,4.47,cy,color=black,sw=.75,arrow=True)
F.route("train_text_vectors","train_matrix",[(5.405,2.65),(5.405,2.86)],black)
for j in (1,2,4):
    cx=tx+(j+.5)*cw
    F.line(cx,2.65,cx,2.86,color=black,sw=.75,arrow=True)
F.route("train_image_vectors","train_matrix",[(5.02,3.135),(5.13,3.135)],black)
for i in (1,2,4):
    cy=my+(i+.5)*ch
    F.line(5.02,cy,5.13,cy,color=black,sw=.75,arrow=True)

# Right upper: zero-shot class vectors produced by prompting, not a learned new head.
for i,s in enumerate(["plane","car","dog","⋮","bird"]):
    y=.83+i*.39
    rect(8.13,y,.78,.39,"#ffffff",gray,sid="class_labels" if i==2 else None)
    txt(s,8.14,y+.07,.76,.22,9.3,color=ps,font="Courier New")
F.line(8.93,1.03,9.23,1.03,color=black);F.line(9.23,1.03,9.23,2.40,color=black)
F.line(8.93,2.40,9.23,2.40,color=black)
rect(9.63,1.34,1.45,.68,"#ffffff",black,sid="prompt",sw=.9)
txt("A photo of\na {object}.",9.68,1.47,1.35,.45,10,font="Courier New")
enc(11.46,.82,1.32,1.55,"Text\nEncoder","text","class_text_encoder")
F.route("class_labels","prompt",[(8.91,1.80),(9.23,1.80),(9.23,1.61),(9.63,1.61)],black)
F.route("prompt","class_text_encoder",[(11.08,1.68),(11.46,1.68)],black)
vx=12.62; vy=3.89; vw=.55
F.rect(vx,vy,5*vw,.48,purple,ps,.8,"class_vectors")
for j,s in enumerate(["T₁","T₂","T₃","···","Tₙ"]):
    if j:F.line(vx+j*vw,vy,vx+j*vw,vy+.48,color=ps,sw=.6)
    txt(s,vx+j*vw,vy+.12,vw,.22,10.4)
F.route("class_text_encoder","class_vectors",[(12.78,1.60),(15.09,1.60),(15.09,3.68),(12.895,3.68),(12.895,3.89)],black)
for j in (1,2,4):
    cx=vx+(j+.5)*vw
    F.line(cx,3.68,cx,3.89,color=black,sw=.75,arrow=True)

# Right lower: one query image and all text class vectors meet only at similarity scores.
F.image(HERE/"dog_cc0.jpg",8.68,4.33,.88,.78,sid="query_image")
enc(10.0,4.12,1.32,1.30,"Image\nEncoder","image","query_image_encoder")
F.route("query_image","query_image_encoder",[(9.56,4.72),(10.0,4.72)],black)
rect(11.67,4.54,.57,.42,green,gs,sid="query_vector")
txt("I₁",11.67,4.64,.57,.23,10)
F.route("query_image_encoder","query_vector",[(11.32,4.76),(11.67,4.76)],black)
sx=12.62;sy=4.54;sw=.55
F.rect(sx,sy,5*sw,.42,"#ffffff",gray,.7,"score_row")
for j,s in enumerate(["I₁·T₁","I₁·T₂","I₁·T₃","···","I₁·Tₙ"]):
    if j==2:rect(sx+j*sw,sy,sw,.42,blue,gray,sw=.6)
    elif j: F.line(sx+j*sw,sy,sx+j*sw,sy+.42,color=gray,sw=.5)
    txt(s,sx+j*sw,sy+.1,sw,.22,8.7)
F.route("query_vector","score_row",[(12.24,4.75),(12.62,4.75)],black)
F.route("class_vectors","score_row",[(12.895,4.37),(12.895,4.54)],black)
for j in (1,2,4):
    cx=vx+(j+.5)*vw
    F.line(cx,4.37,cx,4.54,color=black,sw=.75,arrow=True)
rect(13.25,5.65,1.50,.49,"#ffffff",black,sid="prediction",sw=.8)
txt("A photo of\na dog.",13.31,5.69,1.38,.4,9.2,font="Courier New")
F.route("score_row","prediction",[(14.00,4.96),(14.00,5.65)],black)

F.finish(HERE/"expected_topology.json")
