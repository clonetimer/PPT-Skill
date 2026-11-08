"""Reusable, editable components for source-grounded ML paper figures.

Coordinates are inches. Components emit FigureSpec primitives through a small
canvas sink (the trial Figure helper is one such sink). Source-specific layout,
colors and labels remain caller parameters; the component owns its geometry,
ports and local semantic checks.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Protocol, Sequence

Point = tuple[float, float]


class Canvas(Protocol):
    def rect(self, x, y, w, h, fill="#FFFFFF", stroke="#222222", sw=.8, sid=None, dash=False): ...
    def ellipse(self, x, y, w, h, fill="#FFFFFF", stroke="#222222", sw=.8, sid=None): ...
    def polygon(self, points, fill="#FFFFFF", stroke="#222222", sw=.8, sid=None): ...
    def text(self, s, x, y, w, h, size=10, align="center", color="#222222",
             bold=False, rotation=0, sid=None, font=None): ...
    def line(self, x1, y1, x2, y2, color="#333333", sw=.9, arrow=False, dash=False,
             link=None, arrow_size=None, head_id=None): ...


@dataclass(frozen=True)
class Component:
    semantic_id: str
    ports: Mapping[str, Point]
    bounds: tuple[float, float, float, float]
    visual_bounds: tuple[float, float, float, float] | None = None

    def port(self, name: str) -> Point:
        return self.ports[name]

    def __post_init__(self) -> None:
        if self.visual_bounds is None:
            object.__setattr__(self,"visual_bounds",self.bounds)


@dataclass(frozen=True)
class ResidualLayer:
    label: str
    width: float
    fill: str


def _positive(*values: float) -> None:
    if any(not isinstance(v,(int,float)) or isinstance(v,bool) or
           not math.isfinite(v) or v <= 0 for v in values):
        raise ValueError("Component dimensions and scale must be positive")


def _finite(*values: float) -> None:
    if any(not isinstance(v,(int,float)) or isinstance(v,bool) or
           not math.isfinite(v) for v in values):
        raise ValueError("Component coordinates must be finite")


def _union_boxes(*boxes: tuple[float,float,float,float]) -> tuple[float,float,float,float]:
    left=min(box[0] for box in boxes);top=min(box[1] for box in boxes)
    right=max(box[0]+box[2] for box in boxes)
    bottom=max(box[1]+box[3] for box in boxes)
    return (left,top,right-left,bottom-top)


def feature_map_strip(canvas: Canvas, *, sid: str, x: float, y: float, w: float,
                      h: float, channels: int, spatial_size: str, fill: str,
                      stroke: str, label_color: str, white: bool = False,
                      show_channel: bool = True, show_dimension: bool = True,
                      dimension_side: str = "left", dimension_band: str = "below",
                      channel_font_pt: float = 8.5,
                      dimension_font_pt: float = 7.7) -> Component:
    """One feature-map state; dimensions and channels stay attached to its ID."""
    _positive(w, h, channel_font_pt, dimension_font_pt)
    _finite(x,y)
    if type(channels) is not int or channels < 1 or not spatial_size:
        raise ValueError("A feature map needs channels and a spatial size")
    if dimension_side not in {"left", "right"} or dimension_band not in {"below", "inside"}:
        raise ValueError("dimension_side/band must name a supported label lane")
    visual=(x,y,w,h)
    canvas.rect(x, y, w, h, "#FFFFFF" if white else fill, stroke, .65, sid)
    if show_channel:
        label_w = .38 if channels >= 1000 else .30
        visual=_union_boxes(visual,(x+w/2-label_w/2,y-.35,label_w,.20))
        canvas.text(str(channels), x+w/2-label_w/2, y-.35, label_w, .20,
                    channel_font_pt, color=label_color, sid=f"{sid}_channels")
    if show_dimension:
        dim_x = x-.43 if dimension_side == "left" else x-.07
        dim_y = y+h*.75-.10 if dimension_band == "inside" else y+h+.17
        # The text box rotates by 90 degrees about its center.
        visual=_union_boxes(visual,(dim_x+.17,dim_y-.17,.20,.54))
        canvas.text(spatial_size, dim_x, dim_y, .54, .20, dimension_font_pt,
                    color=label_color, rotation=-90, sid=f"{sid}_dimension")
    return Component(sid, {"left":(x,y+h/2), "right":(x+w,y+h/2),
                           "top":(x+w/2,y), "bottom":(x+w/2,y+h),
                           "center":(x+w/2,y+h/2)}, (x,y,w,h),visual)


def crop_concat_pair(canvas: Canvas, *, sid: str, x: float, y: float, h: float,
                     channels_per_half: int, spatial_size: str,
                     fill: str, stroke: str, label_color: str,
                     half_width: float = .08, gap: float = .02) -> Component:
    """Adjacent cropped (white) and upsampled (blue) maps, not an add node."""
    _positive(h, half_width, gap)
    _finite(x,y)
    if type(channels_per_half) is not int or channels_per_half < 1:
        raise ValueError("Each concatenation half needs channels")
    copy=feature_map_strip(canvas,sid=f"copy{sid}",x=x,y=y,w=half_width,h=h,
        channels=2*channels_per_half,spatial_size=spatial_size,fill=fill,
        stroke=stroke,label_color=label_color,white=True,
        dimension_side="left",dimension_band="inside")
    up=feature_map_strip(canvas,sid=f"up{sid}",x=x+half_width+gap,y=y,w=half_width,h=h,
        channels=channels_per_half,spatial_size=spatial_size,fill=fill,
        stroke=stroke,label_color=label_color,show_channel=False,show_dimension=False)
    return Component(f"concat{sid}",{
        "crop_in":copy.port("left"), "upsample_in":up.port("bottom"),
        "conv_out":up.port("right"), "copy_center":copy.port("center"),
        "up_center":up.port("center")},(x,y,2*half_width+gap,h),
                     _union_boxes(copy.visual_bounds,up.visual_bounds))


def encoder_wedge(canvas: Canvas, *, sid: str, x: float, y: float, w: float,
                  h: float, label: str, fill: str, stroke: str,
                  taper: float, font_pt: float = 11) -> Component:
    """Paper-style tapered encoder, with distinct input and output ports."""
    _positive(w,h,taper,font_pt)
    _finite(x,y)
    label_lines=label.splitlines() if isinstance(label,str) else []
    max_line=max((len(line) for line in label_lines),default=0)
    required_text_h=len(label_lines)*font_pt/72*1.15
    if (taper >= h/2 or not any(line.strip() for line in label_lines) or
        w < .16+max_line*font_pt/72*.50 or
        h < .54 or required_text_h > .54):
        raise ValueError("Taper must fit the wedge and label must be present")
    canvas.polygon([(x,y),(x+w,y+taper),(x+w,y+h-taper),(x,y+h)],fill,stroke,1,sid)
    canvas.text(label,x+.08,y+h/2-.27,w-.16,.54,font_pt)
    return Component(sid,{"input":(x,y+h/2),"output":(x+w,y+h/2),
                          "top":(x+w/2,y+taper/2),"bottom":(x+w/2,y+h-taper/2)},
                     (x,y,w,h))


def addition_junction(canvas: Canvas, *, sid: str, x: float, y: float,
                      diameter: float, stroke: str, symbol_font_pt: float = 23) -> Component:
    """True additive merge with separate main and shortcut ports."""
    _positive(diameter,symbol_font_pt)
    _finite(x,y)
    if diameter < symbol_font_pt/(72*.70):
        raise ValueError("Addition symbol does not fit its junction")
    canvas.ellipse(x,y,diameter,diameter,"#FFFFFF",stroke,1.35,sid)
    # Same optical adjustment as the reviewed ResNet redraw, scaled by diameter.
    scale=diameter/.51
    canvas.text("+",round(x+.04*scale,5),round(y+.05*scale,5),
                round(.43*scale,5),round(.40*scale,5),symbol_font_pt,font="Arial")
    return Component(sid,{"main_in":(x+diameter/2,y),
                          "shortcut_in":(x+diameter,y+diameter/2),
                          "top_in":(x+diameter/2,y),
                          "shortcut_in_left":(x,y+diameter/2),
                          "shortcut_in_right":(x+diameter,y+diameter/2),
                          "out":(x+diameter/2,y+diameter)},
                     (x,y,diameter,diameter))


def residual_variant(canvas: Canvas, *, sid: str, x: float, y: float,
                     layers: Sequence[ResidualLayer], layer_stroke: str,
                     line_color: str, shortcut_fill: str,
                     panel_width: float = 3.25,
                     layer_height: float = .28,
                     layer_gap: float = .32,
                     input_label: str = "xₗ", output_label: str = "xₗ₊₁") -> Component:
    """One identity-shortcut variant with an arbitrary ordered layer sequence.

    The gray down arrow is a backdrop, while all model layers, paths and the
    addition node are separate editable objects. Use only when the cited source
    actually has an identity shortcut and additive merge.
    """
    _positive(panel_width,layer_height,layer_gap)
    _finite(x,y)
    if panel_width<2.90 or layer_height<.23:
        raise ValueError("Panel or layer is too small for editable labels and ports")
    max_layer_width=min(panel_width-.85,2*1.91,2*(panel_width-1.91))
    if len(layers)<2 or any(not layer.label or not math.isfinite(layer.width) or
                            layer.width<=.06 or layer.width>max_layer_width
                            for layer in layers):
        raise ValueError("Residual variant needs 2+ valid layer bars")
    base_x=x+.48;sum_y=y+2.95;diameter=.35;sum_x=base_x-diameter/2
    main_x=x+1.91
    first_y=y+1.20
    last_bottom=first_y+(len(layers)-1)*(layer_height+layer_gap)+layer_height
    if last_bottom>=sum_y-.25:
        raise ValueError("Layer sequence does not fit before the additive merge")
    def route(a: str,b: str,points: Sequence[Point],width: float = .9) -> None:
        # Figure sinks register semantic routes; a basic drawing sink still
        # receives the identical editable line geometry.
        fn=getattr(canvas,"route",None)
        if callable(fn):fn(a,b,list(points),line_color,width)
        else:
            for i,(p,q) in enumerate(zip(points[:-1],points[1:])):
                canvas.line(*p,*q,color=line_color,sw=width,arrow=i==len(points)-2)
    # Source figure's large gray identity arrow is a separate editable polygon.
    canvas.polygon([(base_x-.27,y+.12),(base_x+.27,y+.12),
                    (base_x+.27,y+3.36),(base_x+.48,y+3.36),
                    (base_x,y+3.66),(base_x-.48,y+3.36),
                    (base_x-.27,y+3.36)],shortcut_fill,shortcut_fill,.3)
    canvas.text(input_label,base_x-.28,y-.03,.56,.30,13,
                sid=f"{sid}_input",font="Times New Roman")
    route(f"{sid}_input",f"{sid}_add",[(base_x,y+.28),(base_x,sum_y)])
    route(f"{sid}_input",f"{sid}_layer_0",[(base_x,y+.45),(main_x,first_y)])
    layer_centers=[]
    for i,layer in enumerate(layers):
        ly=first_y+i*(layer_height+layer_gap)
        lx=main_x-layer.width/2
        canvas.rect(lx,ly,layer.width,layer_height,layer.fill,layer_stroke,.75,
                    f"{sid}_layer_{i}")
        canvas.text(layer.label,lx+.03,ly+.035,layer.width-.06,layer_height-.07,10,
                    sid=f"{sid}_layer_{i}_label")
        layer_centers.append((main_x,ly+layer_height))
        if i<len(layers)-1:
            next_y=first_y+(i+1)*(layer_height+layer_gap)
            route(f"{sid}_layer_{i}",f"{sid}_layer_{i+1}",
                  [(main_x,ly+layer_height),(main_x,next_y)],.85)
    junction=addition_junction(canvas,sid=f"{sid}_add",x=sum_x,y=sum_y,
                               diameter=diameter,stroke=line_color,symbol_font_pt=13)
    route(f"{sid}_layer_{len(layers)-1}",f"{sid}_add",
          [(main_x,last_bottom),junction.port("shortcut_in_right")])
    route(f"{sid}_add",f"{sid}_output",
          [junction.port("out"),(base_x,y+3.66)])
    canvas.text(output_label,base_x-.39,y+3.70,.78,.30,13,
                sid=f"{sid}_output",font="Times New Roman")
    return Component(sid,{"input":(base_x,y+.28),"main":(main_x,first_y),
                          "add":junction.port("top_in"),"output":(base_x,y+3.66)},
                     (x,y,panel_width,4.05),(x,y-.03,panel_width,4.08))


_SUB={"0":"₀","1":"₁","2":"₂","3":"₃","4":"₄","5":"₅",
      "6":"₆","7":"₇","8":"₈","9":"₉","n":"ₙ","N":"ₙ"}


def _subscript(index: str) -> str:
    if not index or any(ch not in _SUB for ch in index):
        raise ValueError(f"No reviewed subscript glyph for {index!r}")
    return "".join(_SUB[ch] for ch in index)


def similarity_matrix(canvas: Canvas, *, sid: str, x: float, y: float,
                      cell_w: float, cell_h: float, indices: Sequence[str],
                      row_header_x: float, column_header_y: float,
                      image_fill: str, image_stroke: str,
                      text_fill: str, text_stroke: str,
                      match_fill: str, grid_stroke: str,
                      text_vectors_id: str | None = None,
                      image_vectors_id: str | None = None,
                      cell_prefix: str | None = None,
                      grid_font_pt: float = 8.7) -> Component:
    """Paired image-row/text-column matrix with an explicit positive diagonal."""
    _positive(cell_w,cell_h,grid_font_pt)
    _finite(x,y,row_header_x,column_header_y)
    if cell_w < .35 or cell_h < .40:
        raise ValueError("Matrix cells too small for editable labels")
    if len(indices)<3 or indices.count("…")!=1 or indices[-1] not in {"n","N"}:
        raise ValueError("Use at least 3 displayed indices, one ellipsis and terminal n/N")
    if len(set(indices))!=len(indices):
        raise ValueError("Displayed vector indices must be unique")
    # Validate all glyphs before emitting the first editable element.
    for index in indices:
        if index!="…":_subscript(index)
    n=len(indices);width=n*cell_w;height=n*cell_h
    if row_header_x+cell_w>x or column_header_y+cell_h>y:
        raise ValueError("Row/column headers must sit outside the matrix")
    canvas.rect(x,column_header_y,width,cell_h,text_fill,text_stroke,.8,
                text_vectors_id or f"{sid}_text_vectors")
    for j,index in enumerate(indices):
        if j:canvas.line(x+j*cell_w,column_header_y,x+j*cell_w,column_header_y+cell_h,
                         color=text_stroke,sw=.55)
        label="···" if index=="…" else "T"+_subscript(index)
        canvas.text(label,x+j*cell_w,column_header_y+.13,cell_w,.26,11)
    canvas.rect(row_header_x,y,cell_w,height,image_fill,image_stroke,.8,
                image_vectors_id or f"{sid}_image_vectors")
    for i,index in enumerate(indices):
        if i:canvas.line(row_header_x,y+i*cell_h,row_header_x+cell_w,y+i*cell_h,
                         color=image_stroke,sw=.55)
        label="⋮" if index=="…" else "I"+_subscript(index)
        canvas.text(label,row_header_x,y+i*cell_h+.13,cell_w,.26,11)
    canvas.rect(x,y,width,height,"#ffffff",grid_stroke,.7,sid)
    cell_ports={}
    for i,ri in enumerate(indices):
        for j,cj in enumerate(indices):
            cx=x+j*cell_w;cy=y+i*cell_h
            canvas.rect(cx,cy,cell_w,cell_h,match_fill if i==j else "#ffffff",
                        grid_stroke,.55,f"{cell_prefix or sid+'_cell'}_{i}_{j}")
            label=("⋱" if ri=="…" and cj=="…" else "⋮" if ri=="…" else
                   "···" if cj=="…" else f"I{_subscript(ri)}·T{_subscript(cj)}")
            canvas.text(label,cx+.01,cy+.18,cell_w-.02,.20,grid_font_pt)
            cell_ports[f"cell_{i}_{j}"]=(cx+cell_w/2,cy+cell_h/2)
    ports={"row_group_in":(row_header_x,y+height/2),
           "column_group_in":(x+width/2,column_header_y),
           "matrix_left":(x,y+height/2),"matrix_top":(x+width/2,y)}
    ports.update({f"row_{i}":(row_header_x,y+(i+.5)*cell_h) for i in range(n)})
    ports.update({f"column_{j}":(x+(j+.5)*cell_w,column_header_y) for j in range(n)})
    ports.update(cell_ports)
    return Component(sid,ports,(row_header_x,column_header_y,
                                x+width-row_header_x,y+height-column_header_y))


def vector_fanout(canvas: Canvas, *, source: Point, targets: Sequence[Point],
                  trunk: float, orientation: str, color: str, sw: float = .75,
                  omitted_index: int | None = None) -> Component:
    """One continuous batch trunk with a branch to every displayed member.

    ``orientation='down'`` uses a horizontal trunk; ``'right'`` uses a vertical
    trunk. The optional ellipsis branch is dashed and has no arrow head.
    """
    _positive(sw)
    _finite(*source,trunk,*(coordinate for target in targets for coordinate in target))
    if len(targets)<2 or orientation not in {"down","right"}:
        raise ValueError("Fanout needs 2+ targets and down/right orientation")
    if omitted_index is not None and not 0<=omitted_index<len(targets):
        raise ValueError("Omitted member index outside target range")
    if orientation=="down":
        if any(y<=trunk for _,y in targets):raise ValueError("Downward targets must be below trunk")
        x0=min(source[0],*(x for x,_ in targets));x1=max(source[0],*(x for x,_ in targets))
        canvas.line(source[0],source[1],source[0],trunk,color=color,sw=sw)
        canvas.line(x0,trunk,x1,trunk,color=color,sw=sw)
        for i,(x,y) in enumerate(targets):
            canvas.line(x,trunk,x,y,color=color,sw=sw,arrow=i!=omitted_index,
                        dash=i==omitted_index)
        bounds=(x0,min(source[1],trunk),x1-x0,max(y for _,y in targets)-min(source[1],trunk))
    else:
        if any(x<=trunk for x,_ in targets):raise ValueError("Rightward targets must be right of trunk")
        y0=min(source[1],*(y for _,y in targets));y1=max(source[1],*(y for _,y in targets))
        canvas.line(source[0],source[1],trunk,source[1],color=color,sw=sw)
        canvas.line(trunk,y0,trunk,y1,color=color,sw=sw)
        for i,(x,y) in enumerate(targets):
            canvas.line(trunk,y,x,y,color=color,sw=sw,arrow=i!=omitted_index,
                        dash=i==omitted_index)
        bounds=(min(source[0],trunk),y0,max(x for x,_ in targets)-min(source[0],trunk),y1-y0)
    return Component("vector_fanout",{f"member_{i}":p for i,p in enumerate(targets)},bounds)


def token_strip(canvas: Canvas, *, sid: str, x: float, y: float,
                count: int, box: float, gap: float, fill: str,
                stroke: str, ellipsis_index: int | None = None,
                group_outline: bool = False) -> Component:
    """An ordered, editable token row with individually addressable slots."""
    _finite(x,y)
    _positive(box,gap)
    if type(count) is not int or count<3 or box<.15 or gap<.02:
        raise ValueError("Token strip needs 3+ legible slots and a positive gap")
    if ellipsis_index is not None and not 0<ellipsis_index<count-1:
        raise ValueError("An omitted token must be inside the visible row")
    width=count*box+(count-1)*gap
    ports={"left":(x,y+box/2),"right":(x+width,y+box/2)}
    if group_outline:
        canvas.rect(x-.06,y-.06,width+.12,box+.12,"#FFFFFF",stroke,.55,
                    f"{sid}_group")
        ports.update({"group_left":(x-.06,y+box/2),
                      "group_right":(x+width+.06,y+box/2),
                      "group_top":(x+width/2,y-.06),
                      "group_bottom":(x+width/2,y+box+.06)})
    for i in range(count):
        bx=x+i*(box+gap)
        if i==ellipsis_index:
            canvas.text("···",bx,y,box,box,11,sid=f"{sid}_ellipsis")
        else:
            canvas.rect(bx,y,box,box,fill,stroke,.65,f"{sid}_token_{i}")
        ports[f"top_{i}"]=(bx+box/2,y)
        ports[f"bottom_{i}"]=(bx+box/2,y+box)
    outer=(x-.06,y-.06,width+.12,box+.12) if group_outline else (x,y,width,box)
    return Component(sid,ports,outer)


def _draw_path(canvas: Canvas, points: Sequence[Point], *, color: str,
               sw: float, source_sid: str | None = None,
               target_sid: str | None = None,
               arrow_size: float | None = None,
               head_id: str | None = None) -> None:
    route=getattr(canvas,"route",None)
    if source_sid and target_sid and callable(route):
        route(source_sid,target_sid,list(points),color,sw,
              arrow_size=arrow_size,head_id=head_id)
    else:
        for j,(a,b) in enumerate(zip(points[:-1],points[1:])):
            canvas.line(*a,*b,color=color,sw=sw,arrow=j==len(points)-2,
                        arrow_size=arrow_size,head_id=head_id)


def multihead_neighbor_bundle(canvas: Canvas, *, sid: str,
                              source: Point, target: Point, source_radius: float,
                              target_radius: float, colors: Sequence[str],
                              wave_amplitude: float = .025,
                              source_sid: str | None = None,
                              target_sid: str | None = None) -> Component:
    """Parallel per-head neighborhood edges, with a semantic route for one strand.

    Source and target are node centers. The component stops paths at node
    perimeters; head identity is encoded by color *and* a slight wave.
    """
    _finite(*source,*target)
    _positive(source_radius,target_radius,wave_amplitude)
    if len(colors)<2 or len(set(colors))!=len(colors):
        raise ValueError("Distinct head colors are required")
    dx=target[0]-source[0];dy=target[1]-source[1]
    length=math.hypot(dx,dy)
    if length<=source_radius+target_radius+.16:
        raise ValueError("Neighbor nodes are too close for head paths")
    ux,uy=dx/length,dy/length
    px,py=-uy,ux
    start=(source[0]+ux*source_radius,source[1]+uy*source_radius)
    # Leave room for PowerPoint's native arrowhead, which projects past its
    # connector end and otherwise obscures a small target node.
    end=(target[0]-ux*(target_radius+.055),target[1]-uy*(target_radius+.055))
    count=len(colors)
    for k,color in enumerate(colors):
        lane=(k-(count-1)/2)*.065
        points=[]
        for j in range(17):
            t=j/16
            wobble=wave_amplitude*math.sin(t*math.pi*8+k*math.pi/2)*math.sin(math.pi*t)
            offset=lane*math.sin(math.pi*t)+wobble
            points.append((start[0]+(end[0]-start[0])*t+px*offset,
                           start[1]+(end[1]-start[1])*t+py*offset))
        _draw_path(canvas,points,color=color,sw=.75,
                   source_sid=source_sid if k==count//2 else None,
                   target_sid=target_sid if k==count//2 else None,
                   arrow_size=.045,head_id=f"{sid}:head:{k}")
    minx=min(source[0],target[0])-.12;miny=min(source[1],target[1])-.12
    maxx=max(source[0],target[0])+.12;maxy=max(source[1],target[1])+.12
    return Component(sid,{"source":start,"target":end},
                     (minx,miny,maxx-minx,maxy-miny))


def multihead_self_loop(canvas: Canvas, *, sid: str, center: Point,
                        node_radius: float, colors: Sequence[str],
                        node_sid: str | None = None) -> Component:
    """Visible self-attention paths anchored twice on the same node."""
    _finite(*center)
    _positive(node_radius)
    if len(colors)<2 or len(set(colors))!=len(colors):
        raise ValueError("Distinct head colors are required")
    cx,cy=center
    for k,color in enumerate(colors):
        reach=.30+k*.055
        start=(cx+node_radius*.28,cy-node_radius*.96)
        end=(cx+node_radius*.95,cy-node_radius*.30)
        points=[start,(cx+reach*.63,cy-node_radius-reach*.24),
                (cx+node_radius+reach*.44,cy-node_radius-reach*.25),
                (cx+node_radius+reach*.56,cy-reach*.22),end]
        _draw_path(canvas,points,color=color,sw=.8,
                   source_sid=node_sid if k==len(colors)//2 else None,
                   target_sid=node_sid if k==len(colors)//2 else None,
                   arrow_size=.045,head_id=f"{sid}:head:{k}")
    return Component(sid,{"start":start,"end":end},
                     (cx-node_radius,cy-node_radius-.39,
                      node_radius*2+.52,node_radius*2+.39))


def vector_math_label(canvas: Canvas, *, sid: str, text: str,
                      x: float, y: float, w: float, h: float,
                      arrow_fraction: float = .5, arrow_width: float = .13,
                      font_pt: float = 13, color: str = "#171717") -> Component:
    """Editable mathematical vector label with a small, consistent over-arrow.

    Pass a rendered subscript string, for example ``h₁`` or ``α₁₂``. The arrow
    fraction points at the symbol within the full text box, not the suffix.
    """
    _finite(x,y,arrow_fraction)
    _positive(w,h,arrow_width,font_pt)
    if not text.strip() or not 0<arrow_fraction<1 or arrow_width>=w*.75:
        raise ValueError("Vector label needs text and an arrow that fits")
    ax=x+w*arrow_fraction;ay=y+.035
    left=ax-arrow_width/2;right=ax+arrow_width/2
    canvas.text(text,x,y,w,h,font_pt,color=color,sid=sid)
    canvas.line(left,ay,right,ay,color=color,sw=.45)
    canvas.line(right,ay,right-.026,ay-.012,color=color,sw=.45)
    canvas.line(right,ay,right-.026,ay+.012,color=color,sw=.45)
    return Component(sid,{"center":(x+w/2,y+h/2)},(x,y,w,h),
                     (x,min(y,ay-.012),w,y+h-min(y,ay-.012)))
