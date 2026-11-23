"""Bounded scientific glyphs compiled to editable FigureSpec primitives.

Coordinates are inches. Layout is local to the supplied box; this module neither
infers scientific facts nor lays out a complete graph. Unknown values remain
symbolic, and a box too small for readable marks fails explicitly.
"""
from __future__ import annotations

import math
import unicodedata

from ml_figure_components import addition_junction, feature_map_strip, token_strip

INK = "#26343F"
COLORS = ("#2878A5", "#A45B36", "#568349", "#7C609A", "#A07C21")
FILLS = ("#D7EAF4", "#F2E0D5", "#E1EDD9", "#E7E0F1", "#F2EACB")
KINDS = {"tensor", "time_series", "conv1d", "embedding", "add", "graph_attention",
         "pool", "concat", "projection", "head", "gate", "process"}


def _wrapped(text, width, size):
    """Conservative CJK-aware wrapping; preserve characters and explicit lines."""
    limit = (width-.045)*72/size
    if limit < 1:
        raise ValueError("box is too narrow for readable text")
    lines = []
    for source in str(text).split("\n"):
        line, used = "", 0.0
        for char in source:
            units = 1.0 if unicodedata.east_asian_width(char) in "WF" else .60
            if used + units > limit and line:
                lines.append(line)
                line, used = "", 0.0
            line += char
            used += units
        lines.append(line)
    return "\n".join(lines)


class _Canvas:
    """Adapter for existing ML components, with ownership on every real mark."""
    def __init__(self, node):
        self.node, self.elements = node, []
        self.font = node.get("font", "Noto Sans CJK SC")
        self.size = node.get("font_size", 11)
        self.role, self.head = "mechanism", None

    def emit(self, kind, **values):
        item = {"type": kind, "semantic_owner": self.node["id"],
                "visual_role": self.role, "evidence_refs": list(self.node.get("evidence", []))}
        if self.head is not None:
            item["head_index"] = self.head
        item.update(values)
        self.elements.append(item)
        return item

    def rect(self, x, y, w, h, fill="#FFFFFF", stroke=INK, sw=.8, sid=None, dash=False):
        return self.emit("rect", x=x, y=y, w=w, h=h, fill=fill, stroke=stroke, sw=sw, dash=dash)

    def ellipse(self, x, y, w, h, fill="#FFFFFF", stroke=INK, sw=.8, sid=None):
        return self.emit("ellipse", x=x, y=y, w=w, h=h, fill=fill, stroke=stroke, sw=sw)

    def polygon(self, points, fill="#FFFFFF", stroke=INK, sw=.8, sid=None):
        return self.emit("polygon", points=[list(p) for p in points], fill=fill, stroke=stroke, sw=sw)

    def text(self, s, x, y, w, h, size=10, align="center", color=INK,
             bold=False, rotation=0, sid=None, font=None):
        # token_strip's three middle dots are one omission glyph, not three
        # scientific values. Use the single glyph to fit narrow editable slots.
        if sid and sid.endswith("_ellipsis") and s == "···":
            s = "⋯"
        text = _wrapped(s, w, size)
        if len(text.split("\n"))*size/72*1.18+.015 > h+1e-8:
            raise ValueError(f"box is too small for readable label {s!r}")
        return self.emit("text", text=text, x=x, y=y, w=w, h=h, size=size, align=align,
                         color=color, bold=bold, rotation=rotation, font=self.font)

    def line(self, x1, y1, x2, y2, color=INK, sw=.9, arrow=False, dash=False,
             link=None, arrow_size=None, head_id=None):
        return self.emit("line", x1=x1, y1=y1, x2=x2, y2=y2, color=color, sw=sw,
                         arrow=arrow, dash=dash, arrow_size=arrow_size or .045)


def _ports(x, y, w, h):
    return {"left": [x, y+h/2], "right": [x+w, y+h/2],
            "top": [x+w/2, y], "bottom": [x+w/2, y+h]}


