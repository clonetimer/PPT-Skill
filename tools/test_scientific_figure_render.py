"""Render and mutation tests inspect marks, routes and native output."""
import copy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scientific_figure_plan import PlanError, plan_figure

try:
    from build_scientific_figure import audit_figure, compile_figure, build
except ImportError:
    audit_figure = compile_figure = build = None


class ScientificRenderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        source = self.root / 'source.txt'
        source.write_text('Synthetic: features -> 3-head attention -> features', encoding='utf-8')
        self.brief = {
            'schema_version': '1.0', 'id': 'synthetic_attention',
            'title': 'Synthetic graph attention', 'claim': 'Three parallel attention heads transform features.',
            'intent': 'reconstruct', 'medium': 'figure',
            'canvas': {'width_in': 11, 'height_in': 4},
            'evidence': [{'id': 's', 'path': 'source.txt', 'kind': 'synthetic',
                          'locator': 'line 1', 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}],
            'nodes': [
                {'id': 'x', 'kind': 'tensor', 'label': 'Input', 'params': {'shape': [12, 32]},
                 'box': [.4, 1, 2, 2], 'evidence': ['s']},
                {'id': 'gat', 'kind': 'graph_attention', 'label': 'Attention',
                 'params': {'heads': 3, 'merge': 'unknown', 'adjacency': 'unknown'},
                 'box': [3.3, 1, 3.8, 2], 'evidence': ['s']},
                {'id': 'y', 'kind': 'tensor', 'label': 'Output', 'params': {'shape': [12, 16]},
                 'box': [8.2, 1, 2, 2], 'evidence': ['s']},
            ],
            'edges': [{'id': 'in', 'source': 'x', 'target': 'gat', 'kind': 'data', 'evidence': ['s']},
                      {'id': 'out', 'source': 'gat', 'target': 'y', 'kind': 'data', 'evidence': ['s']}],
            'critical_edges': ['in', 'out'], 'unknowns': [],
        }

    def tearDown(self):
        self.tmp.cleanup()

    def compile(self):
        self.assertIsNotNone(compile_figure, 'Missing semantic-to-native compiler')
        plan = plan_figure(self.brief, self.root)
        return plan, compile_figure(plan)

    def test_three_heads_are_visible_not_just_metadata(self):
        plan, spec = self.compile()
        for head in range(3):
            marks = [e for e in spec['elements'] if e.get('semantic_owner') == 'gat'
                     and e.get('head_index') == head]
            self.assertTrue(any(e['type'] == 'ellipse' for e in marks))
            self.assertTrue(any(e['type'] == 'line' for e in marks))
        self.assertTrue(audit_figure(plan, spec)['passed'])

    def test_deleted_head_fails_even_with_unchanged_label_and_plan(self):
        plan, spec = self.compile()
        spec['elements'] = [e for e in spec['elements'] if not
                            (e.get('semantic_owner') == 'gat' and e.get('head_index') == 1)]
        result = audit_figure(plan, spec)
        self.assertFalse(result['passed'])
        self.assertTrue(any('head' in x.lower() for x in result['errors']))

    def test_deleting_neighborhood_arrows_preserves_wires_but_fails_audit(self):
        plan, spec = self.compile()
        spec['elements'] = [e for e in spec['elements'] if not
                            (e.get('visual_role') == 'attention_neighbor' and e['type'] == 'line')]
        self.assertFalse(audit_figure(plan, spec)['passed'])

    def test_corrupted_dimension_values_fail_audit(self):
        plan, spec = self.compile()
        for e in spec['elements']:
            if e.get('visual_role') == 'dimension' and e['type'] == 'text':
                e['text'] = '1 × 1'
        self.assertFalse(audit_figure(plan, spec)['passed'])

    def test_disconnected_attention_inputs_fail_audit(self):
        plan, spec = self.compile()
        spec['elements'] = [e for e in spec['elements'] if e.get('visual_role') != 'head_input']
        self.assertFalse(audit_figure(plan, spec)['passed'])

    def test_deleted_critical_connector_fails(self):
        plan, spec = self.compile()
        spec['elements'] = [e for e in spec['elements'] if e.get('edge_id') != 'out']
        self.assertFalse(audit_figure(plan, spec)['passed'])

    def test_misdirected_connector_fails(self):
        plan, spec = self.compile()
        edge = next(e for e in spec['elements'] if e.get('edge_id') == 'out')
        edge['x1'] += 1.5
        self.assertFalse(audit_figure(plan, spec)['passed'])

    def test_connector_crossing_text_is_detected_even_outside_other_nodes(self):
        plan, spec = self.compile()
        part = next(e for e in spec['elements'] if e.get('edge_id') == 'in')
        mx, my = (part['x1'] + part['x2']) / 2, (part['y1'] + part['y2']) / 2
        spec['elements'].append({'id': 'blocking_label', 'type': 'text', 'text': 'Scientific label',
                                 'x': mx - .1, 'y': my - .1, 'w': .2, 'h': .2})
        self.assertFalse(audit_figure(plan, spec)['passed'])

    def test_primitive_replacement_is_not_accepted_as_tensor(self):
        plan, spec = self.compile()
        spec['elements'] = [e for e in spec['elements'] if e.get('semantic_owner') != 'x']
        spec['elements'].append({'type': 'rect', 'semantic_owner': 'x',
                                 'x': .4, 'y': 1, 'w': 2, 'h': 2, 'fill': '#DDEEFF'})
        self.assertFalse(audit_figure(plan, spec)['passed'])

    def test_unknown_merge_is_visibly_disclosed(self):
        _, spec = self.compile()
        text = '\n'.join(e.get('text', '') for e in spec['elements'])
        self.assertTrue('融合未提供' in text or 'unknown' in text.lower())

    def test_non_native_routes_do_not_silently_render_boxes(self):
        self.brief['intent'] = 'conceptual'
        self.assertIsNotNone(compile_figure, 'Missing semantic-to-native compiler')
        with self.assertRaisesRegex(PlanError, 'imagegen|native'):
            compile_figure(plan_figure(self.brief, self.root))

    def test_add_needs_two_real_input_edges(self):
        self.brief['nodes'][1].update(kind='add', label='+', params={})
        self.assertIsNotNone(compile_figure, 'Missing semantic-to-native compiler')
        with self.assertRaisesRegex(PlanError, 'two|2|inputs'):
            compile_figure(plan_figure(self.brief, self.root))

    def test_add_operands_cannot_merge_before_the_addition_mark(self):
        self.brief['nodes'][1].update(kind='add', label='+', params={})
        self.brief['edges'][0]['target_port'] = 'left'
        self.brief['edges'][1].update(source='y', target='gat', target_port='input')
        with self.assertRaisesRegex(PlanError, 'distinct.*input|input.*distinct'):
            self.compile()
        self.brief['edges'][1]['target_port'] = 'bottom'
        _, spec = self.compile()
        endpoints = [(e['x2'], e['y2']) for e in spec['elements']
                     if e.get('edge_id') in {'in', 'out'} and e.get('arrow')]
        self.assertEqual(len(set(endpoints)), 2)

    def test_gate_control_cannot_share_the_data_input(self):
        self.brief['nodes'][1].update(kind='gate', label='Gate', params={'threshold': 'unknown'})
        self.brief['edges'][0]['target_port'] = 'left'
        self.brief['edges'][1].update(source='y', target='gat', kind='conditioning', target_port='input')
        with self.assertRaisesRegex(PlanError, 'control|conditioning'):
            self.compile()
        self.brief['edges'][1]['target_port'] = 'top'
        _, spec = self.compile()
        control = next(e for e in spec['elements'] if e.get('edge_id') == 'out' and e.get('arrow'))
        self.assertEqual((control['x2'], control['y2']), tuple(spec['node_geometry']['gat']['ports']['top']))

    def test_concat_declared_inputs_cannot_disagree_with_edges(self):
        self.brief['nodes'][1].update(kind='concat', label='Concat', params={'inputs': 4})
        self.assertIsNotNone(compile_figure, 'Missing semantic-to-native compiler')
        with self.assertRaisesRegex(PlanError, 'concat|inputs'):
            compile_figure(plan_figure(self.brief, self.root))

    def test_native_pptx_has_editable_text_and_no_bitmap(self):
        from pptx import Presentation
        from pptx.enum.shapes import MSO_SHAPE_TYPE
        self.assertIsNotNone(build, 'Missing build entry point')
        outputs = build(self.brief, self.root, self.root / 'result')
        slide = Presentation(outputs['pptx']).slides[0]
        text = '\n'.join(s.text for s in slide.shapes if s.has_text_frame)
        self.assertIn('Attention', text)
        self.assertIn('32', text)
        self.assertFalse(any(s.shape_type == MSO_SHAPE_TYPE.PICTURE for s in slide.shapes))
        self.assertGreater(sum(s.has_text_frame and bool(s.text) for s in slide.shapes), 5)
        self.assertTrue(Path(outputs['svg']).is_file())

    def test_dotted_ids_preserve_the_full_output_name(self):
        self.brief['id'] = 'trial.v1'
        outputs = build(self.brief, self.root, self.root / 'result')
        self.assertEqual(Path(outputs['pptx']).name, 'trial.v1.pptx')

    def test_wrapping_preserves_a_long_scientific_label(self):
        self.brief['nodes'][1]['label'] = '时序编码后的三个并行图注意力头保持各自的独立计算'
        self.brief['nodes'][1]['box'][3] = 2.5
        plan, spec = self.compile()
        self.assertTrue(audit_figure(plan, spec)['passed'])

    def test_all_bundled_examples_build(self):
        examples = Path(__file__).resolve().parents[1] / 'examples' / 'semantic_figures'
        for path in sorted(examples.glob('*.json')):
            with self.subTest(example=path.name):
                outputs = build(json.loads(path.read_text(encoding='utf-8')), examples, self.root / path.stem)
                self.assertTrue(Path(outputs['pptx']).is_file())

    def test_render_failure_preserves_previous_complete_output(self):
        outputs = build(self.brief, self.root, self.root / 'result')
        before = {key: Path(path).read_bytes() for key, path in outputs.items()}
        self.brief['title'] = 'New unrendered title'
        with patch('build_scientific_figure.render', side_effect=OSError('export interrupted')):
            with self.assertRaisesRegex(OSError, 'export interrupted'):
                build(self.brief, self.root, self.root / 'result')
        self.assertEqual(before, {key: Path(path).read_bytes() for key, path in outputs.items()})

    def test_first_failed_render_leaves_no_passing_artifacts(self):
        output = self.root / 'first_failure'
        with patch('build_scientific_figure.render', side_effect=OSError('export interrupted')):
            with self.assertRaises(OSError):
                build(self.brief, self.root, output)
        self.assertFalse(list(output.glob('*')) if output.exists() else [])


if __name__ == '__main__':
    unittest.main()
