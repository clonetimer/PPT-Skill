"""Behavior checks for evidence-grounded scientific figure planning."""
from pathlib import Path
from tempfile import TemporaryDirectory
import copy
import hashlib
import unittest

try:
    from scientific_figure_plan import PlanError, plan_figure
except ImportError:
    PlanError = ValueError
    plan_figure = None


class FigurePlanningTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        source = self.root / 'evidence.txt'
        source.write_text('Two-head graph attention maps 12 x 32 to 12 x 16.', encoding='utf-8')
        self.brief = {
            'schema_version': '1.0', 'id': 'case', 'title': 'Satellite diagnosis',
            'claim': 'An evidenced encoder transforms node features.',
            'intent': 'reconstruct', 'medium': 'figure',
            'canvas': {'width_in': 10, 'height_in': 4},
            'evidence': [{'id': 's1', 'path': 'evidence.txt',
                          'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                          'locator': 'line 1', 'kind': 'user_brief'}],
            'nodes': [
                {'id': 'x', 'kind': 'tensor', 'label': 'Input', 'evidence': ['s1'],
                 'params': {'shape': [12, 32]}, 'box': [.3, 1, 2, 2]},
                {'id': 'a', 'kind': 'graph_attention', 'label': 'Graph attention',
                 'evidence': ['s1'], 'params': {'heads': 2, 'merge': 'unknown',
                 'adjacency': 'unknown'}, 'box': [3, 1, 3, 2]},
                {'id': 'y', 'kind': 'tensor', 'label': 'Output', 'evidence': ['s1'],
                 'params': {'shape': [12, 16]}, 'box': [7, 1, 2, 2]},
            ],
            'edges': [
                {'id': 'e1', 'source': 'x', 'target': 'a', 'evidence': ['s1'], 'kind': 'data'},
                {'id': 'e2', 'source': 'a', 'target': 'y', 'evidence': ['s1'], 'kind': 'data'},
            ],
            'critical_edges': ['e1', 'e2'], 'unknowns': ['Exact graph adjacency is unavailable.'],
        }

    def tearDown(self):
        self.tmp.cleanup()

    def plan(self, brief=None):
        self.assertIsNotNone(plan_figure, 'Missing runnable scientific figure planner')
        return plan_figure(brief or self.brief, self.root)

    def test_satellite_domain_cannot_override_graph_attention_grammar(self):
        original = copy.deepcopy(self.brief)
        plan = self.plan()
        self.assertEqual(plan['route']['renderer'], 'native')
        self.assertEqual(plan['route']['profile'], 'scientific_semantic')
        self.assertEqual(plan['nodes'][1]['glyph'], 'attention_heads')
        self.assertEqual(plan['nodes'][0]['glyph'], 'tensor_planes')
        self.assertEqual(self.brief, original)

    def test_unknown_science_remains_unknown(self):
        plan = self.plan()
        self.assertEqual(plan['nodes'][1]['params']['merge'], 'unknown')
        self.assertNotIn('graph_edges', plan['nodes'][1]['params'])
        self.assertTrue(any('adjacency' in x.lower() for x in plan['unknowns']))

    def test_changed_source_is_rejected(self):
        (self.root / 'evidence.txt').write_text('Different experiment', encoding='utf-8')
        with self.assertRaisesRegex(PlanError, 'hash|SHA'):
            self.plan()

    def test_unknown_source_reference_is_rejected(self):
        self.brief['nodes'][1]['evidence'] = ['missing']
        with self.assertRaisesRegex(PlanError, 'evidence'):
            self.plan()

    def test_unknown_kind_is_not_silently_a_box(self):
        self.brief['nodes'][1]['kind'] = 'quantum_hypergraph'
        with self.assertRaisesRegex(PlanError, 'Unsupported|unsupported'):
            self.plan()

    def test_generic_box_override_of_attention_is_rejected(self):
        self.brief['nodes'][1]['glyph'] = 'process_box'
        with self.assertRaisesRegex(PlanError, 'glyph'):
            self.plan()

    def test_missing_source_critical_route_is_rejected(self):
        self.brief['edges'].pop()
        with self.assertRaisesRegex(PlanError, 'critical'):
            self.plan()

    def test_empty_critical_routes_cannot_validate_method(self):
        self.brief['critical_edges'] = []
        with self.assertRaisesRegex(PlanError, 'critical'):
            self.plan()

    def test_broken_edge_endpoint_is_rejected(self):
        self.brief['edges'][0]['target'] = 'missing'
        with self.assertRaisesRegex(PlanError, 'endpoint'):
            self.plan()

    def test_opaque_evidenced_component_is_allowed(self):
        self.brief['nodes'][1].update(kind='process', params={'opaque': True,
            'explanation': 'The supplied source names this module but omits internals.'})
        self.assertEqual(self.plan()['nodes'][1]['glyph'], 'process_box')

    def test_arbitrary_process_box_needs_evidence_boundary(self):
        self.brief['nodes'][1].update(kind='process', params={})
        with self.assertRaisesRegex(PlanError, 'opaque'):
            self.plan()

    def test_redraw_requires_visual_source_and_anchors(self):
        self.brief['intent'] = 'redraw'
        with self.assertRaisesRegex(PlanError, 'reference_image'):
            self.plan()
        self.make_visual_evidence()
        self.brief['source_anchors'] = ['two towers', 'parallel heads', 'thin arrows']
        self.assertEqual(self.plan()['route']['profile'], 'source_matched')
        self.assertEqual(self.plan()['route']['renderer'], 'source_spec')

    def make_visual_evidence(self):
        from PIL import Image
        path = self.root / 'reference.png'
        Image.new('RGB', (20, 20), 'white').save(path)
        self.brief['evidence'][0].update(kind='reference_image', path=path.name,
            sha256=hashlib.sha256(path.read_bytes()).hexdigest())

    def test_text_file_cannot_masquerade_as_source_artwork(self):
        self.brief['intent'] = 'redraw'
        self.brief['evidence'][0]['kind'] = 'reference_image'
        self.brief['source_anchors'] = ['two towers', 'parallel heads', 'thin arrows']
        with self.assertRaisesRegex(PlanError, 'image|visual'):
            self.plan()

    def test_duplicate_source_anchors_are_rejected(self):
        self.brief['intent'] = 'redraw'
        self.make_visual_evidence()
        self.brief['source_anchors'] = ['same anchor'] * 3
        with self.assertRaisesRegex(PlanError, 'distinct|anchors'):
            self.plan()

    def test_malformed_json_fields_have_field_specific_errors(self):
        cases = [('intent', []), ('medium', []), ('style', []), ('panels', [{}])]
        for key, value in cases:
            with self.subTest(field=key):
                brief = copy.deepcopy(self.brief)
                brief[key] = value
                with self.assertRaisesRegex(PlanError, key):
                    self.plan(brief)
        for collection, field in [('nodes', 'kind'), ('evidence', 'kind'), ('edges', 'source')]:
            with self.subTest(field=f'{collection}.{field}'):
                brief = copy.deepcopy(self.brief)
                brief[collection][0][field] = []
                with self.assertRaises(PlanError):
                    self.plan(brief)
        for field in ('merge', 'adjacency'):
            with self.subTest(field=f'attention.{field}'):
                brief = copy.deepcopy(self.brief)
                brief['nodes'][1]['params'][field] = []
                with self.assertRaisesRegex(PlanError, field):
                    self.plan(brief)

    def test_native_canvas_limits_are_checked_before_export(self):
        self.brief['canvas']['width_in'] = 60
        with self.assertRaisesRegex(PlanError, 'canvas'):
            self.plan()

    def test_concept_art_and_workflow_take_different_routes(self):
        self.brief['intent'] = 'conceptual'
        self.assertEqual(self.plan()['route']['renderer'], 'imagegen')
        self.brief['intent'] = 'workflow'
        self.brief['nodes'][1].update(kind='process', params={})
        self.assertEqual(self.plan()['route']['profile'], 'engineering_flow')

    def test_invalid_head_counts_and_fabricated_adjacency_are_rejected(self):
        self.brief['nodes'][1]['params']['heads'] = True
        with self.assertRaisesRegex(PlanError, 'heads'):
            self.plan()
        self.brief['nodes'][1]['params']['heads'] = 3
        self.brief['nodes'][1]['params']['graph_edges'] = [[0, 1]]
        with self.assertRaisesRegex(PlanError, 'adjacency'):
            self.plan()

    def test_nonfinite_and_out_of_canvas_geometry_are_rejected(self):
        self.brief['nodes'][1]['box'][0] = float('nan')
        with self.assertRaisesRegex(PlanError, 'box'):
            self.plan()
        self.brief['nodes'][1]['box'][0] = 9
        with self.assertRaisesRegex(PlanError, 'canvas'):
            self.plan()


if __name__ == '__main__':
    unittest.main()