def _count(params, key):
    value = params.get(key)
    if type(value) is not int or value < 1:
        raise ValueError(f"{key} must be a positive integer; no count is inferred")
    return value


def _dimensions(params):
    shape = params.get("shape")
    if shape is None:
        return "维数未提供"
    if not isinstance(shape, list) or not shape or any(
            not ((type(v) is int and v > 0) or (isinstance(v, str) and v.strip())) for v in shape):
        raise ValueError("shape must contain positive integers or symbolic dimensions")
    return " × ".join(str(v) for v in shape)


def _caption(kind, p):
    if kind in {"tensor", "embedding", "projection"}:
        return ("张量示意 · " if kind == "tensor" else "") + _dimensions(p), "dimension"
    if kind in {"conv1d", "time_series"}:
        return (("扫描示意" if kind == "conv1d" else "x(t) · 时间序列示意") +
                ("\n" + _dimensions(p) if "shape" in p else "")), "disclosure"
    if kind == "graph_attention":
        _count(p, "heads")
        merge = p.get("merge", "unknown")
        if merge not in {"mean", "concat", "unknown"}:
            raise ValueError("merge must be mean, concat or unknown")
        return (("融合未提供" if merge == "unknown" else merge) + "\n" +
                ("j∈N(i) · 邻域示意" if p.get("adjacency", "unknown") == "unknown"
                 else "给定邻接")), "disclosure"
    if kind == "pool":
        if p.get("reduction") != "mean":
            raise ValueError("pool reduction must be explicitly mean")
        return f"组内 mean 示意 · G={_count(p, 'groups')}\n{_dimensions(p)}", "parameters"
    if kind == "concat":
        return f"concat · inputs={_count(p, 'inputs')}", "parameters"
    if kind == "head":
        return (f"{_count(p, 'outputs')} outputs" + (f" · {p['activation']}" if p.get("activation") else "") +
                ("\n输出示意（中间项省略）" if p["outputs"] > 3 else "")), "parameters"
    if kind == "gate":
        return f"τ = {p['threshold']}" if "threshold" in p else "τ 未提供", "parameters"
    return ("内部未提供" if kind == "process" and p.get("opaque") else ""), "disclosure"


def _tensor(c, b, p):
    x, y, w, h = b
    rank = len(p.get("shape", []))
    step = min(.13, w*.07, h*.12) if rank >= 3 else 0
    fh = min(h, .25) if rank == 1 else h-2*step
    front = (x+w*.12, y+2*step+(h-2*step-fh)/2, w*.66, fh)
    c.role = "tensor_plane"
    for layer in ((2, 1, 0) if rank >= 3 else (0,)):
        fx, fy, fw, fh = front
        feature_map_strip(c, sid=f"plane_{layer}", x=fx+layer*step, y=fy-layer*step,
                          w=fw, h=fh, channels=1, spatial_size="?", fill=FILLS[layer],
                          stroke=INK, label_color=INK, show_channel=False, show_dimension=False)
    if rank == 2:
        c.role = "tensor_grid"
        for fraction in (1/3, 2/3):
            c.line(fx+fw*fraction, fy, fx+fw*fraction, fy+fh, sw=.5)
            c.line(fx, fy+fh*fraction, fx+fw, fy+fh*fraction, sw=.5)
    c.role = "omission"
    c.text("⋯", front[0]+front[2]*.35, front[1]+front[3]*.38, front[2]*.3, .22, 11)
    return _ports(*front)


