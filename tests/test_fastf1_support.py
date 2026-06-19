from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from apexline.fastf1_support import classify_lap, lap_key


class FastF1SupportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.reference_xy = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)]

    def test_lap_key_is_deterministic(self) -> None:
        self.assertEqual(
            lap_key(2025, 10, "Canadian Grand Prix", "R", "RUS", 63),
            "2025-10-canadian-grand-prix-r-rus-lap-63",
        )

    def test_lap_key_is_session_unique(self) -> None:
        race_key = lap_key(2025, 10, "Canadian Grand Prix", "R", "RUS", 1)
        qualifying_key = lap_key(2025, 10, "Canadian Grand Prix", "Q", "RUS", 1)
        self.assertNotEqual(race_key, qualifying_key)

    def test_classify_lap_flags_basic_rejections(self) -> None:
        diagnostic = classify_lap(
            driver="RUS",
            lap_number=13,
            lap_time_ms=None,
            is_accurate=False,
            is_pit_lap=True,
            points=[],
            reference_xy=self.reference_xy,
            validation_samples=120,
            validation_offset_step=4,
            length_tolerance_pct=0.05,
            rmse_threshold_m=25.0,
            p95_threshold_m=50.0,
            min_position_samples=4,
        )
        self.assertCountEqual(
            diagnostic.reasons,
            ["fastf1_inaccurate", "pit_lap", "missing_lap_time", "no_position_data"],
        )

    def test_classify_lap_flags_too_few_samples(self) -> None:
        diagnostic = classify_lap(
            driver="RUS",
            lap_number=1,
            lap_time_ms=74_000,
            is_accurate=True,
            is_pit_lap=False,
            points=[(0.0, 0.0), (100.0, 0.0), (100.0, 100.0)],
            reference_xy=self.reference_xy,
            validation_samples=120,
            validation_offset_step=4,
            length_tolerance_pct=0.05,
            rmse_threshold_m=25.0,
            p95_threshold_m=50.0,
            min_position_samples=4,
        )
        self.assertIn("too_few_position_samples", diagnostic.reasons)

    def test_classify_lap_flags_path_length_outlier(self) -> None:
        points = [(0.0, 0.0), (160.0, 0.0), (160.0, 160.0), (0.0, 160.0)]
        diagnostic = classify_lap(
            driver="RUS",
            lap_number=2,
            lap_time_ms=74_000,
            is_accurate=True,
            is_pit_lap=False,
            points=points,
            reference_xy=self.reference_xy,
            validation_samples=120,
            validation_offset_step=4,
            length_tolerance_pct=0.05,
            rmse_threshold_m=25.0,
            p95_threshold_m=50.0,
            min_position_samples=4,
        )
        self.assertIn("path_length_outlier", diagnostic.reasons)

    def test_classify_lap_normalizes_repeated_overlap_before_shape_fit(self) -> None:
        points = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0), (0.0, 0.0), (100.0, 0.0)]
        diagnostic = classify_lap(
            driver="RUS",
            lap_number=2,
            lap_time_ms=74_000,
            is_accurate=True,
            is_pit_lap=False,
            points=points,
            reference_xy=self.reference_xy,
            validation_samples=120,
            validation_offset_step=4,
            length_tolerance_pct=0.05,
            rmse_threshold_m=25.0,
            p95_threshold_m=50.0,
            min_position_samples=4,
        )
        self.assertNotIn("path_length_outlier", diagnostic.reasons)
        self.assertTrue(diagnostic.compliant)
        self.assertIsNotNone(diagnostic.fit)
        self.assertIsNotNone(diagnostic.normalization)
        self.assertAlmostEqual(diagnostic.path_length_m, 60.0)
        self.assertAlmostEqual(diagnostic.normalized_path_length_m or 0.0, 40.0)

    def test_classify_lap_flags_shape_thresholds(self) -> None:
        rectangle_points = [(0.0, 0.0), (125.0, 0.0), (125.0, 75.0), (0.0, 75.0)]
        diagnostic = classify_lap(
            driver="RUS",
            lap_number=3,
            lap_time_ms=74_000,
            is_accurate=True,
            is_pit_lap=False,
            points=rectangle_points,
            reference_xy=self.reference_xy,
            validation_samples=240,
            validation_offset_step=4,
            length_tolerance_pct=0.20,
            rmse_threshold_m=0.5,
            p95_threshold_m=0.5,
            min_position_samples=4,
        )
        self.assertIn("shape_rmse_over_threshold", diagnostic.reasons)
        self.assertIn("shape_p95_over_threshold", diagnostic.reasons)


if __name__ == "__main__":
    unittest.main()
