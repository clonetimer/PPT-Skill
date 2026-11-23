#!/usr/bin/env python3
"""Compile an evidence-linked FigurePlan to SVG and editable native PPTX."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory

from scientific_figure_plan import PlanError, plan_figure
from scientific_figure_glyphs import draw_node
from render_figure_spec import render


def _distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _default_ports(source, target):
    sx, sy, sw, sh = source['box']
    tx, ty, tw, th = target['box']
    if max(sy, ty) < min(sy + sh, ty + th):
        return ('right', 'left') if tx > sx else ('left', 'right')
    return ('bottom', 'top') if ty > sy else ('top', 'bottom')


def _route(edge, source, target):
    sp, tp = _default_ports(source, target)
    sp, tp = edge.get('source_port', sp), edge.get('target_port', tp)
    start, end = source['ports'][sp], target['ports'][tp]
    if edge.get('via'):
        points = [start, *edge['via'], end]
    elif abs(start[0] - end[0]) < 1e-8 or abs(start[1] - end[1]) < 1e-8:
        points = [start, end]
    elif sp in {'left', 'right', 'input', 'output'}:
        mx = (start[0] + end[0]) / 2
        points = [start, (mx, start[1]), (mx, end[1]), end]
    else:
        my = (start[1] + end[1]) / 2
        points = [start, (start[0], my), (end[0], my), end]
    points = [tuple(p) for i, p in enumerate(points) if i == 0 or _distance(p, points[i - 1]) > 1e-8]
    if len(points) < 2:
        raise PlanError(f'{edge["id"]}: connector endpoints coincide')
    return points, sp, tp


def _component_nodes(plan):
    nodes = copy.deepcopy(plan['nodes'])
    incoming = {n['id']: [] for n in nodes}
    for edge in plan['edges']:
        incoming[edge['target']].append(edge)
    for node in nodes:
        inputs = len([e for e in incoming[node['id']] if e['kind'] != 'conditioning'])
        if node['kind'] == 'add' and inputs < 2:
            raise PlanError(f'{node["id"]}: addition needs at least two real inputs')
        if node['kind'] == 'concat':
            if inputs < 2 or node['params'].get('inputs', inputs) != inputs:
                raise PlanError(f'{node["id"]}: concat inputs must match at least two actual incoming edges')
            node['params']['inputs'] = inputs
        node.setdefault('font', plan.get('style', {}).get('font', 'Noto Sans CJK SC'))
        node.setdefault('font_size', plan.get('style', {}).get('font_size', 11))
    return nodes


def _check_operator_ports(plan, components):
    """Keep operands and threshold controls distinct at the actual marks."""
    for node in plan['nodes']:
        if node['kind'] not in {'add', 'gate'}:
            continue
        routes = []
        for edge in plan['edges']:
            if edge['target'] == node['id']:
                points, _, target_port = _route(edge, components[edge['source']], components[edge['target']])
                routes.append((edge, points[-1], target_port))
        data = [(edge, end) for edge, end, _ in routes if edge['kind'] != 'conditioning']
        if node['kind'] == 'add':
            for i, (_, end) in enumerate(data):
                if any(_distance(end, other) < .03 for _, other in data[i + 1:]):
                    raise PlanError(f'{node["id"]}: addition operands need distinct input ports; '
                                    'do not merge them before the addition mark')
        else:
            for edge, end, port in routes:
                if edge['kind'] == 'conditioning' and (
                        port not in {'top', 'bottom'} or
                        any(_distance(end, other) < .03 for _, other in data)):
                    raise PlanError(f'{node["id"]}: conditioning must reach a separate top/bottom '
                                    'control port on the gate boundary')


def compile_figure(plan: dict) -> dict:
    """Compile a validated plan; unknown science stays explicit in the glyphs."""
    if plan.get('route', {}).get('renderer') != 'native':
        raise PlanError(f'This is a {plan.get("route", {}).get("renderer", "unplanned")} route, not a native figure. '
                        'Use the selected source-specific FigureSpec, imagegen or chart workflow.')
    nodes = _component_nodes(plan)
    components = {node['id']: draw_node(node) for node in nodes}
    _check_operator_ports(plan, components)
    elements = []
    for edge in plan['edges']:
        points, sp, tp = _route(edge, components[edge['source']], components[edge['target']])
        for index, (a, b) in enumerate(zip(points, points[1:])):
            elements.append({'type': 'line', 'x1': a[0], 'y1': a[1], 'x2': b[0], 'y2': b[1],
                'color': '#52677A' if edge['kind'] == 'conditioning' else '#263F52',
                'sw': 1.05, 'arrow': index == len(points) - 2, 'arrow_size': .075,
                'dash': edge['kind'] == 'conditioning', 'edge_id': edge['id'],
                'source': edge['source'], 'target': edge['target'],
                'source_port': sp, 'target_port': tp, 'segment_index': index,
                'evidence_refs': edge['evidence'], 'visual_role': 'scientific_connector'})
    for node in nodes:
        for element in components[node['id']]['elements']:
            item = copy.deepcopy(element)
            item['semantic_owner'] = node['id']
            item['evidence_refs'] = node['evidence']
            elements.append(item)
    font = plan.get('style', {}).get('font', 'Noto Sans CJK SC')
    for panel in plan.get('panels', []):
        elements.append({'type': 'text', 'text': panel['label'], 'x': panel['x'], 'y': panel['y'],
                         'w': panel['w'], 'h': panel.get('h', .3), 'size': panel.get('size', 13),
                         'bold': True, 'align': 'left', 'font': font, 'color': '#182E42',
                         'visual_role': 'panel_label'})
    if plan.get('disclosure'):
        elements.append({'type': 'text', 'text': plan['disclosure'], 'x': .3,
            'y': plan['canvas']['height_in'] - .38, 'w': plan['canvas']['width_in'] - .6,
            'h': .24, 'size': 9, 'align': 'left', 'font': font, 'color': '#53616A',
            'visual_role': 'evidence_disclosure'})
    for i, element in enumerate(elements):
        element['id'] = f'el_{i:04d}'
        element.setdefault('semantic_role', element.get('visual_role', 'scientific_mark'))
    payload = json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return {'schema_version': 'scientific-figure-1.0', 'id': plan['id'], 'title': plan['title'],
        'canvas': copy.deepcopy(plan['canvas']), 'style': {'font': font},
        'figure_contract': {'claim': plan['claim'], 'intent': plan['intent'],
                            'medium': plan['medium'], 'unverified': list(plan['unknowns'])},
        'evidence_records': copy.deepcopy(plan['evidence']),
        'plan_sha256': hashlib.sha256(payload).hexdigest(),
        'node_geometry': {key: {'ports': value['ports'], 'box': value['box']} for key, value in components.items()},
        'semantic_edges': [[e['source'], e['target']] for e in plan['edges']], 'elements': elements}


def _bounds(element):
    if element['type'] == 'line':
        return (min(element['x1'], element['x2']), min(element['y1'], element['y2']),
                max(element['x1'], element['x2']), max(element['y1'], element['y2']))
    if element['type'] in {'polygon', 'polyline'}:
        xs, ys = zip(*element['points'])
        return min(xs), min(ys), max(xs), max(ys)
    if all(k in element for k in ('x', 'y', 'w', 'h')):
        return element['x'], element['y'], element['x'] + element['w'], element['y'] + element['h']
    return None


def _segment_crosses_box(a, b, box):
    """Liang-Barsky clipping against the interior, excluding touching borders."""
    x, y, w, h = box
    left, right, top, bottom = x + .015, x + w - .015, y + .015, y + h - .015
    dx, dy = b[0] - a[0], b[1] - a[1]
    lo, hi = 0., 1.
    for p, q in ((-dx, a[0] - left), (dx, right - a[0]),
                 (-dy, a[1] - top), (dy, bottom - a[1])):
        if abs(p) < 1e-12:
            if q < 0:
                return False
        elif p < 0:
            lo = max(lo, q / p)
        else:
            hi = min(hi, q / p)
        if lo > hi:
            return False
    return lo < hi and hi > 0 and lo < 1


def audit_figure(plan: dict, spec: dict) -> dict:
    """Check actual marks and connector endpoints; leave visual judgment pending."""
    errors, warnings = [], []
    elements = spec.get('elements', [])
    expected_components = {n['id']: draw_node(n) for n in _component_nodes(plan)}
    for node in plan['nodes']:
        nid, kind = node['id'], node['kind']
        marks = [e for e in elements if e.get('semantic_owner') == nid]
        shapes = [e for e in marks if e['type'] not in {'text', 'image'}]
        if not shapes:
            errors.append(f'{nid}: missing visible scientific glyph')
        labels = [e.get('text', '') for e in marks if e['type'] == 'text' and e.get('visual_role') == 'node_label']
        normalized_label = ''.join(node['label'].split())
        if normalized_label not in {''.join(label.split()) for label in labels}:
            errors.append(f'{nid}: missing exact node label')
        if kind == 'tensor':
            if not any(e.get('visual_role') == 'tensor_plane' and e['type'] in {'rect', 'polygon', 'grid'} for e in shapes):
                errors.append(f'{nid}: missing tensor plane')
            dim_marks = [e for e in marks if e.get('visual_role') == 'dimension' and e['type'] == 'text']
            if not dim_marks:
                errors.append(f'{nid}: missing dimension annotation')
        if 'shape' in node['params']:
            dimension = ''.join('×'.join(str(v) for v in node['params']['shape']).split())
            captions = [''.join(e.get('text', '').split()) for e in marks
                        if e['type'] == 'text' and e.get('visual_role') != 'node_label']
            if not any(dimension in caption for caption in captions):
                errors.append(f'{nid}: visible dimensions disagree with the source plan')
        if kind == 'graph_attention':
            for i in range(node['params']['heads']):
                head = [e for e in shapes if e.get('head_index') == i]
                if not any(e['type'] == 'ellipse' for e in head) or not any(e['type'] == 'line' for e in head):
                    errors.append(f'{nid}: attention head {i} has no visible neighborhood mechanism')
                if not any(e['type'] == 'line' and e.get('visual_role') == 'head_input' and e.get('arrow') for e in head):
                    errors.append(f'{nid}: attention head {i} has no input connection')
                circles = [e for e in head if e['type'] == 'ellipse']
                known = node['params']['adjacency'] == 'known'
                relations = node['params'].get('graph_edges', []) if known else [[0, 1]]
                for a, b in relations:
                    routes = [e for e in head if e['type'] == 'line' and
                              e.get('visual_role') == 'attention_neighbor' and
                              (not known or e.get('graph_edge') == [a, b])]
                    if not routes or max(a, b) >= len(circles):
                        errors.append(f'{nid}: head {i} is missing neighborhood relation {a}→{b}')
                        continue
                    def touches(point, circle):
                        center = (circle['x'] + circle['w']/2, circle['y'] + circle['h']/2)
                        return abs(_distance(point, center) - circle['w']/2) <= .025
                    if not (touches((routes[0]['x1'], routes[0]['y1']), circles[a]) and
                            touches((routes[-1]['x2'], routes[-1]['y2']), circles[b]) and routes[-1].get('arrow')):
                        errors.append(f'{nid}: head {i} neighborhood relation misses its nodes')
                    for first, second in zip(routes, routes[1:]):
                        if _distance((first['x2'], first['y2']), (second['x1'], second['y1'])) > .015:
                            errors.append(f'{nid}: head {i} neighborhood relation is disconnected')
            unexpected = {e['head_index'] for e in marks if 'head_index' in e} - set(range(node['params']['heads']))
            if unexpected:
                errors.append(f'{nid}: unexpected attention head indices')
            text = '\n'.join(e.get('text', '') for e in marks)
            if node['params']['merge'] == 'unknown' and not ('融合未提供' in text or 'unknown' in text.lower()):
                errors.append(f'{nid}: unknown head merge is not disclosed')
        if kind == 'add' and not (any(e['type'] == 'ellipse' for e in shapes) and
                                  any(e.get('text') == '+' for e in marks)):
            errors.append(f'{nid}: missing explicit addition junction')
        if kind == 'concat':
            expected = len([e for e in plan['edges'] if e['target'] == nid and e['kind'] != 'conditioning'])
            if len([e for e in shapes if e.get('visual_role') == 'concat_segment']) != expected:
                errors.append(f'{nid}: concat segments do not match its inputs')
        if kind == 'pool' and not any(e.get('visual_role') == 'pool_output' for e in shapes):
            errors.append(f'{nid}: missing visible pooling output')
    for edge in plan['edges']:
        route = sorted([e for e in elements if e.get('edge_id') == edge['id']], key=lambda e: e.get('segment_index', -1))
        if not route or any(e['type'] != 'line' for e in route):
            errors.append(f'{edge["id"]}: missing visible connector')
            continue
        points, _, _ = _route(edge, expected_components[edge['source']], expected_components[edge['target']])
        if _distance((route[0]['x1'], route[0]['y1']), points[0]) > .015 or \
           _distance((route[-1]['x2'], route[-1]['y2']), points[-1]) > .015:
            errors.append(f'{edge["id"]}: connector misses its actual node ports')
        if not route[-1].get('arrow') or any(e.get('arrow') for e in route[:-1]):
            errors.append(f'{edge["id"]}: incorrect arrow direction/placement')
        for a, b in zip(route, route[1:]):
            if _distance((a['x2'], a['y2']), (b['x1'], b['y1'])) > .015:
                errors.append(f'{edge["id"]}: broken route')
        for part in route:
            for node in plan['nodes']:
                if node['id'] not in {edge['source'], edge['target']} and _segment_crosses_box(
                        (part['x1'], part['y1']), (part['x2'], part['y2']), node['box']):
                    errors.append(f'{edge["id"]}: connector crosses {node["id"]}; supply explicit via waypoints')
            for label in elements:
                if label['type'] == 'text' and label.get('text') and _segment_crosses_box(
                        (part['x1'], part['y1']), (part['x2'], part['y2']),
                        (label['x'], label['y'], label['w'], label['h'])):
                    errors.append(f'{edge["id"]}: connector crosses text {label.get("semantic_owner", label.get("id"))}; '
                                  'choose a side port or explicit via waypoints')
    w, h = plan['canvas']['width_in'], plan['canvas']['height_in']
    for element in elements:
        bounds = _bounds(element)
        if bounds and (not all(math.isfinite(v) for v in bounds) or
                       min(bounds[:2]) < -.01 or bounds[2] > w + .01 or bounds[3] > h + .01):
            errors.append(f'{element.get("id")}: rendered primitive leaves canvas')
    if plan['unknowns']:
        warnings.append('Unresolved scientific details remain; inspect the plan and visible disclosures.')
    warnings.append('Automatic marks/geometry checks do not certify scientific truth, aesthetics, or Office-host rendering.')
    return {'passed': not errors, 'errors': list(dict.fromkeys(errors)), 'warnings': warnings,
            'scientific_review': 'pending', 'visual_review': 'pending'}


def build(brief: dict, source_root: Path, output_dir: Path) -> dict:
    plan = plan_figure(brief, source_root)
    spec = compile_figure(plan)
    review = audit_figure(plan, spec)
    if not review['passed']:
        raise PlanError('Figure preflight failed: ' + '; '.join(review['errors']))
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {key: str(output_dir / f'{plan["id"]}{suffix}') for key, suffix in
             [('plan', '.plan.json'), ('spec', '.figure.json'), ('svg', '.svg'),
              ('pptx', '.pptx'), ('review', '.review.json')]}
    # Do not let a failed exporter replace the last coherent plan/artifact set.
    # Stage all bytes first; only successful rendering reaches publication.
    with TemporaryDirectory(prefix=f'.{plan["id"]}-', dir=output_dir) as temporary:
        staged = {key: Path(temporary) / Path(path).name for key, path in paths.items()}
        for key, data in [('plan', plan), ('spec', spec), ('review', review)]:
            staged[key].write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        render(spec, staged['svg'], staged['pptx'])
        for key in paths:
            staged[key].replace(paths[key])
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('brief', type=Path)
    parser.add_argument('--source-root', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    try:
        paths = build(json.loads(args.brief.read_text(encoding='utf-8')),
                      args.source_root or args.brief.resolve().parent, args.output_dir)
    except (PlanError, ValueError, OSError, json.JSONDecodeError) as error:
        parser.exit(2, f'Scientific figure build failed: {error}\n')
    print(json.dumps(paths, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
