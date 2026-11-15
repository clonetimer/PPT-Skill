"""Tests for optional visual proposals and conservative SourceLayout evidence fusion."""
from __future__ import annotations

import unittest

from source_layout_vision import (
    fuse_visual_evidence,
    map_raster_bbox_to_pdf,
    normalize_layout_detections,
    normalize_ocr_detections,
)


REGION = [200.0, 100.0, 700.0, 350.0]


class RasterCoordinateTests(unittest.TestCase):
    def test_map_raster_bbox_uses_actual_raster_dimensions(self):
        bbox = map_raster_bbox_to_pdf(
            [100, 50, 500, 250],
            raster_size=(1000, 500),
            figure_region_pt=REGION,
        )
        self.assertEqual(bbox, [250.0, 125.0, 450.0, 225.0])

    def test_map_raster_bbox_does_not_assume_nominal_dpi(self):
        bbox = map_raster_bbox_to_pdf(
            [100, 50, 500, 250],
            raster_size=(1001, 501),
            figure_region_pt=REGION,
        )
        self.assertAlmostEqual(bbox[0], 200 + 500 * 100 / 1001, places=3)
        self.assertAlmostEqual(bbox[1], 100 + 250 * 50 / 501, places=3)

    def test_map_raster_bbox_rejects_nonfinite_or_out_of_bounds_coordinates(self):
        for bbox in ([float("nan"), 0, 20, 20], [-1, 0, 20, 20], [0, 0, 1001, 20]):
            with self.subTest(bbox=bbox):
                with self.assertRaisesRegex(ValueError, "INVALID_RASTER_BBOX"):
                    map_raster_bbox_to_pdf(bbox, (1000, 500), REGION)


class LayoutDetectionNormalizationTests(unittest.TestCase):
    def test_layout_detections_map_to_pdf_and_filter_nonvisual_classes(self):
        raw = {
            "res": {
                "boxes": [
                    {"label": "figure", "score": 0.96, "coordinate": [10, 20, 400, 300]},
                    {"label": "image", "score": 0.91, "coordinate": [30, 40, 180, 220]},
                    {"label": "text", "score": 0.99, "coordinate": [5, 5, 450, 30]},
                ]
            }
        }
        candidates = normalize_layout_detections(raw, (500, 350), REGION)
        self.assertEqual([item["model_label"] for item in candidates], ["figure", "image"])
        self.assertEqual(candidates[0]["bbox_pt"], [210.0, 114.286, 600.0, 314.286])
        self.assertTrue(all(item["needs_human_review"] for item in candidates))

    def test_duplicate_same_class_boxes_are_merged_but_nested_boxes_remain(self):
        raw = {
            "res": {
                "boxes": [
                    {"label": "figure", "score": 0.80, "coordinate": [10, 10, 400, 300]},
                    {"label": "figure", "score": 0.96, "coordinate": [10, 10, 400, 300]},
                    {"label": "image", "score": 0.92, "coordinate": [30, 30, 150, 180]},
                ]
            }
        }
        candidates = normalize_layout_detections(raw, (500, 350), REGION)
        self.assertEqual(len(candidates), 2)
        figure = next(item for item in candidates if item["model_label"] == "figure")
        self.assertEqual(figure["model_score"], 0.96)


