#!/usr/bin/env python3
"""Generate real Canada 2025 lap-diagnostic SVGs from FastF1 positions.

The script intentionally emits SVG directly instead of relying on a plotting
library. That keeps the diagnostic figures reproducible in sandboxes and CI.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from . import analyze_f1_circuit_gps as analyzer
from .geometry import normalize_repeated_lap_segment


PROJECT_DIR = Path.cwd()


XY = tuple[float, float]


def load_session(year: int, event: str, cache_dir: Path) -> Any:
    import fastf1  # type: ignore[import-not-found]

    cache_dir.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(str(cache_dir))
    session = fastf1.get_session(year, event, "R")
    session.load(laps=True, telemetry=True, weather=False, messages=False)
    return session


def find_lap(session: Any, driver: str, lap_number: int) -> Any:
    for _, lap in session.laps.pick_drivers(driver).iterlaps():
        if int(lap.get("LapNumber")) == lap_number:
            return lap
    raise ValueError(f"Could not find {driver} lap {lap_number}")


def lap_transform(points: list[XY], gps_xy: list[XY], sample_count: int = 720) -> tuple[complex, complex, analyzer.FitStats]:
    """Learn one similarity transform from a clean reference lap."""

    fit = analyzer.validate_shape(
        fastf1_xy=points,
        gps_xy=gps_xy,
        sample_count=sample_count,
        offset_step=1,
    )
    source = analyzer.resample_closed(points, sample_count)
    target = analyzer.resample_closed(gps_xy, sample_count)
    target_for_fit = list(reversed(target)) if fit.direction == "reversed" else target
    target_for_fit = analyzer.rotate_samples(target_for_fit, fit.start_offset_samples)

    source_complex = [complex(x, y) for x, y in source]
    target_complex = [complex(x, y) for x, y in target_for_fit]
    source_mean = sum(source_complex) / len(source_complex)
    target_mean = sum(target_complex) / len(target_complex)
    centered_source = [point - source_mean for point in source_complex]
    centered_target = [point - target_mean for point in target_complex]
    c = sum(t * s.conjugate() for s, t in zip(centered_source, centered_target)) / sum(
        abs(point) ** 2 for point in centered_source
    )
    translation = target_mean - c * source_mean
    return c, translation, fit


def apply_transform(points: list[XY], scale_rotate: complex, translation: complex) -> list[XY]:
    raw_complex = [complex(x, y) for x, y in points]
    transformed = [scale_rotate * point + translation for point in raw_complex]
    return [(point.real, point.imag) for point in transformed]


def format_ms(ms: int | None) -> str:
    if ms is None:
        return "missing"
    return f"{ms / 1000:.3f}s"


def bbox(points: list[XY]) -> tuple[float, float, float, float]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def merged_bbox(lines: list[list[XY]]) -> tuple[float, float, float, float]:
    boxes = [bbox(line) for line in lines]
    return (
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    )


def project(
    point: XY,
    box: tuple[float, float, float, float],
    panel_x: float,
    panel_y: float,
    panel_w: float,
    panel_h: float,
    pad: float,
) -> XY:
    min_x, min_y, max_x, max_y = box
    width = max(max_x - min_x, 1.0)
    height = max(max_y - min_y, 1.0)
    scale = min((panel_w - pad * 2) / width, (panel_h - pad * 2) / height)
    used_w = width * scale
    used_h = height * scale
    offset_x = panel_x + (panel_w - used_w) / 2
    offset_y = panel_y + (panel_h - used_h) / 2
    x = offset_x + (point[0] - min_x) * scale
    y = offset_y + used_h - (point[1] - min_y) * scale
    return x, y


def polyline_svg(
    points: list[XY],
    box: tuple[float, float, float, float],
    panel_x: float,
    panel_y: float,
    panel_w: float,
    panel_h: float,
    *,
    stroke: str,
    width: float,
    opacity: float = 1.0,
) -> str:
    projected = [project(point, box, panel_x, panel_y, panel_w, panel_h, 18) for point in points]
    coords = " ".join(f"{x:.1f},{y:.1f}" for x, y in projected)
    return (
        f'<polyline points="{coords}" fill="none" stroke="{stroke}" '
        f'stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round" opacity="{opacity}"/>'
    )


def text_svg(x: float, y: float, text: str, *, size: int = 14, weight: int = 400, fill: str = "#111827") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Inter, Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}">{escape(text)}</text>'
    )


def text_lines_svg(
    x: float,
    y: float,
    lines: list[str],
    *,
    size: int = 14,
    weight: int = 400,
    fill: str = "#111827",
    line_gap: int | None = None,
) -> list[str]:
    gap = line_gap or (size + 5)
    return [text_svg(x, y + index * gap, line, size=size, weight=weight, fill=fill) for index, line in enumerate(lines)]


def draw_lap_examples(
    *,
    session: Any,
    gps_xy: list[XY],
    output: Path,
) -> None:
    reference_length = analyzer.path_length(gps_xy)
    examples = [
        {
            "title": "Fastest valid lap",
            "subtitle_lines": ["RUS lap 63, race fastest lap"],
            "driver": "RUS",
            "lap": 63,
            "reason": "compliant",
            "color": "#059669",
            "repair_lines": None,
        },
        {
            "title": "Boundary seam repaired",
            "subtitle_lines": ["VER lap 2, recovered to one clean", "loop before shape fit"],
            "driver": "VER",
            "lap": 2,
            "reason": "compliant after seam repair",
            "color": "#2563eb",
            "repair_lines": [],
        },
        {
            "title": "Pit/inaccurate lap",
            "subtitle_lines": ["RUS lap 13, projected with clean-lap transform"],
            "driver": "RUS",
            "lap": 13,
            "reason": "pit_lap + fastf1_inaccurate",
            "color": "#f97316",
            "repair_lines": None,
        },
    ]
    anchor_lap = find_lap(session, "RUS", 63)
    anchor_points = analyzer.lap_position_points(anchor_lap)
    anchor_scale_rotate, anchor_translation, anchor_fit = lap_transform(anchor_points, gps_xy)

    width = 1500
    height = 650
    panel_w = 448
    panel_h = 500
    panel_y = 92
    gap = 26
    left = 26
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        text_svg(28, 42, "Canada 2025: FastF1 traces vs the oracle circuit line", size=24, weight=700),
        text_svg(28, 68, "Gray is the oracle GPS line. Color is a FastF1 lap projected with one clean RUS lap 63 transform.", size=14, fill="#475569"),
    ]

    for index, example in enumerate(examples):
        panel_x = left + index * (panel_w + gap)
        lap = find_lap(session, example["driver"], example["lap"])
        points = analyzer.lap_position_points(lap)
        raw_path_length_m = analyzer.path_length(analyzer.closed_path(points)) * 0.1
        display_points = points
        display_path_length_m = raw_path_length_m
        fit = None
        if example["repair_lines"] is not None:
            normalized = normalize_repeated_lap_segment(
                points,
                target_length_m=reference_length,
                length_tolerance_pct=0.05,
                min_points=100,
            )
            if normalized is not None:
                display_points, normalization = normalized
                display_path_length_m = normalization.normalized_path_length_m
                fit = analyzer.validate_shape(display_points, gps_xy, sample_count=240, offset_step=8)
                example["repair_lines"] = [
                    f"raw {raw_path_length_m:.1f} m -> {display_path_length_m:.1f} m after seam trim",
                    f"fit RMSE {fit.rmse_m:.1f} m",
                ]
        elif example["reason"] == "compliant":
            fit = anchor_fit
        transformed = apply_transform(display_points, anchor_scale_rotate, anchor_translation)
        length_error_m = display_path_length_m - reference_length
        length_error_pct = length_error_m / reference_length * 100
        lap_time_ms = analyzer.value_to_ms(lap.get("LapTime"))
        box = merged_bbox([gps_xy, transformed])
        fit_text = "shape fit: skipped after pre-fit rejection"
        if fit is not None:
            fit_text = f"fit: RMSE {fit.rmse_m:.1f} m, p95 {fit.p95_m:.1f} m"

        parts.extend(
            [
                f'<rect x="{panel_x}" y="{panel_y}" width="{panel_w}" height="{panel_h}" rx="10" fill="#ffffff" stroke="#cbd5e1"/>',
                text_svg(panel_x + 20, panel_y + 34, example["title"], size=17, weight=700),
            ]
        )
        parts.extend(text_lines_svg(panel_x + 20, panel_y + 56, example["subtitle_lines"], size=13, fill="#475569", line_gap=16))
        parts.extend(
            [
                polyline_svg(gps_xy, box, panel_x + 18, panel_y + 96, panel_w - 36, 264, stroke="#94a3b8", width=3.0, opacity=0.85),
                polyline_svg(transformed, box, panel_x + 18, panel_y + 96, panel_w - 36, 264, stroke=example["color"], width=3.2, opacity=0.95),
            ]
        )

        start = project(transformed[0], box, panel_x + 18, panel_y + 96, panel_w - 36, 264, 18)
        end = project(transformed[-1], box, panel_x + 18, panel_y + 96, panel_w - 36, 264, 18)
        parts.extend(
            [
                f'<circle cx="{start[0]:.1f}" cy="{start[1]:.1f}" r="4.5" fill="#111827"/>',
                f'<circle cx="{end[0]:.1f}" cy="{end[1]:.1f}" r="4.5" fill="#64748b"/>',
                text_svg(panel_x + 20, panel_y + 392, f"time: {format_ms(lap_time_ms)}", size=13),
                text_svg(panel_x + 20, panel_y + 416, f"length: {display_path_length_m:.1f} m ({length_error_pct:+.1f}%)", size=13),
                text_svg(panel_x + 20, panel_y + 440, fit_text, size=13),
                text_svg(panel_x + 20, panel_y + 464, f"reason: {example['reason']}", size=13, fill=example["color"]),
            ]
        )
        if example["repair_lines"] is not None:
            parts.extend(text_lines_svg(panel_x + 20, panel_y + 488, example["repair_lines"], size=12, fill="#475569", line_gap=15))

    parts.extend(
        [
            '<line x1="586" y1="622" x2="636" y2="622" stroke="#94a3b8" stroke-width="4" stroke-linecap="round"/>',
            text_svg(646, 627, "repo GPS", size=13, fill="#475569"),
            '<line x1="742" y1="622" x2="792" y2="622" stroke="#059669" stroke-width="4" stroke-linecap="round"/>',
            text_svg(802, 627, "FastF1 trace", size=13, fill="#475569"),
            "</svg>",
        ]
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--event", default="Canadian Grand Prix")
    parser.add_argument("--circuit-id", default="ca-1978")
    parser.add_argument("--fastf1-cache-dir", type=Path, default=PROJECT_DIR / "data" / "fastf1-cache")
    parser.add_argument("--circuits-repo", type=Path, default=Path("/tmp/f1-circuits"))
    parser.add_argument("--circuits-repo-url", default="https://github.com/bacinger/f1-circuits.git")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_DIR / "docs" / "assets")
    args = parser.parse_args()

    analyzer.ensure_f1_circuits_repo(args.circuits_repo, args.circuits_repo_url)
    circuit_points, _ = analyzer.load_circuit_latlon(args.circuits_repo, args.circuit_id)
    origin = analyzer.projection_origin(circuit_points)
    gps_xy = [analyzer.latlon_to_xy(point, origin) for point in circuit_points]
    session = load_session(args.year, args.event, args.fastf1_cache_dir)

    draw_lap_examples(
        session=session,
        gps_xy=gps_xy,
        output=args.output_dir / "canada-2025-lap-diagnostic-overlays.svg",
    )

    print(f"Wrote {args.output_dir / 'canada-2025-lap-diagnostic-overlays.svg'}")


if __name__ == "__main__":
    main()
