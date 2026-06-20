from __future__ import annotations

import subprocess
import sys
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
                    sys.executable,
                    "-m",
                    "apexline.summarize",
                    "--year",
                    "2025",
                    "--diagnostics-json",
                    str(ROOT / "data/2025/all-events/r/lap-diagnostics.json"),
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
                [sys.executable, "-m", "apexline", "fixture-demo", "--output-dir", str(out)],
                check=True,
                cwd=ROOT,
            )
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "apexline",
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
                    sys.executable,
                    "-m",
                    "apexline.summarize",
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
