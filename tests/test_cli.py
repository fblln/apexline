from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from apexline.cli import output_paths, parse_args


class CliTests(unittest.TestCase):
    def test_validate_subcommand_parses_single_session(self) -> None:
        args = parse_args(["validate", "--year", "2024", "--event", "Monaco", "--session", "Q"])
        self.assertEqual(args.command, "validate")
        self.assertEqual(args.year, 2024)
        self.assertEqual(args.event, "Monaco")
        self.assertEqual(args.session, "Q")

    def test_legacy_circuit_arg_maps_to_validate(self) -> None:
        args = parse_args(["--year", "2025", "--circuit", "Canada"])
        self.assertEqual(args.command, "validate")
        self.assertEqual(args.event, "Canada")

    def test_legacy_no_circuit_maps_to_batch(self) -> None:
        args = parse_args(["--year", "2025", "--limit", "1"])
        self.assertEqual(args.command, "batch")

    def test_validate_default_outputs_are_event_session_scoped(self) -> None:
        args = parse_args(["validate", "--year", "2025", "--event", "Canadian Grand Prix", "--session", "R"])
        paths = output_paths(args, event_name="Canadian Grand Prix")
        self.assertEqual(paths["lap_diagnostics_json"], Path("data/2025/canadian-grand-prix/r/lap-diagnostics.json"))
        self.assertEqual(paths["manifest_json"], Path("data/2025/canadian-grand-prix/r/artifact-manifest.json"))


if __name__ == "__main__":
    unittest.main()