def _sequence(c, b, p, convolution=False):
    x, y, w, h = b
    if not convolution:
        cy = y+h*.55
        c.role = "time_axis"
        c.line(x, cy, x+w, cy, arrow=True)
        for fraction in (.18, .5, .82):
            tx = x+w*fraction
            c.line(tx, cy-.09, tx, cy+.09)
        c.text("…  t  …", x+w*.2, y, w*.6, .22, 10)
        return {"left": [x, cy], "right": [x+w, cy],
                "top": [x+w*.5, cy-.09], "bottom": [x+w*.5, cy+.09]}
    size, gap = min(.27, (w-.24)/5, h*.32), .04
    if size < .15 or h < .55:
        raise ValueError("conv1d box is too small for its scanning window")
    tw = size*5+gap*4
    tx, ty = x+(w-tw)/2, y+h*.47
    window = (tx+size+gap-.035, ty-.04, size*2+gap+.07, size+.08)
    c.role = "conv_window"
    c.rect(*window, fill=FILLS[1], dash=True)
    c.line(window[0], ty-.14, window[0]+window[2], ty-.14, arrow=True)
    c.role = "sequence_token"
    token_strip(c, sid="sequence", x=tx, y=ty, count=5, box=size, gap=gap,
                fill="#FFFFFF", stroke=INK, ellipsis_index=2)
    return {"left": [tx, ty+size/2], "right": [tx+tw, ty+size/2],
            "top": [window[0]+window[2]/2, window[1]],
            "bottom": [window[0]+window[2]/2, window[1]+window[3]]}


def _embedding(c, b, p):
    x, y, w, h = b
    size, gap = min(.23, w*.13, h*.42), .04
    if size < .15:
        raise ValueError("embedding box is too small for visible tokens")
    ty = y+h/2-size/2
    c.role = "embedding_token"
    strip = token_strip(c, sid="tokens", x=x, y=ty, count=3, box=size, gap=gap,
                        fill=FILLS[0], stroke=INK, ellipsis_index=1)
    vx, vw = x+w*.72, w*.28
    c.role = "embedding_vector"
    c.rect(vx, y, vw, h, FILLS[3])
    for fraction in (.25, .75):
        c.line(vx, y+h*fraction, vx+vw, y+h*fraction, sw=.65)
    c.text("⋯", vx, y+h/2-.11, vw, .22, 11)
    c.role = "embedding_mapping"
    c.line(*strip.port("right"), vx-.025, y+h/2, arrow=True)
    ports = _ports(vx, y, vw, h)
    ports["left"] = list(strip.port("left"))
    return ports


def _add(c, b, p):
    x, y, w, h = b
    d = min(w, h, .66)
    c.role = "addition"
    addition_junction(c, sid="add", x=x+(w-d)/2, y=y+(h-d)/2, diameter=d,
                      stroke=INK, symbol_font_pt=min(23, d*72*.60))
    return _ports(x+(w-d)/2, y+(h-d)/2, d, d)


