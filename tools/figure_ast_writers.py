#!/usr/bin/env python3
"""Independent SVG and DrawingML writers consuming the same immutable FigureAST."""
from __future__ import annotations

import base64
import math
from pathlib import Path
from xml.sax.saxutils import escape

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches, Pt

from figure_ast import FigureAST

DPI = 120.0


def _color(value: str) -> str:
    return str(value).lstrip("#").upper()


def _rgb(value: str) -> RGBColor:
    return RGBColor.from_string(_color(value))


def _resolve_image(path: str, root: Path | None) -> Path:
    result = Path(path)
    if not result.is_absolute():
        result = (root or Path(__file__).resolve().parents[1]) / result
    if not result.is_file():
        raise FileNotFoundError(f"FIGURE_IMAGE_NOT_FOUND:{result}")
    return result


def _tag(shape, element: dict, part: str, enabled: bool) -> None:
    if not enabled:
        return
    role = element.get("semantic_id") or element.get("semantic_role") or "element"
    element_id = element.get("id") or "generated"
    shape.name = f"{role}__{element_id}__{part}"


def _no_effects(shape) -> None:
    for node in shape._element.iter():
        style = node.find(qn("p:style"))
        if style is not None:
            ref = style.find(qn("a:effectRef"))
            if ref is not None:
                ref.set("idx", "0")
        effects = node.find(qn("a:effectLst"))
        if effects is not None:
            node.remove(effects)
    sp = getattr(shape._element, "spPr", None)
    if sp is not None and sp.find(qn("a:effectLst")) is None:
        sp.append(OxmlElement("a:effectLst"))


