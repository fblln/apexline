from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SmokeTests(unittest.TestCase):
    def test_summary_script_renders_existing_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_md = Path(tmpdir) / "lap-compliance.md"
            output_svg = Path(tmpdir) / "lap-compliance.svg"
            subprocess.run(
                [
                    "python3",
                    str(ROOT / "scripts" / "summarize_lap_diagnostics.py"),
                    "--year",
                    "2025",
                    "--diagnostics-json",
                    str(ROOT / "data" / "lap-diagnostics-2025.json"),
                    "--output-md",
                    str(output_md),
                    "--output-svg",
                    str(output_svg),
                ],
                check=True,
                cwd=ROOT,
            )
            self.assertTrue(output_md.exists())
            self.assertTrue(output_svg.exists())
            self.assertIn("2025 lap compliance summary", output_md.read_text(encoding="utf-8"))

    def test_fixture_demo_schema_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir)
            subprocess.run(
                ["python3", str(ROOT / "scripts" / "analyze_f1_circuit_gps.py"), "fixture-demo", "--output-dir", str(out)],
                check=True,
                cwd=ROOT,
            )
            subprocess.run(
                [
                    "python3",
                    str(ROOT / "scripts" / "analyze_f1_circuit_gps.py"),
                    "schema-check",
                    str(out / "circuit-analysis.json"),
                    str(out / "lap-diagnostics.json"),
                    str(out / "artifact-manifest.json"),
                ],
                check=True,
                cwd=ROOT,
            )
            subprocess.run(
                [
                    "python3",
                    str(ROOT / "scripts" / "summarize_lap_diagnostics.py"),
                    "--manifest",
                    str(out / "artifact-manifest.json"),
                    "--output-md",
                    str(out / "summary.md"),
                    "--output-svg",
                    str(out / "summary.svg"),
                ],
                check=True,
                cwd=ROOT,
            )
            self.assertTrue((out / "summary.md").exists())


if __name__ == "__main__":
    unittest.main()