def _attention(c, b, p):
    x, y, w, h = b
    count = _count(p, "heads")
    cell = w/count
    adjacency = p.get("adjacency", "unknown")
    if adjacency not in {"known", "unknown"}:
        raise ValueError("adjacency must be known or unknown")
    if cell < .64 or h < .75:
        raise ValueError("box is too small for readable independent heads; enlarge box")
    nodes, edges = p.get("graph_nodes", []), p.get("graph_edges", [])
    if adjacency == "known":
        if not isinstance(nodes, list) or not nodes or len(nodes) > 6 or cell < 1.15 or h < 1.0:
            raise ValueError("known adjacency needs 1–6 nodes and a larger box per head")
        if not isinstance(edges, list) or any(not isinstance(e, (list, tuple)) or len(e) != 2 or
                any(type(i) is not int or not 0 <= i < len(nodes) for i in e) for e in edges):
            raise ValueError("graph edge indices must refer to supplied adjacency nodes")
    merge_y, bus_y, anchors, entries = y+h-.035, y+.245, [], []
    for k in range(count):
        c.head = k
        cx, color = x+cell*(k+.5), COLORS[k % len(COLORS)]
        c.role = "attention_head_label"
        c.text(f"H{k+1}", cx-cell/2, y, cell, .19, 9.5, color=color, bold=True)
        r = .095
        if adjacency == "unknown":
            points = [(cx-cell*.24, y+h*.55), (cx+cell*.24, y+h*.55)]
            labels, links = ["j", "i"], [(0, 1)]
        else:
            labels, links = [str(v) for v in nodes], edges
            widths = [sum(1 if unicodedata.east_asian_width(ch) in "WF" else .6 for ch in label)
                      *9/72+.07 for label in labels]
            r = max(r, max(widths)/2)
            rx, ry = cell/2-r-.10, (h-.70-2*r)/2
            if rx < .12 or ry < .02:
                raise ValueError("known adjacency labels need a larger box")
            points = [(cx+math.cos(math.pi+2*math.pi*i/len(nodes))*rx,
                       y+h/2+.11+math.sin(math.pi+2*math.pi*i/len(nodes))*ry)
                      for i in range(len(nodes))]
        c.role = "head_input"
        if adjacency == "unknown":
            entry_x, entry_y = points[0][0], points[0][1]-r
        else:
            entry_x, entry_y = cx, y+.35
            c.line(cx-cell*.36, entry_y, cx+cell*.36, entry_y)
        c.line(entry_x, bus_y, entry_x, entry_y, arrow=True)
        entries.append(entry_x)
        c.role = "attention_neighbor"
        for source, target in links:
            ax, ay = points[source]
            bx, by = points[target]
            if source == target:
                side = 1 if ax < cx else -1
                loop = [(ax, ay-r), (ax, ay-r-.10), (ax+side*(r+.08), ay-r-.10), (ax+side*r, ay)]
                for first, last in zip(loop, loop[1:]):
                    c.line(*first, *last, color=color, arrow=last == loop[-1])["graph_edge"] = [source, target]
            else:
                length = math.hypot(bx-ax, by-ay)
                if length < 2*r+.035:
                    raise ValueError("known adjacency nodes overlap; enlarge box")
                ux, uy = (bx-ax)/length, (by-ay)/length
                mark = c.line(ax+ux*r, ay+uy*r, bx-ux*r, by-uy*r, color=color, arrow=True)
                if adjacency == "known":
                    mark["graph_edge"] = [source, target]
        for index, ((cxn, cyn), label) in enumerate(zip(points, labels)):
            c.role = "attention_head" if adjacency == "known" or index == 1 else "attention_neighbor"
            c.ellipse(cxn-r, cyn-r, 2*r, 2*r, FILLS[k % len(FILLS)], color)
            c.text(label, cxn-r, cyn-r, 2*r, 2*r, 9)
        anchor = points[-1]
        c.role = "head_merge"
        if adjacency == "known":
            # A whole graph yields a set of node features, not an arbitrary
            # selected node. A bracket carries that set to the head merge.
            anchor = (cx, y+h-.16-r)
            c.line(cx-cell*.36, anchor[1]+r, cx+cell*.36, anchor[1]+r, color=color)
        c.line(anchor[0], anchor[1]+r, anchor[0], merge_y, color=color)
        anchors.append(anchor[0])
    c.head, c.role = None, "head_merge"
    c.line(min(anchors), merge_y, x+w, merge_y, arrow=True)
    c.role = "shared_input"
    c.line(x, bus_y, max(entries), bus_y)
    return {"left": [x, bus_y], "right": [x+w, merge_y], "top": [(x+max(entries))/2, bus_y],
            "bottom": [anchors[-1], merge_y]}