class SvgWriter:
    """Serialize AST primitives to SVG. Geometry is read only from FigureAST."""
    def __init__(self, dpi: float = DPI, root: Path | None = None):
        self.dpi = float(dpi)
        self.root = root

    def write(self, ast: FigureAST, output: str | Path) -> dict:
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        spec = ast.to_spec()
        width = float(ast.canvas.get("width_in")) * self.dpi
        height = float(ast.canvas.get("height_in")) * self.dpi
        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}">',
            '<defs><marker id="ast-arrow" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0 0 L9 4.5 L0 9 Z" fill="#43525B"/></marker></defs>',
            f'<rect width="{width:.0f}" height="{height:.0f}" fill="#FFFFFF"/>',
        ]
        for node in ast.nodes:
            e = node.to_element()
            kind = node.kind
            if kind == "image":
                image = _resolve_image(e["path"], self.root)
                data = base64.b64encode(image.read_bytes()).decode("ascii")
                mime = "image/png" if image.suffix.lower() == ".png" else "image/jpeg"
                parts.append(
                    f'<image x="{e["x"]*self.dpi}" y="{e["y"]*self.dpi}" width="{e["w"]*self.dpi}" height="{e["h"]*self.dpi}" href="data:{mime};base64,{data}"/>'
                )
            elif kind == "text":
                x, y, w, h = [float(e[k]) * self.dpi for k in ("x", "y", "w", "h")]
                size = float(e.get("size", 14)) * self.dpi / 72.0
                lines = str(e["text"]).split("\n")
                align = e.get("align", "center")
                anchor = {"left": "start", "center": "middle", "right": "end"}[align]
                tx = x if align == "left" else x + w / 2 if align == "center" else x + w
                line_height = size * 1.18
                baseline = y + h / 2 - (len(lines) - 1) * line_height / 2 + size * .35
                tspans = "".join(
                    f'<tspan x="{tx:.3f}" dy="{0 if i == 0 else line_height:.3f}">{escape(line)}</tspan>'
                    for i, line in enumerate(lines)
                )
                font = e.get("font", spec.get("style", {}).get("font", "Times New Roman"))
                if font == "Microsoft YaHei":
                    font = "Noto Sans CJK SC, DejaVu Sans, Microsoft YaHei, sans-serif"
                rotate = (
                    f' transform="rotate({e["rotation"]} {x+w/2:.3f} {y+h/2:.3f})"'
                    if e.get("rotation") else ""
                )
                parts.append(
                    f'<text x="{tx:.3f}" y="{baseline:.3f}" text-anchor="{anchor}" dominant-baseline="middle" font-family="{escape(str(font))}" font-size="{size:.3f}" fill="{e.get("color", "#28343C")}"'
                    + (' font-weight="700"' if e.get("bold") else "")
                    + (' font-style="italic"' if e.get("italic") else "")
                    + rotate + f'>{tspans}</text>'
                )
            elif kind in {"rect", "trapezoid"}:
                x, y, w, h = [float(e[k]) * self.dpi for k in ("x", "y", "w", "h")]
                fill, stroke = e.get("fill", "#FFFFFF"), e.get("stroke", "#43525B")
                sw = float(e.get("sw", 1)) * self.dpi / 72
                if kind == "rect":
                    dash = ' stroke-dasharray="8 6"' if e.get("dash") else ""
                    parts.append(
                        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{float(e.get("radius", 0))*self.dpi}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>'
                    )
                else:
                    points = f'{x+w*.13},{y} {x+w*.87},{y} {x+w},{y+h} {x},{y+h}'
                    parts.append(f'<polygon points="{points}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
            elif kind == "line":
                x1, y1, x2, y2 = [float(e[k]) * self.dpi for k in ("x1", "y1", "x2", "y2")]
                dash = ' stroke-dasharray="8 6"' if e.get("dash") else ""
                arrow = ' marker-end="url(#ast-arrow)"' if e.get("arrow") and not e.get("arrow_size") else ""
                parts.append(
                    f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{e.get("color", "#43525B")}" stroke-width="{float(e.get("sw", 1))*self.dpi/72}"{dash}{arrow}/>'
                )
                if e.get("arrow") and e.get("arrow_size"):
                    length = math.hypot(x2-x1, y2-y1)
                    if length:
                        size = float(e["arrow_size"]) * self.dpi
                        ux, uy = (x2-x1)/length, (y2-y1)/length
                        px, py = -uy, ux
                        points = (
                            f'{x2},{y2} {x2-ux*size+px*size/2},{y2-uy*size+py*size/2} '
                            f'{x2-ux*size-px*size/2},{y2-uy*size-py*size/2}'
                        )
                        parts.append(f'<polygon points="{points}" fill="{e.get("color", "#43525B")}"/>')
            elif kind == "polyline":
                points = " ".join(f"{x*self.dpi},{y*self.dpi}" for x, y in e["points"])
                parts.append(
                    f'<polyline points="{points}" fill="none" stroke="{e.get("color", "#43525B")}" stroke-width="{float(e.get("sw", 1.2))*self.dpi/72}" stroke-linecap="round" stroke-linejoin="round"/>'
                )
            elif kind == "polygon":
                points = " ".join(f"{x*self.dpi},{y*self.dpi}" for x, y in e["points"])
                parts.append(
                    f'<polygon points="{points}" fill="{e.get("fill", "#FFFFFF")}" stroke="{e.get("stroke", "#43525B")}" stroke-width="{float(e.get("sw", 1))*self.dpi/72}"/>'
                )
            elif kind == "ellipse":
                x, y, w, h = [float(e[k]) * self.dpi for k in ("x", "y", "w", "h")]
                parts.append(
                    f'<ellipse cx="{x+w/2}" cy="{y+h/2}" rx="{w/2}" ry="{h/2}" fill="{e.get("fill", "#FFFFFF")}" stroke="{e.get("stroke", "#43525B")}" stroke-width="{float(e.get("sw", 1))*self.dpi/72}"/>'
                )
            elif kind in {"grid", "stack_grid"}:
                x, y, w, h = [float(e[k]) * self.dpi for k in ("x", "y", "w", "h")]
                rows, cols = int(e["rows"]), int(e["cols"])
                border = e.get("border", "#98A6AF")
                stroke = e.get("stroke", "#D7DEE3")
                if kind == "stack_grid":
                    offset = float(e.get("offset", .16)) * self.dpi
                    for layer in range(int(e.get("layers", 5))-1, 0, -1):
                        parts.append(
                            f'<rect x="{x+offset*layer}" y="{y-offset*layer}" width="{w}" height="{h}" fill="#FFFFFF" stroke="{border}" stroke-width="1"/>'
                        )
                parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{e.get("fill", "#FBFCFD")}" stroke="{border}" stroke-width="1"/>')
                for col in range(1, cols):
                    xx = x + w * col / cols
                    parts.append(f'<line x1="{xx}" y1="{y}" x2="{xx}" y2="{y+h}" stroke="{stroke}" stroke-width="{float(e.get("sw", .4))*self.dpi/72}"/>')
                for row in range(1, rows):
                    yy = y + h * row / rows
                    parts.append(f'<line x1="{x}" y1="{yy}" x2="{x+w}" y2="{yy}" stroke="{stroke}" stroke-width="{float(e.get("sw", .4))*self.dpi/72}"/>')
            elif kind == "sensor":
                x, y, scale = float(e["x"]), float(e["y"]), float(e.get("scale", 1))
                variant, color = int(e.get("variant", 0)), e.get("color", "#43525B")
                X, Y, S = x*self.dpi, y*self.dpi, scale*self.dpi
                if variant == 0:
                    parts.append(f'<circle cx="{X+S*.10}" cy="{Y+S*.10}" r="{S*.075}" fill="#E8F0F3" stroke="{color}" stroke-width="2"/>')
                    parts.append(f'<circle cx="{X+S*.10}" cy="{Y+S*.10}" r="{S*.025}" fill="{color}"/>')
                elif variant == 1:
                    parts.append(f'<rect x="{X+S*.02}" y="{Y+S*.06}" width="{S*.17}" height="{S*.14}" rx="2" fill="#E8F0F3" stroke="{color}" stroke-width="2"/>')
                elif variant == 2:
                    points = f'{X+S*.02},{Y+S*.12} {X+S*.12},{Y+S*.04} {X+S*.20},{Y+S*.15} {X+S*.10},{Y+S*.23}'
                    parts.append(f'<polygon points="{points}" fill="#E8F0F3" stroke="{color}" stroke-width="2"/>')
                else:
                    parts.append(f'<rect x="{X+S*.06}" y="{Y+S*.025}" width="{S*.09}" height="{S*.24}" rx="3" fill="#E8F0F3" stroke="{color}" stroke-width="2"/>')
                parts.append(f'<line x1="{X+S*.10}" y1="{Y+S*.20}" x2="{X+S*.10}" y2="{Y+S*.30}" stroke="{color}" stroke-width="2"/>')
                parts.append(f'<rect x="{X+S*.015}" y="{Y+S*.30}" width="{S*.18}" height="{S*.045}" fill="#FFFFFF" stroke="{color}" stroke-width="1.5"/>')
            elif kind == "graph":
                x, y, w, h = [float(e[k]) for k in ("x", "y", "w", "h")]
                nodes = e["nodes"]
                for a, b in e["edges"]:
                    x1, y1 = x+nodes[a][0]*w, y+nodes[a][1]*h
                    x2, y2 = x+nodes[b][0]*w, y+nodes[b][1]*h
                    parts.append(f'<line x1="{x1*self.dpi}" y1="{y1*self.dpi}" x2="{x2*self.dpi}" y2="{y2*self.dpi}" stroke="{e.get("edge", "#43525B")}" stroke-width="{float(e.get("sw", .7))*self.dpi/72}"/>')
                radius = float(e.get("r", .034))*self.dpi
                for nx, ny in nodes:
                    parts.append(f'<circle cx="{(x+nx*w)*self.dpi}" cy="{(y+ny*h)*self.dpi}" r="{radius}" fill="{e.get("fill", "#7896A6")}"/>')
            else:
                raise ValueError(f"UNSUPPORTED_SVG_PRIMITIVE:{kind}")
        parts.append("</svg>")
        output.write_text("\n".join(parts) + "\n", encoding="utf-8")
        return {"writer": "svg", "nodes": len(ast.nodes), "output": str(output)}


class DrawingMLWriter:
    """Serialize the same AST to native PowerPoint DrawingML objects."""
    def __init__(self, root: Path | None = None, preserve_source_ids: bool = False):
        self.root = root
        self.preserve_source_ids = preserve_source_ids

    def _name(self, shape, e: dict, part: str) -> None:
        _tag(shape, e, part, self.preserve_source_ids)

    def _line(self, slide, e: dict, part: str = "line") -> None:
        shape = slide.shapes.add_connector(
            MSO_CONNECTOR.STRAIGHT, Inches(e["x1"]), Inches(e["y1"]),
            Inches(e["x2"]), Inches(e["y2"])
        )
        self._name(shape, e, part)
        color = _rgb(e.get("color", "#43525B"))
        shape.line.color.rgb = color
        shape.line.width = Pt(e.get("sw", 1))
        if e.get("dash"):
            shape.line.dash_style = MSO_LINE_DASH_STYLE.DASH
        _no_effects(shape)
        if e.get("arrow"):
            angle = math.degrees(math.atan2(e["y2"]-e["y1"], e["x2"]-e["x1"]))
            size = float(e.get("arrow_size", .105))
            arrow = slide.shapes.add_shape(
                MSO_SHAPE.ISOSCELES_TRIANGLE,
                Inches(e["x2"]-size/2), Inches(e["y2"]-size/2),
                Inches(size), Inches(size)
            )
            self._name(arrow, e, "arrowhead")
            arrow.rotation = angle + 90
            arrow.fill.solid()
            arrow.fill.fore_color.rgb = color
            arrow.line.color.rgb = color
            _no_effects(arrow)

    def _text(self, slide, e: dict, default_font: str) -> None:
        shape = slide.shapes.add_textbox(
            Inches(e["x"]), Inches(e["y"]), Inches(e["w"]), Inches(e["h"])
        )
        self._name(shape, e, "text")
        frame = shape.text_frame
        frame.clear()
        frame.word_wrap = True
        frame.margin_left = Inches(.02)
        frame.margin_right = Inches(.02)
        frame.margin_top = Inches(.008)
        frame.margin_bottom = Inches(.008)
        frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        align = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}[e.get("align", "center")]
        for index, line in enumerate(str(e["text"]).split("\n")):
            paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
            paragraph.alignment = align
            paragraph.space_before = Pt(0)
            paragraph.space_after = Pt(0)
            paragraph.line_spacing = 1
            run = paragraph.add_run()
            run.text = line
            run.font.name = e.get("font", default_font)
            run.font.size = Pt(e.get("size", 14))
            run.font.bold = e.get("bold", False)
            run.font.italic = e.get("italic", False)
            run.font.color.rgb = _rgb(e.get("color", "#28343C"))
        if e.get("rotation"):
            shape.rotation = e["rotation"]
        _no_effects(shape)

    def _shape(self, slide, e: dict, kind: int, part: str) -> None:
        shape = slide.shapes.add_shape(
            kind, Inches(e["x"]), Inches(e["y"]), Inches(e["w"]), Inches(e["h"])
        )
        self._name(shape, e, part)
        shape.fill.solid()
        shape.fill.fore_color.rgb = _rgb(e.get("fill", "#FFFFFF"))
        shape.line.color.rgb = _rgb(e.get("stroke", "#43525B"))
        shape.line.width = Pt(e.get("sw", 1))
        if e.get("dash"):
            shape.line.dash_style = MSO_LINE_DASH_STYLE.DASH
        _no_effects(shape)

    def write(self, ast: FigureAST, output: str | Path) -> dict:
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        spec = ast.to_spec()
        default_font = spec.get("style", {}).get("font", "Times New Roman")
        prs = Presentation()
        prs.slide_width = Inches(ast.canvas.get("width_in"))
        prs.slide_height = Inches(ast.canvas.get("height_in"))
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = _rgb("#FFFFFF")
        for node in ast.nodes:
            e, kind = node.to_element(), node.kind
            if kind == "image":
                image = _resolve_image(e["path"], self.root)
                shape = slide.shapes.add_picture(
                    str(image), Inches(e["x"]), Inches(e["y"]),
                    width=Inches(e["w"]), height=Inches(e["h"])
                )
                self._name(shape, e, "picture")
            elif kind == "text":
                self._text(slide, e, default_font)
            elif kind == "rect":
                self._shape(slide, e, MSO_SHAPE.ROUNDED_RECTANGLE if e.get("radius", 0) > 0 else MSO_SHAPE.RECTANGLE, "rect")
            elif kind == "trapezoid":
                self._shape(slide, e, MSO_SHAPE.TRAPEZOID, "trapezoid")
            elif kind == "line":
                self._line(slide, e)
            elif kind == "polyline":
                for index, (a, b) in enumerate(zip(e["points"][:-1], e["points"][1:]), 1):
                    self._line(slide, {
                        "id": e.get("id"), "semantic_id": e.get("semantic_id"),
                        "semantic_role": e.get("semantic_role"),
                        "x1": a[0], "y1": a[1], "x2": b[0], "y2": b[1],
                        "color": e.get("color", "#43525B"), "sw": e.get("sw", 1.2)
                    }, f"segment-{index:02d}")
            elif kind == "polygon":
                points = e["points"]
                builder = slide.shapes.build_freeform(
                    start_x=round(points[0][0]*1000),
                    start_y=round(points[0][1]*1000),
                    scale=Inches(.001)
                )
                builder.add_line_segments(
                    [(round(x*1000), round(y*1000)) for x, y in points[1:]],
                    close=True
                )
                shape = builder.convert_to_shape()
                self._name(shape, e, "polygon")
                shape.fill.solid()
                shape.fill.fore_color.rgb = _rgb(e.get("fill", "#FFFFFF"))
                shape.line.color.rgb = _rgb(e.get("stroke", "#43525B"))
                shape.line.width = Pt(e.get("sw", 1))
                _no_effects(shape)
            elif kind == "ellipse":
                self._shape(slide, e, MSO_SHAPE.OVAL, "ellipse")
            elif kind in {"grid", "stack_grid"}:
                x, y, w, h = [e[k] for k in ("x", "y", "w", "h")]
                rows, cols = int(e["rows"]), int(e["cols"])
                if kind == "stack_grid":
                    offset = float(e.get("offset", .16))
                    for layer in range(int(e.get("layers", 5))-1, 0, -1):
                        self._shape(slide, {
                            "id": e.get("id"), "semantic_id": e.get("semantic_id"),
                            "semantic_role": e.get("semantic_role"),
                            "x": x+offset*layer, "y": y-offset*layer, "w": w, "h": h,
                            "fill": "#FFFFFF", "stroke": e.get("border", "#98A6AF"), "sw": .8
                        }, MSO_SHAPE.RECTANGLE, f"stack-layer-{layer}")
                self._shape(slide, {
                    "id": e.get("id"), "semantic_id": e.get("semantic_id"),
                    "semantic_role": e.get("semantic_role"),
                    "x": x, "y": y, "w": w, "h": h,
                    "fill": e.get("fill", "#FBFCFD"),
                    "stroke": e.get("border", "#98A6AF"), "sw": .8
                }, MSO_SHAPE.RECTANGLE, "grid-base")
                for col in range(1, cols):
                    xx = x + w*col/cols
                    self._line(slide, {
                        "id": e.get("id"), "semantic_id": e.get("semantic_id"),
                        "semantic_role": e.get("semantic_role"),
                        "x1": xx, "y1": y, "x2": xx, "y2": y+h,
                        "color": e.get("stroke", "#D7DEE3"), "sw": e.get("sw", .4)
                    }, f"grid-column-{col:02d}")
                for row in range(1, rows):
                    yy = y + h*row/rows
                    self._line(slide, {
                        "id": e.get("id"), "semantic_id": e.get("semantic_id"),
                        "semantic_role": e.get("semantic_role"),
                        "x1": x, "y1": yy, "x2": x+w, "y2": yy,
                        "color": e.get("stroke", "#D7DEE3"), "sw": e.get("sw", .4)
                    }, f"grid-row-{row:02d}")
            elif kind == "sensor":
                x, y, scale = float(e["x"]), float(e["y"]), float(e.get("scale", 1))
                variant, color = int(e.get("variant", 0)), e.get("color", "#43525B")
                if variant == 0:
                    shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x+scale*.025), Inches(y+scale*.025), Inches(scale*.15), Inches(scale*.15))
                elif variant == 1:
                    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x+scale*.02), Inches(y+scale*.06), Inches(scale*.17), Inches(scale*.14))
                elif variant == 2:
                    shape = slide.shapes.add_shape(MSO_SHAPE.PARALLELOGRAM, Inches(x+scale*.015), Inches(y+scale*.04), Inches(scale*.19), Inches(scale*.19))
                else:
                    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x+scale*.06), Inches(y+scale*.025), Inches(scale*.09), Inches(scale*.24))
                self._name(shape, e, "sensor-body")
                shape.fill.solid()
                shape.fill.fore_color.rgb = _rgb("#E8F0F3")
                shape.line.color.rgb = _rgb(color)
                _no_effects(shape)
                self._line(slide, {
                    "id": e.get("id"), "semantic_id": e.get("semantic_id"),
                    "semantic_role": e.get("semantic_role"),
                    "x1": x+scale*.10, "y1": y+scale*.20,
                    "x2": x+scale*.10, "y2": y+scale*.30,
                    "color": color, "sw": 1
                }, "sensor-stem")
                self._shape(slide, {
                    "id": e.get("id"), "semantic_id": e.get("semantic_id"),
                    "semantic_role": e.get("semantic_role"),
                    "x": x+scale*.015, "y": y+scale*.30,
                    "w": scale*.18, "h": scale*.045,
                    "fill": "#FFFFFF", "stroke": color, "sw": 1
                }, MSO_SHAPE.RECTANGLE, "sensor-foot")
            elif kind == "graph":
                x, y, w, h = [float(e[k]) for k in ("x", "y", "w", "h")]
                nodes = e["nodes"]
                for index, (a, b) in enumerate(e["edges"], 1):
                    self._line(slide, {
                        "id": e.get("id"), "semantic_id": e.get("semantic_id"),
                        "semantic_role": e.get("semantic_role"),
                        "x1": x+nodes[a][0]*w, "y1": y+nodes[a][1]*h,
                        "x2": x+nodes[b][0]*w, "y2": y+nodes[b][1]*h,
                        "color": e.get("edge", "#43525B"), "sw": e.get("sw", .7)
                    }, f"graph-edge-{index:02d}")
                radius = float(e.get("r", .034))
                for index, (nx, ny) in enumerate(nodes, 1):
                    shape = slide.shapes.add_shape(
                        MSO_SHAPE.OVAL,
                        Inches(x+nx*w-radius), Inches(y+ny*h-radius),
                        Inches(radius*2), Inches(radius*2)
                    )
                    self._name(shape, e, f"graph-node-{index:02d}")
                    shape.fill.solid()
                    shape.fill.fore_color.rgb = _rgb(e.get("fill", "#7896A6"))
                    shape.line.fill.background()
                    _no_effects(shape)
            else:
                raise ValueError(f"UNSUPPORTED_DRAWINGML_PRIMITIVE:{kind}")
        prs.save(output)
        return {"writer": "drawingml", "nodes": len(ast.nodes),
                "shape_count": len(slide.shapes), "output": str(output)}


def render_ast(ast: FigureAST, svg_path: str | Path, pptx_path: str | Path,
               root: Path | None = None, preserve_source_ids: bool = False) -> dict:
    svg_result = SvgWriter(root=root).write(ast, svg_path)
    pptx_result = DrawingMLWriter(root=root, preserve_source_ids=preserve_source_ids).write(ast, pptx_path)
    return {"ast_sha256": ast.ast_sha256, "source_sha256": ast.source_sha256,
            "svg": svg_result, "pptx": pptx_result}
