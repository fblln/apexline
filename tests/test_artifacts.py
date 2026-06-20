from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from apexline.artifacts import default_batch_dir, default_run_dir, normalize_session, session_slug, slugify
from apexline.plot_rejected_lap_galleries import relative_index_link


class ArtifactPathTests(unittest.TestCase):
    def test_slugify_event_and_session(self) -> None:
        self.assertEqual(slugify("Canadian Grand Prix"), "canadian-grand-prix")
        self.assertEqual(session_slug("Sprint Qualifying"), "sq")

    def test_normalize_session_aliases(self) -> None:
        self.assertEqual(normalize_session("race"), "R")
        self.assertEqual(normalize_session("practice-1"), "FP1")
        self.assertEqual(normalize_session("SQ"), "SQ")

    def test_default_single_session_output_path(self) -> None:
        self.assertEqual(
            default_run_dir(Path("data"), 2025, "Canadian Grand Prix", "R"),
            Path("data/2025/canadian-grand-prix/r"),
        )

    def test_default_batch_output_path(self) -> None:
        self.assertEqual(default_batch_dir(Path("data"), 2025, "Q"), Path("data/2025/all-events/q"))

    def test_gallery_link_is_relative_to_custom_index(self) -> None:
        root = Path(__file__).resolve().parents[1]
        index = root / "tmp" / "reports" / "index.md"
        gallery = root / "tmp" / "assets" / "event.svg"
        self.assertEqual(relative_index_link(gallery, index), "../assets/event.svg")


if __name__ == "__main__":
    unittest.main()