def _pool(c, b, p):
    x, y, w, h = b
    groups = _count(p, "groups")
    visible = list(range(groups)) if groups <= 3 else [0, None, groups-1]
    if h/len(visible) < .25 or w < 1.5:
        raise ValueError("pool box is too small for its groups")
    d, mx = .19, x+w*.62
    rows = []
    for slot, group in enumerate(visible):
        cy = y+(slot+.5)*h/len(visible)
        if group is None:
            c.role = "omission"
            c.text("⋯", x+w*.3, cy-.11, w*.4, .22, 11)
            continue
        start = len(c.elements)
        c.role = "pool_input"
        c.line(x, cy, x+.16, cy, arrow=True)
        c.role = "pool_feature"
        c.rect(x+.16, cy-.10, w*.30, .20, FILLS[slot % len(FILLS)])
        c.text(f"g{group+1} · ⋯", x+.16, cy-.10, w*.30, .20, 9)
        c.role = "pool_reduction"
        c.line(x+.16+w*.30, cy, mx-d/2, cy, arrow=True)
        c.ellipse(mx-d/2, cy-d/2, d, d, FILLS[2])
        c.text("μ", mx-d/2, cy-d/2, d, d, 9)
        c.line(mx+d/2, cy, x+w-.30, cy, arrow=True)
        c.role = "pool_output"
        c.rect(x+w-.30, cy-.10, .13, .20, FILLS[2])
        c.line(x+w-.17, cy, x+w, cy)
        for mark in c.elements[start:]:
            mark.update(group_index=group, compressed=groups > 3, schematic=True)
        rows.append(cy)
    c.role = "group_bundle"
    c.line(x, rows[0], x, rows[-1])
    c.line(x+w, rows[0], x+w, rows[-1])
    return {"left": [x, y+h/2], "right": [x+w, y+h/2],
            "top": [mx, rows[0]-d/2], "bottom": [mx, rows[-1]+d/2]}


def _concat(c, b, p):
    x, y, w, h = b
    count = _count(p, "inputs")
    if w/count < .18:
        raise ValueError("concat box is too small for its inputs")
    height, cy = min(.48, h*.65), y+h/2
    c.role = "concat_segment"
    for i in range(count):
        c.rect(x+i*w/count, cy-height/2, w/count, height, FILLS[i % len(FILLS)])
    c.role = "concat_join"
    c.line(x, cy-height/2-.06, x+w, cy-height/2-.06)
    return _ports(x, cy-height/2, w, height)


def _projection(c, b, p):
    x, y, w, h = b
    c.role = "projection_wedge"
    c.polygon([(x, y), (x+w, y+h*.3), (x+w, y+h*.7), (x, y+h)], FILLS[3])
    return {"left": [x, y+h/2], "right": [x+w, y+h/2],
            "top": [x+w/2, y+h*.15], "bottom": [x+w/2, y+h*.85]}


def _head(c, b, p):
    x, y, w, h = b
    count = _count(p, "outputs")
    visible = list(range(count)) if count <= 3 else [0, None, count-1]
    d = min(.17, h/len(visible)*.65)
    if d < .10 or w < .7:
        raise ValueError("head box is too small for its outputs")
    c.role = "head_operator"
    c.polygon([(x, y+h*.2), (x+w*.4, y+h*.4),
               (x+w*.4, y+h*.6), (x, y+h*.8)], FILLS[1])
    centers = []
    for slot, index in enumerate(visible):
        cy = y+(slot+.5)*h/len(visible)
        if index is None:
            c.role = "omission"
            c.text("⋯", x+w-.40, cy-.11, .35, .22, 11)
            continue
        c.role = "head_fanout"
        c.line(x+w*.4, y+h/2, x+w-d-.10, cy, arrow=True)
        c.role = "output_marker"
        c.ellipse(x+w-d-.10, cy-d/2, d, d, FILLS[1]).update(
            output_index=index, compressed=count > 3, schematic=True)
        c.role = "head_output"
        c.line(x+w-.10, cy, x+w, cy)
        centers.append(cy)
    c.role = "output_bundle"
    c.line(x+w, centers[0], x+w, centers[-1])
    return {"left": [x, y+h/2], "right": [x+w, y+h/2],
            "top": [x+w-d/2-.10, centers[0]-d/2], "bottom": [x+w-d/2-.10, centers[-1]+d/2]}