class OCRPanelMarkerTests(unittest.TestCase):
    def test_ocr_parser_accepts_parenthesized_and_punctuated_panel_labels(self):
        raw = {
            "res": {
                "rec_texts": ["(a)", "b)", "C."],
                "rec_scores": [0.98, 0.94, 0.96],
                "dt_polys": [
                    [[10, 10], [30, 10], [30, 28], [10, 28]],
                    [[50, 10], [68, 10], [68, 28], [50, 28]],
                    [[90, 10], [110, 10], [110, 28], [90, 28]],
                ],
            }
        }
        markers = normalize_ocr_detections(raw, (500, 350), REGION)
        self.assertEqual([item["label"] for item in markers], ["a", "b", "c"])
        self.assertEqual([item["marker_style"] for item in markers],
                         ["parenthesized", "punctuated", "punctuated"])

    def test_ocr_parser_rejects_words_and_numeric_axis_ticks(self):
        raw = {
            "res": {
                "rec_texts": ["accuracy", "x-axis", "0.25", "loss"],
                "rec_scores": [0.99, 0.99, 0.99, 0.98],
                "dt_polys": [
                    [[10, 10], [90, 10], [90, 28], [10, 28]],
                    [[100, 10], [160, 10], [160, 28], [100, 28]],
                    [[170, 10], [210, 10], [210, 28], [170, 28]],
                    [[220, 10], [270, 10], [270, 28], [220, 28]],
                ],
            }
        }
        self.assertEqual(normalize_ocr_detections(raw, (500, 350), REGION), [])

    def test_bare_single_letter_is_only_a_low_confidence_marker_candidate(self):
        raw = {
            "res": {
                "rec_texts": ["a"],
                "rec_scores": [0.91],
                "dt_polys": [[[10, 10], [22, 10], [22, 24], [10, 24]]],
            }
        }
        markers = normalize_ocr_detections(raw, (500, 350), REGION)
        self.assertEqual(len(markers), 1)
        self.assertEqual(markers[0]["marker_style"], "bare")
        self.assertEqual(markers[0]["confidence"], "low")


