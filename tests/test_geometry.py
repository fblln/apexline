from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from apexline.geometry import rdp, resample_closed, validate_shape


class GeometryTests(unittest.TestCase):
    def test_resample_closed_hits_square_corners(self) -> None:
        points = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        sampled = resample_closed(points, 4)
        self.assertEqual(len(sampled), 4)
        self.assertAlmostEqual(sampled[0][0], 0.0)
        self.assertAlmostEqual(sampled[0][1], 0.0)
        self.assertAlmostEqual(sampled[1][0], 10.0)
        self.assertAlmostEqual(sampled[1][1], 0.0)
        self.assertAlmostEqual(sampled[2][0], 10.0)
        self.assertAlmostEqual(sampled[2][1], 10.0)
        self.assertAlmostEqual(sampled[3][0], 0.0)
        self.assertAlmostEqual(sampled[3][1], 10.0)

    def test_rdp_reduces_nearly_straight_line(self) -> None:
        points = [(0.0, 0.0), (1.0, 0.02), (2.0, -0.02), (3.0, 0.01), (4.0, 0.0)]
        simplified = rdp(points, tolerance_m=0.1)
        self.assertEqual(simplified, [(0.0, 0.0), (4.0, 0.0)])

    def test_validate_shape_handles_rotation_and_scale(self) -> None:
        source = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
        angle = math.radians(30.0)
        scale = 0.1
        target = []
        for x, y in source:
            xr = x * math.cos(angle) - y * math.sin(angle)
            yr = x * math.sin(angle) + y * math.cos(angle)
            target.append((xr * scale + 12.5, yr * scale - 4.0))

        fit = validate_shape(source, target, sample_count=120, offset_step=4)
        self.assertLess(fit.rmse_m, 1e-6)
        self.assertAlmostEqual(fit.scale_m_per_fastf1_unit, 0.1, places=6)


if __name__ == "__main__":
    unittest.main()
