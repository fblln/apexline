from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from apexline.validation_summary import build_markdown, build_svg


class ValidationSummaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rows = [
            {
                "validation_complete": True,
                "round": 1,
                "event_name": "Alpha Grand Prix",
                "circuit_name": "Alpha Circuit",
                "declared_length_m": 5000,
                "repo_vs_fastf1": {"rmse_m": 5.0, "p95_m": 9.0},
                "repo_vs_fastf1_average": {"rmse_m": 4.0},
                "polyline_vs_source": {"simplified_points": 80, "encoded_chars": 240, "max_m": 0.8, "tolerance_m": 1.0, "source_length_m": 5000},
            },
            {
                "validation_complete": True,
                "round": 2,
                "event_name": "Beta Grand Prix",
                "circuit_name": "Beta Circuit",
                "declared_length_m": 4000,
                "repo_vs_fastf1": {"rmse_m": 7.0, "p95_m": 12.0},
                "repo_vs_fastf1_average": {"rmse_m": 8.0},
                "polyline_vs_source": {"simplified_points": 90, "encoded_chars": 180, "max_m": 0.9, "tolerance_m": 1.0, "source_length_m": 4000},
            },
        ]

    def test_build_markdown_contains_summary_sections(self) -> None:
        markdown = build_markdown(self.rows, 2025)
        self.assertIn("# 2025 Validation Summary", markdown)
        self.assertIn("| Circuits processed | 2 |", markdown)
        self.assertIn("## Biggest Deviations", markdown)
        self.assertIn("## Most Compact Oracle Polylines", markdown)

    def test_build_svg_contains_event_labels(self) -> None:
        svg = build_svg(self.rows, 2025)
        self.assertIn("2025 oracle-vs-FastF1 shape RMSE by circuit", svg)
        self.assertIn("01 Alpha GP", svg)
        self.assertIn("02 Beta GP", svg)


if __name__ == "__main__":
    unittest.main()
