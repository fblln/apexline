from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from apexline.schemas import (
    validate_any_artifact,
    validate_circuit_analysis,
    validate_lap_diagnostics_season,
    validate_rejected_lap_gallery,
)


class SchemaTests(unittest.TestCase):
    def test_checked_in_circuit_analysis_validates(self) -> None:
        payload = json.loads((ROOT / "data/2025/all-events/r/circuit-analysis.json").read_text(encoding="utf-8"))
        validate_circuit_analysis(payload)

    def test_checked_in_lap_diagnostics_validates(self) -> None:
        payload = json.loads((ROOT / "data/2025/all-events/r/lap-diagnostics.json").read_text(encoding="utf-8"))
        validate_lap_diagnostics_season(payload)

    def test_checked_in_rejected_gallery_validates(self) -> None:
        payload = json.loads(
            (ROOT / "docs" / "assets" / "rejected-laps-2025" / "10-canadian-grand-prix.json").read_text(encoding="utf-8")
        )
        validate_rejected_lap_gallery(payload)

    def test_any_artifact_infers_versioned_payloads(self) -> None:
        payload = json.loads((ROOT / "data/2025/all-events/r/lap-diagnostics.json").read_text(encoding="utf-8"))
        validate_any_artifact(payload)


if __name__ == "__main__":
    unittest.main()
