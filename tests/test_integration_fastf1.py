from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from apexline.fastf1_support import score_fastf1_laps


@unittest.skipUnless(os.getenv("APEXLINE_RUN_INTEGRATION") == "1", "set APEXLINE_RUN_INTEGRATION=1 to run FastF1 integration tests")
class FastF1IntegrationTests(unittest.TestCase):
    def test_can_score_one_real_session(self) -> None:
        results = score_fastf1_laps(
            year=2025,
            event="Canadian Grand Prix",
            cache_dir=ROOT / "data" / "fastf1-cache",
            session_name="R",
            preferred_driver=None,
            reference_xy=[(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)],
            validation_samples=120,
            validation_offset_step=4,
            max_shape_candidates=2,
        )
        self.assertGreaterEqual(len(results), 1)


if __name__ == "__main__":
    unittest.main()