class EvidenceFusionTests(unittest.TestCase):
    def _inputs(self):
        regions = [
            {
                "id": "visual_region_001", "candidate_type": "visual_region",
                "model_label": "figure", "model_score": 0.96,
                "bbox_pt": [0.0, 0.0, 200.0, 200.0],
                "bbox_normalized": [0.0, 0.0, 1.0, 1.0],
                "needs_human_review": True,
            },
            {
                "id": "visual_region_002", "candidate_type": "visual_region",
                "model_label": "image", "model_score": 0.92,
                "bbox_pt": [20.0, 20.0, 100.0, 100.0],
                "bbox_normalized": [0.1, 0.1, 0.4, 0.4],
                "needs_human_review": True,
            },
            {
                "id": "visual_region_003", "candidate_type": "visual_region",
                "model_label": "image", "model_score": 0.93,
                "bbox_pt": [110.0, 20.0, 190.0, 100.0],
                "bbox_normalized": [0.55, 0.1, 0.4, 0.4],
                "needs_human_review": True,
            },
            {
                "id": "visual_region_004", "candidate_type": "visual_region",
                "model_label": "table", "model_score": 0.90,
                "bbox_pt": [40.0, 110.0, 100.0, 170.0],
                "bbox_normalized": [0.2, 0.55, 0.3, 0.3],
                "needs_human_review": True,
            },
            {
                "id": "visual_region_005", "candidate_type": "visual_region",
                "model_label": "algorithm", "model_score": 0.89,
                "bbox_pt": [60.0, 110.0, 120.0, 170.0],
                "bbox_normalized": [0.3, 0.55, 0.3, 0.3],
                "needs_human_review": True,
            },
        ]
        markers = [
            {
                "id": "ocr_marker_001", "label": "a", "text": "(a)",
                "marker_style": "parenthesized", "ocr_score": 0.98,
                "bbox_pt": [24.0, 24.0, 34.0, 34.0],
                "bbox_normalized": [0.12, 0.12, 0.05, 0.05],
                "confidence": "high",
            },
            {
                "id": "ocr_marker_002", "label": "b", "text": "(b)",
                "marker_style": "parenthesized", "ocr_score": 0.97,
                "bbox_pt": [114.0, 24.0, 124.0, 34.0],
                "bbox_normalized": [0.57, 0.12, 0.05, 0.05],
                "confidence": "high",
            },
            {
                "id": "ocr_marker_003", "label": "x", "text": "x",
                "marker_style": "bare", "ocr_score": 0.91,
                "bbox_pt": [90.0, 170.0, 98.0, 178.0],
                "bbox_normalized": [0.45, 0.85, 0.04, 0.04],
                "confidence": "low",
            },
        ]
        elements = [
            {"id": "draw_inside_a", "kind": "stroke_path", "source_order": 5,
             "bbox_pt": [30.0, 45.0, 80.0, 85.0]},
            {"id": "draw_inside_b", "kind": "filled_path", "source_order": 6,
             "bbox_pt": [120.0, 45.0, 180.0, 85.0]},
            {"id": "draw_crossing", "kind": "stroke_path", "source_order": 7,
             "bbox_pt": [90.0, 45.0, 130.0, 60.0]},
            {"id": "draw_ambiguous", "kind": "stroke_path", "source_order": 8,
             "bbox_pt": [70.0, 120.0, 90.0, 160.0]},
            {"id": "draw_unassigned", "kind": "stroke_path", "source_order": 9,
             "bbox_pt": [205.0, 205.0, 215.0, 215.0]},
        ]
        images = [
            {"id": "image_xref_9", "kind": "image", "source_order": 3,
             "bbox_pt": [25.0, 35.0, 90.0, 90.0]},
        ]
        return regions, markers, elements, images

    def test_nested_regions_receive_smallest_containing_parent(self):
        regions, markers, elements, images = self._inputs()
        result = fuse_visual_evidence(regions, markers, elements, images, [0, 0, 200, 200])
        by_id = {item["id"]: item for item in result["visual_region_candidates"]}
        self.assertIsNone(by_id["visual_region_001"]["parent_candidate_id"])
        self.assertEqual(by_id["visual_region_002"]["parent_candidate_id"], "visual_region_001")
        self.assertEqual(by_id["visual_region_003"]["parent_candidate_id"], "visual_region_001")
        self.assertEqual(by_id["visual_region_002"]["depth"], 1)

    def test_ocr_panel_markers_anchor_only_to_top_left_of_smallest_region(self):
        regions, markers, elements, images = self._inputs()
        result = fuse_visual_evidence(regions, markers, elements, images, [0, 0, 200, 200])
        hypotheses = result["panel_hypotheses"]
        self.assertEqual([item["label"] for item in hypotheses], ["a", "b"])
        self.assertEqual(
            [item["region_candidate_id"] for item in hypotheses],
            ["visual_region_002", "visual_region_003"],
        )
        unresolved = {item["id"]: item for item in result["ocr_panel_markers"]}
        self.assertEqual(unresolved["ocr_marker_003"]["anchor_status"], "UNRESOLVED")

    def test_source_objects_are_assigned_to_deepest_region_or_unresolved_when_ambiguous(self):
        regions, markers, elements, images = self._inputs()
        result = fuse_visual_evidence(regions, markers, elements, images, [0, 0, 200, 200])
        ownership = {item["source_object_id"]: item for item in result["source_object_ownership"]}
        self.assertEqual(ownership["draw_inside_a"]["candidate_id"], "visual_region_002")
        self.assertEqual(ownership["draw_inside_b"]["candidate_id"], "visual_region_003")
        self.assertEqual(ownership["image_xref_9"]["candidate_id"], "visual_region_002")
        self.assertEqual(ownership["draw_crossing"]["candidate_id"], "visual_region_001")
        self.assertEqual(ownership["draw_crossing"]["ownership_scope"], "container")
        self.assertEqual(ownership["draw_ambiguous"]["status"], "UNRESOLVED")
        self.assertEqual(ownership["draw_unassigned"]["status"], "UNRESOLVED")
        self.assertTrue(all(item["source_order"] is not None for item in ownership.values()
                            if item["status"] in ("ASSIGNED", "CONTAINER_ONLY")))

    def test_sibling_regions_create_review_only_horizontal_alignment_group(self):
        regions, markers, elements, images = self._inputs()
        result = fuse_visual_evidence(regions, markers, elements, images, [0, 0, 200, 200])
        groups = result["visual_alignment_groups"]
        horizontal = [item for item in groups if item["axis"] == "horizontal_row"]
        self.assertEqual(len(horizontal), 1)
        self.assertEqual(horizontal[0]["member_candidate_ids"],
                         ["visual_region_002", "visual_region_003"])
        self.assertTrue(horizontal[0]["needs_human_review"])


if __name__ == "__main__":
    unittest.main()