def _gate(c, b, p):
    x, y, w, h = b
    cx, cy = x+w/2, y+h/2
    c.role = "gate_signal"
    c.line(x, cy, cx-.06, cy)
    c.line(cx+.06, cy, x+w, cy, arrow=True)
    c.role = "gate_boundary"
    c.line(cx, y+.06, cx, y+h-.06, dash=True, sw=1.2)
    return {"left": [x, cy], "right": [x+w, cy],
            "top": [cx, y+.06], "bottom": [cx, y+h-.06]}


def draw_node(node: dict) -> dict:
    """Draw one scientific object; ports touch marks, never the label box."""
    kind, box = node.get("kind"), node.get("box")
    if kind not in KINDS:
        raise ValueError(f"Unsupported scientific kind {kind!r}; choose an evidenced kind")
    if not isinstance(box, (list, tuple)) or len(box) != 4 or any(
            isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in box):
        raise ValueError("box must contain four finite coordinates")
    x, y, w, h = box
    c, p = _Canvas(node), node.get("params", {})
    if not isinstance(c.size, (int, float)) or not math.isfinite(c.size) or c.size < 9:
        raise ValueError("font_size must be at least 9 pt; enlarge box instead of shrinking text")
    if w < .6 or h < .6:
        raise ValueError("box is too small for a readable scientific glyph")
    if kind == 'process':
        # A named opaque module remains a legitimate box. Put its meaning in
        # that box, not above an empty panel. Evidence limitations live in the
        # plan and the figure's disclosure, rather than repeated banners.
        c.role = 'process_body'
        c.rect(x+.04, y+.04, w-.08, h-.08, fill='#FFFFFF')
        footer = .28 if 'shape' in p else 0
        c.role = 'node_label'
        c.text(node['label'], x+.12, y+.10, w-.24, h-.20-footer, c.size,
               bold='\n' not in node['label'])
        if footer:
            c.role = 'dimension'
            c.text(_dimensions(p), x+.12, y+h-.35, w-.24, .24, max(9, c.size-1))
        ports = _ports(x+.04, y+.04, w-.08, h-.08)
        ports.update(input=ports['left'], output=ports['right'])
        return {'elements': c.elements, 'ports': ports, 'box': list(box)}
    label = _wrapped(node.get("label", kind), w-.16, c.size)
    caption, caption_role = _caption(kind, p)
    if "shape" in p and kind not in {"tensor", "embedding", "projection", "conv1d", "time_series", "pool"}:
        lines = caption.split("\n")
        lines[0] = (lines[0] + " · " if lines[0] else "") + _dimensions(p)
        caption = "\n".join(lines)
    small = max(9, min(c.size-1, 10))
    caption = _wrapped(caption, w-.16, small) if caption else ""
    label_h = len(label.split("\n"))*c.size/72*1.24+.025
    footer_h = len(caption.split("\n"))*small/72*1.24+.025 if caption else 0
    body = (x+.08, y+label_h+.09, w-.16, h-label_h-footer_h-.23)
    if body[3] < .36:
        raise ValueError("box is too small for label and scientific marks; enlarge box")
    c.role = "node_label"
    c.text(label, x+.08, y+.025, w-.16, label_h, c.size, bold=True)
    if caption:
        c.role = caption_role
        c.text(caption, x+.08, y+h-footer_h-.025, w-.16, footer_h, small)
    drawers = {"tensor": _tensor, "time_series": _sequence, "embedding": _embedding,
               "add": _add, "graph_attention": _attention, "pool": _pool,
               "concat": _concat, "projection": _projection, "head": _head, "gate": _gate}
    if kind == "conv1d":
        ports = _sequence(c, body, p, convolution=True)
    else:
        ports = drawers[kind](c, body, p)
    ports.update(input=ports["left"], output=ports["right"])
    return {"elements": c.elements, "ports": ports, "box": list(box)}
