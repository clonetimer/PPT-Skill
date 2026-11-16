#!/usr/bin/env python3
"""Immutable, backend-neutral intermediate representation for FigureSpec."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Iterable

AST_VERSION = "1.0.0"
SUPPORTED_PRIMITIVES = frozenset({
    "image", "text", "rect", "trapezoid", "line", "polyline",
    "polygon", "ellipse", "grid", "stack_grid", "sensor", "graph",
})

GEOMETRY_KEYS = frozenset({
    "x", "y", "w", "h", "x1", "y1", "x2", "y2", "points",
    "nodes", "edges", "rows", "cols", "layers", "offset",
    "scale", "variant", "rotation",
})
PAINT_KEYS = frozenset({
    "fill", "stroke", "sw", "color", "dash", "radius",
    "edge", "border", "r",
})
CONTENT_KEYS = frozenset({
    "text", "font", "size", "bold", "italic", "align", "path",
})
SEMANTIC_KEYS = frozenset({
    "id", "semantic_id", "semantic_role", "evidence_ref", "semantic_link",
})


@dataclass(frozen=True)
class FrozenMap:
    """Small immutable mapping used by the AST; nested values are frozen too."""
    items: tuple[tuple[str, Any], ...]

    def get(self, key: str, default: Any = None) -> Any:
        for name, value in self.items:
            if name == key:
                return value
        return default

    def to_dict(self) -> dict[str, Any]:
        return {key: thaw(value) for key, value in self.items}


def freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return FrozenMap(tuple((str(k), freeze(v)) for k, v in value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(freeze(v) for v in value)
    return value


def thaw(value: Any) -> Any:
    if isinstance(value, FrozenMap):
        return value.to_dict()
    if isinstance(value, tuple):
        return [thaw(v) for v in value]
    return value


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _finite_numbers(value: Any, where: str) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        if not math.isfinite(float(value)):
            raise ValueError(f"NON_FINITE_GEOMETRY:{where}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _finite_numbers(child, f"{where}[{index}]")


def _require(element: dict[str, Any], keys: Iterable[str], index: int) -> None:
    missing = [key for key in keys if key not in element]
    if missing:
        raise ValueError(f"MISSING_GEOMETRY:element[{index}]:{','.join(missing)}")


def _validate_element(element: dict[str, Any], index: int) -> None:
    kind = element.get("type")
    if kind not in SUPPORTED_PRIMITIVES:
        raise ValueError(f"UNSUPPORTED_PRIMITIVE:element[{index}]:{kind}")
    required = {
        "image": ("x", "y", "w", "h", "path"),
        "text": ("x", "y", "w", "h", "text"),
        "rect": ("x", "y", "w", "h"),
        "trapezoid": ("x", "y", "w", "h"),
        "line": ("x1", "y1", "x2", "y2"),
        "polyline": ("points",),
        "polygon": ("points",),
        "ellipse": ("x", "y", "w", "h"),
        "grid": ("x", "y", "w", "h", "rows", "cols"),
        "stack_grid": ("x", "y", "w", "h", "rows", "cols"),
        "sensor": ("x", "y", "scale"),
        "graph": ("x", "y", "w", "h", "nodes", "edges"),
    }[kind]
    _require(element, required, index)
    for key in GEOMETRY_KEYS:
        if key in element:
            _finite_numbers(element[key], f"element[{index}].{key}")
    if kind in {"image", "text", "rect", "trapezoid", "ellipse", "grid", "stack_grid", "graph"}:
        if float(element["w"]) <= 0 or float(element["h"]) <= 0:
            raise ValueError(f"NON_POSITIVE_SIZE:element[{index}]")
    if kind in {"polyline", "polygon"}:
        points = element["points"]
        minimum = 2 if kind == "polyline" else 3
        if not isinstance(points, list) or len(points) < minimum:
            raise ValueError(f"INVALID_POINTS:element[{index}]")
        if any(not isinstance(p, (list, tuple)) or len(p) != 2 for p in points):
            raise ValueError(f"INVALID_POINT_PAIR:element[{index}]")
    if kind == "graph":
        nodes, edges = element["nodes"], element["edges"]
        if not isinstance(nodes, list) or not isinstance(edges, list):
            raise ValueError(f"INVALID_GRAPH_ARRAYS:element[{index}]")
        for edge in edges:
            if (not isinstance(edge, (list, tuple)) or len(edge) != 2
                    or any(not isinstance(i, int) or i < 0 or i >= len(nodes) for i in edge)):
                raise ValueError(f"INVALID_GRAPH_EDGE:element[{index}]:{edge}")
    if kind in {"grid", "stack_grid"}:
        if int(element["rows"]) < 1 or int(element["cols"]) < 1:
            raise ValueError(f"INVALID_GRID_DIMENSIONS:element[{index}]")


@dataclass(frozen=True)
class PrimitiveNode:
    """One source-ordered primitive with render-independent sections."""
    node_key: str
    kind: str
    geometry: FrozenMap
    paint: FrozenMap
    content: FrozenMap
    semantics: FrozenMap
    extensions: FrozenMap

    def to_element(self) -> dict[str, Any]:
        result: dict[str, Any] = {"type": self.kind}
        for section in (self.geometry, self.paint, self.content,
                        self.semantics, self.extensions):
            result.update(section.to_dict())
        return result


@dataclass(frozen=True)
class FigureAST:
    figure_id: str
    canvas: FrozenMap
    style: FrozenMap
    nodes: tuple[PrimitiveNode, ...]
    metadata: FrozenMap
    source_sha256: str
    ast_sha256: str
    version: str = AST_VERSION

    @classmethod
    def from_spec(cls, spec: dict[str, Any]) -> "FigureAST":
        if not isinstance(spec, dict):
            raise TypeError("FIGURE_SPEC_MUST_BE_OBJECT")
        canvas = spec.get("canvas")
        elements = spec.get("elements")
        if not isinstance(canvas, dict) or not isinstance(elements, list):
            raise ValueError("FIGURE_SPEC_REQUIRES_CANVAS_AND_ELEMENTS")
        for key in ("width_in", "height_in"):
            if key not in canvas or not math.isfinite(float(canvas[key])) or float(canvas[key]) <= 0:
                raise ValueError(f"INVALID_CANVAS:{key}")
        seen_ids: set[str] = set()
        nodes: list[PrimitiveNode] = []
        for index, element in enumerate(elements):
            if not isinstance(element, dict):
                raise ValueError(f"ELEMENT_MUST_BE_OBJECT:{index}")
            _validate_element(element, index)
            source_id = element.get("id")
            if source_id is not None:
                source_id = str(source_id)
                if source_id in seen_ids:
                    raise ValueError(f"DUPLICATE_ELEMENT_ID:{source_id}")
                seen_ids.add(source_id)
            node_key = source_id or f"node_{index + 1:04d}"
            sections: dict[str, dict[str, Any]] = {
                "geometry": {}, "paint": {}, "content": {},
                "semantics": {}, "extensions": {},
            }
            for key, value in element.items():
                if key == "type":
                    continue
                if key in GEOMETRY_KEYS:
                    sections["geometry"][key] = value
                elif key in PAINT_KEYS:
                    sections["paint"][key] = value
                elif key in CONTENT_KEYS:
                    sections["content"][key] = value
                elif key in SEMANTIC_KEYS:
                    sections["semantics"][key] = value
                else:
                    sections["extensions"][key] = value
            nodes.append(PrimitiveNode(
                node_key=node_key,
                kind=str(element["type"]),
                geometry=freeze(sections["geometry"]),
                paint=freeze(sections["paint"]),
                content=freeze(sections["content"]),
                semantics=freeze(sections["semantics"]),
                extensions=freeze(sections["extensions"]),
            ))
        metadata = {k: v for k, v in spec.items()
                    if k not in {"id", "canvas", "style", "elements"}}
        source_sha = hashlib.sha256(_canonical_bytes(spec)).hexdigest()
        provisional = {
            "version": AST_VERSION,
            "figure_id": str(spec.get("id", "unnamed-figure")),
            "canvas": canvas,
            "style": spec.get("style", {}),
            "nodes": [n.to_element() for n in nodes],
            "metadata": metadata,
            "source_sha256": source_sha,
        }
        ast_sha = hashlib.sha256(_canonical_bytes(provisional)).hexdigest()
        return cls(
            figure_id=str(spec.get("id", "unnamed-figure")),
            canvas=freeze(canvas),
            style=freeze(spec.get("style", {})),
            nodes=tuple(nodes),
            metadata=freeze(metadata),
            source_sha256=source_sha,
            ast_sha256=ast_sha,
        )

    def to_spec(self) -> dict[str, Any]:
        result = {
            "id": self.figure_id,
            "canvas": self.canvas.to_dict(),
            "style": self.style.to_dict(),
            "elements": [node.to_element() for node in self.nodes],
        }
        result.update(self.metadata.to_dict())
        return result

    def to_dict(self) -> dict[str, Any]:
        return {
            "ast_version": self.version,
            "figure_id": self.figure_id,
            "canvas": self.canvas.to_dict(),
            "style": self.style.to_dict(),
            "nodes": [
                {
                    "node_key": n.node_key,
                    "kind": n.kind,
                    "geometry": n.geometry.to_dict(),
                    "paint": n.paint.to_dict(),
                    "content": n.content.to_dict(),
                    "semantics": n.semantics.to_dict(),
                    "extensions": n.extensions.to_dict(),
                }
                for n in self.nodes
            ],
            "metadata": self.metadata.to_dict(),
            "source_sha256": self.source_sha256,
            "ast_sha256": self.ast_sha256,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\\n"


def load_figure_ast(path: str) -> FigureAST:
    with open(path, "r", encoding="utf-8") as stream:
        return FigureAST.from_spec(json.load(stream))
