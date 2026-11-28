#!/usr/bin/env python3
"""Plan scientific figures from explicit, evidence-linked semantic objects.

An agent or researcher reads the source and authors this input. This module does
not parse arbitrary code or decide whether a scientific claim is true. It makes
the intended visual vocabulary and its evidence boundary executable.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET


class PlanError(ValueError):
    """The supplied scientific plan cannot be drawn without guessing."""


GLYPHS = {
    'tensor': 'tensor_planes', 'time_series': 'signal_traces',
    'conv1d': 'temporal_kernel', 'embedding': 'indexed_vectors',
    'add': 'sum_junction', 'graph_attention': 'attention_heads',
    'pool': 'group_reduction', 'concat': 'segmented_concat',
    'projection': 'projection_map', 'head': 'task_output',
    'gate': 'decision_boundary', 'process': 'process_box',
}
INTENTS = {'reconstruct', 'redraw', 'conceptual', 'quantitative', 'workflow'}
EVIDENCE_KINDS = {'paper', 'code', 'reference_image', 'user_brief', 'synthetic', 'data'}
PORTS = {'left', 'right', 'top', 'bottom', 'input', 'output'}


def _require(condition, message):
    if not condition:
        raise PlanError(message)


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _positive_int(value):
    return type(value) is int and value > 0


def _shape(shape, owner):
    _require(isinstance(shape, list) and shape, f'{owner}: shape must name its dimensions')
    _require(all(_positive_int(n) or _text(n) for n in shape),
             f'{owner}: shape dimensions must be positive integers or explicit symbols')


def _evidence(records, root):
    _require(isinstance(records, list) and records, 'At least one evidence record is required')
    ids = set()
    for record in records:
        _require(isinstance(record, dict), 'Each evidence record must be an object')
        rid = record.get('id')
        _require(_text(rid) and rid not in ids, 'Evidence IDs must be present and unique')
        ids.add(rid)
        _require(_text(record.get('kind')) and record['kind'] in EVIDENCE_KINDS,
                 f'{rid}: unsupported evidence kind')
        _require(_text(record.get('locator')), f'{rid}: a precise evidence locator is required')
        _require(_text(record.get('path')), f'{rid}: evidence path is required')
        digest = record.get('sha256', '')
        _require(isinstance(digest, str) and re.fullmatch(r'[0-9a-f]{64}', digest),
                 f'{rid}: evidence SHA-256 must contain 64 lowercase hexadecimal characters')
        path = Path(record['path'])
        path = path if path.is_absolute() else root / path
        _require(path.is_file(), f'{rid}: evidence file does not exist: {record["path"]}')
        _require(hashlib.sha256(path.read_bytes()).hexdigest() == digest,
                 f'{rid}: evidence hash mismatch; re-read the changed source before replanning')
        if record['kind'] == 'reference_image':
            _visual_source(path, rid)
    return ids


def _visual_source(path, rid):
    """Verify file type, not whether the image scientifically supports a claim."""
    if path.suffix.lower() == '.svg':
        try:
            root = ET.parse(path).getroot()
            if root.tag == '{http://www.w3.org/2000/svg}svg':
                return
        except (ET.ParseError, OSError):
            pass
    else:
        from PIL import Image, UnidentifiedImageError
        try:
            with Image.open(path) as picture:
                picture.verify()
            return
        except (UnidentifiedImageError, OSError, ValueError, SyntaxError):
            pass
    raise PlanError(f'{rid}: reference_image must be a readable raster image or SVG; '
                    'render a PDF figure/page first, rather than relabeling text as visual evidence')


def _references(item, evidence_ids):
    refs = item.get('evidence')
    _require(isinstance(refs, list) and refs and all(_text(x) for x in refs),
             f'{item.get("id")}: evidence references must be a nonempty list')
    _require(set(refs) <= evidence_ids, f'{item.get("id")}: unknown evidence reference')


def _node_params(node, intent):
    kind, params, owner = node['kind'], node['params'], node['id']
    if 'shape' in params:
        _shape(params['shape'], owner)
    if kind == 'tensor':
        _shape(params.get('shape'), owner)
    if kind == 'graph_attention':
        _require(_positive_int(params.get('heads')), f'{owner}: heads must be a positive integer')
        params.setdefault('merge', 'unknown')
        params.setdefault('adjacency', 'unknown')
        _require(_text(params['merge']) and params['merge'] in {'concat', 'mean', 'unknown'},
                 f'{owner}: unsupported head merge')
        _require(_text(params['adjacency']) and params['adjacency'] in {'known', 'unknown'},
                 f'{owner}: invalid adjacency status')
        if params['adjacency'] == 'unknown':
            _require(not params.get('graph_edges') and not params.get('graph_nodes'),
                     f'{owner}: unknown adjacency cannot declare concrete graph nodes or edges')
        else:
            vertices, links = params.get('graph_nodes'), params.get('graph_edges')
            _require(isinstance(vertices, list) and len(vertices) > 0,
                     f'{owner}: known adjacency requires graph_nodes')
            _require(isinstance(links, list), f'{owner}: known adjacency requires graph_edges')
            _require(all(isinstance(edge, list) and len(edge) == 2 and
                         all(type(i) is int and 0 <= i < len(vertices) for i in edge)
                         for edge in links), f'{owner}: adjacency has an invalid graph endpoint')
    if kind == 'pool':
        _require(_positive_int(params.get('groups')), f'{owner}: pool groups must be a positive integer')
        _require(params.get('reduction') == 'mean', f'{owner}: this renderer supports explicit mean pooling')
        if params.get('shape') and type(params['shape'][0]) is int:
            _require(params['shape'][0] == params['groups'], f'{owner}: pool groups disagree with output shape')
    if kind == 'head':
        _require(_positive_int(params.get('outputs')), f'{owner}: head outputs must be a positive integer')
        _require(_text(params.get('activation')), f'{owner}: head activation must be explicit, or written unknown')
    if kind == 'gate':
        _require(_text(params.get('threshold')), f'{owner}: gate threshold must be explicit, or written unknown')
    if kind == 'process' and intent == 'reconstruct':
        _require(params.get('opaque') is True and _text(params.get('explanation')),
                 f'{owner}: an opaque process needs an evidence-boundary explanation')


def _route(intent):
    return {
        'reconstruct': {'renderer': 'native', 'profile': 'scientific_semantic',
                        'reason': 'Reconstruct evidenced scientific objects using object-specific glyphs.'},
        'redraw': {'renderer': 'source_spec', 'profile': 'source_matched',
                   'reason': 'Use the existing source-specific FigureSpec workflow and inspect actual source anchors; '
                             'the semantic compiler does not replace source artwork with its preset glyphs.'},
        'workflow': {'renderer': 'native', 'profile': 'engineering_flow',
                     'reason': 'Process and control flow may use ordinary functional boxes.'},
        'conceptual': {'renderer': 'imagegen', 'profile': 'conceptual',
                       'reason': 'Use a disclosed conceptual illustration; do not treat it as exact data or topology.'},
        'quantitative': {'renderer': 'existing_chart_pipeline', 'profile': 'quantitative',
                         'reason': 'Use the evidence/data-linked chart pipeline, not schematic figure glyphs.'},
    }[intent]


def plan_figure(brief: dict, source_root: Path) -> dict:
    """Validate source references and attach the chosen route and glyphs.

    ``source_root`` resolves relative evidence paths. It is intentionally
    explicit: the caller's working directory must not change the evidence.
    """
    _require(isinstance(brief, dict), 'FigurePlan must be an object')
    plan = copy.deepcopy(brief)
    _require(plan.get('schema_version') == '1.0', 'Unsupported FigurePlan schema_version')
    for key in ('id', 'title', 'claim'):
        _require(_text(plan.get(key)), f'{key} must be nonempty text')
    _require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', plan['id']),
             'id must be a portable filename without path separators')
    intent = plan.get('intent')
    _require(_text(intent) and intent in INTENTS, 'Unsupported figure intent')
    _require(_text(plan.get('medium')) and plan['medium'] in {'figure', 'slide'}, 'medium must be figure or slide')
    canvas = plan.get('canvas', {})
    _require(isinstance(canvas, dict), 'canvas must be an object')
    _require(all(_number(canvas.get(k)) and canvas[k] > 0 for k in ('width_in', 'height_in')),
             'canvas dimensions must be positive finite numbers')
    if intent in {'reconstruct', 'workflow'}:
        _require(all(1 <= canvas[k] <= 56 for k in ('width_in', 'height_in')),
                 'Native PowerPoint canvas dimensions must be within 1–56 inches')
    style = plan.get('style', {})
    _require(isinstance(style, dict), 'style must be an object')
    _require('font' not in style or _text(style['font']), 'style.font must be nonempty text')
    _require('font_size' not in style or (_number(style['font_size']) and style['font_size'] >= 9),
             'style.font_size must be a finite value of at least 9 pt')
    panels = plan.get('panels', [])
    _require(isinstance(panels, list), 'panels must be a list')
    for panel in panels:
        _require(isinstance(panel, dict) and _text(panel.get('label')), 'panels need a text label')
        _require(all(_number(panel.get(k)) for k in ('x', 'y', 'w')) and
                 _number(panel.get('h', .3)) and _number(panel.get('size', 13)),
                 'panels need finite x, y, w, h and size values')
        _require(panel['x'] >= 0 and panel['y'] >= 0 and panel['w'] > 0 and panel.get('h', .3) > 0 and
                 panel['x'] + panel['w'] <= canvas['width_in'] and
                 panel['y'] + panel.get('h', .3) <= canvas['height_in'] and panel.get('size', 13) >= 9,
                 'panels must fit the canvas with readable text')
    _require('disclosure' not in plan or isinstance(plan['disclosure'], str), 'disclosure must be text')
    evidence_ids = _evidence(plan.get('evidence'), Path(source_root))
    if intent == 'redraw':
        _require(any(r['kind'] == 'reference_image' for r in plan['evidence']),
                 'A source redraw requires inspected reference_image evidence')
        anchors = plan.get('source_anchors')
        _require(isinstance(anchors, list) and len(anchors) >= 3 and all(_text(x) for x in anchors),
                 'A source redraw requires at least three concrete source_anchors')
        _require(len({x.strip().casefold() for x in anchors}) == len(anchors),
                 'Source redraw anchors must be distinct')
    nodes = plan.get('nodes')
    _require(isinstance(nodes, list), 'nodes must be a list')
    if intent in {'reconstruct', 'redraw', 'workflow'}:
        _require(bool(nodes), 'A native figure needs semantic nodes')
    node_ids = set()
    for node in nodes:
        _require(isinstance(node, dict), 'Each node must be an object')
        nid = node.get('id')
        _require(_text(nid) and nid not in node_ids, 'Node IDs must be present and unique')
        node_ids.add(nid)
        _require(_text(node.get('label')), f'{nid}: node label is required')
        kind = node.get('kind')
        _require(_text(kind) and kind in GLYPHS, f'{nid}: Unsupported node kind {kind!r}; supply a supported semantic kind')
        _references(node, evidence_ids)
        _require(isinstance(node.get('params'), dict), f'{nid}: params must be an object')
        _require('font' not in node or _text(node['font']), f'{nid}: font must be nonempty text')
        _require('font_size' not in node or (_number(node['font_size']) and node['font_size'] >= 9),
                 f'{nid}: font_size must be at least 9 pt')
        _node_params(node, intent)
        box = node.get('box')
        _require(isinstance(box, list) and len(box) == 4 and all(_number(v) for v in box),
                 f'{nid}: box must have four finite numbers')
        x, y, w, h = box
        _require(x >= 0 and y >= 0 and w > 0 and h > 0 and
                 x + w <= canvas['width_in'] and y + h <= canvas['height_in'],
                 f'{nid}: box must fit the canvas')
        glyph = GLYPHS[kind]
        _require('glyph' not in node or node['glyph'] == glyph,
                 f'{nid}: glyph override contradicts its scientific kind')
        node['glyph'] = glyph
        node['requirements'] = {'glyph': glyph, 'evidence': list(node['evidence'])}
        if kind == 'graph_attention':
            node['requirements']['heads'] = node['params']['heads']
    edges = plan.get('edges')
    _require(isinstance(edges, list), 'edges must be a list')
    edge_ids = set()
    for edge in edges:
        _require(isinstance(edge, dict), 'Each edge must be an object')
        eid = edge.get('id')
        _require(_text(eid) and eid not in edge_ids, 'Edge IDs must be present and unique')
        edge_ids.add(eid)
        _require(_text(edge.get('source')) and _text(edge.get('target')) and
                 edge['source'] in node_ids and edge['target'] in node_ids,
                 f'{eid}: unknown edge endpoint')
        _references(edge, evidence_ids)
        _require(_text(edge.get('kind')) and edge['kind'] in {'data', 'conditioning', 'residual'},
                 f'{eid}: unsupported edge kind')
        for key in ('source_port', 'target_port'):
            _require(key not in edge or (_text(edge[key]) and edge[key] in PORTS), f'{eid}: unsupported endpoint port')
        via = edge.get('via', [])
        _require(isinstance(via, list) and all(isinstance(p, list) and len(p) == 2 and
                 all(_number(v) for v in p) for p in via), f'{eid}: invalid connector waypoints')
        _require(all(0 <= p[0] <= canvas['width_in'] and 0 <= p[1] <= canvas['height_in']
                     for p in via), f'{eid}: connector waypoints leave the canvas')
    critical = plan.get('critical_edges')
    _require(isinstance(critical, list) and all(_text(x) for x in critical),
             'critical_edges must be a list of source-derived edge IDs')
    _require(set(critical) <= edge_ids, 'A source-derived critical edge is missing from edges')
    if intent in {'reconstruct', 'redraw'} and len(nodes) > 1:
        _require(bool(critical), 'A method figure requires nonempty source-derived critical edges')
    unknowns = plan.get('unknowns')
    _require(isinstance(unknowns, list) and all(_text(x) for x in unknowns), 'unknowns must be a list of text')
    for node in nodes:
        if node['kind'] == 'graph_attention':
            for field in ('adjacency', 'merge'):
                if node['params'][field] == 'unknown':
                    note = f'{node["id"]}: {field} is unknown; the graphic must not imply a concrete implementation.'
                    if note not in unknowns:
                        unknowns.append(note)
    plan['route'] = _route(intent)
    plan['review_status'] = {'scientific_review': 'pending', 'visual_review': 'pending',
                             'source_reading': 'authored_by_agent_or_researcher'}
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('brief', type=Path)
    parser.add_argument('--source-root', type=Path,
                        help='Base for relative evidence paths; defaults to the brief directory')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = plan_figure(json.loads(args.brief.read_text(encoding='utf-8')),
                             args.source_root or args.brief.resolve().parent)
    except (PlanError, OSError, json.JSONDecodeError) as error:
        parser.exit(2, f'Figure planning failed: {error}\n')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{result["id"]}: {result["route"]["profile"]} → {args.out}')


if __name__ == '__main__':
    main()
