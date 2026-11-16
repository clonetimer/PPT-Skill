#!/usr/bin/env python3
"""Render a FigureSpec through the experimental immutable AST and dual writers."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from figure_ast import load_figure_ast
from figure_ast_writers import render_ast


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("figure_spec", type=Path)
    parser.add_argument("--svg", type=Path, required=True)
    parser.add_argument("--pptx", type=Path, required=True)
    parser.add_argument("--ast-json", type=Path)
    parser.add_argument("--preserve-source-ids", action="store_true")
    args = parser.parse_args()
    ast = load_figure_ast(args.figure_spec)
    result = render_ast(
        ast, args.svg, args.pptx,
        root=Path(__file__).resolve().parents[1],
        preserve_source_ids=args.preserve_source_ids,
    )
    if args.ast_json:
        args.ast_json.parent.mkdir(parents=True, exist_ok=True)
        args.ast_json.write_text(ast.to_json(), encoding="utf-8")
        result["ast_json"] = str(args.ast_json)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
