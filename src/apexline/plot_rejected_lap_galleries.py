#!/usr/bin/env python3
"""Generate SVG galleries for every rejected FastF1 lap in selected events."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from . import analyze_f1_circuit_gps as analyzer
from .artifacts import default_run_dir, normalize_session, provenance, slugify
from .fastf1_support import effective_shape_thresholds
from .geometry import normalize_repeated_lap_segment
from .plot_canada_examples import apply_transform, lap_transform
from .schemas import SCHEMA_VERSION


PROJECT_DIR = Path.cwd()


XY = tuple[float, float]


@dataclass(frozen=True)
class RejectedLap:
    driver: str
    lap_number: int
    lap_time_ms: int | None
    reasons: list[str]
    warnings: list[str]
    points: list[XY]
    path_length_m: float | None
    length_error_pct: float | None
    fit: analyzer.FitStats | None


def format_ms(ms: int | None) -> str:
    if ms is None:
        return "--"
    return f"{ms / 1000:.3f}s"


def slug(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-").replace("--", "-")


def relative_index_link(path: Path, index_output: Path) -> str:
    return Path(os.path.relpath(path.resolve(), index_output.parent.resolve())).as_posix()


def text_svg(x: float, y: float, text: str, *, size: int = 12, weight: int = 400, fill: str = "#111827") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Inter, Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}">{escape(text)}</text>'
    )


def bbox(points: list[XY]) -> tuple[float, float, float, float]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def merged_bbox(lines: list[list[XY]]) -> tuple[float, float, float, float]:
    non_empty = [line for line in lines if line]
    boxes = [bbox(line) for line in non_empty]
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
    return (
        offset_x + (point[0] - min_x) * scale,
        offset_y + used_h - (point[1] - min_y) * scale,
    )


def thin_points(points: list[XY], max_points: int) -> list[XY]:
    if max_points <= 0 or len(points) <= max_points:
        return points
    step = (len(points) - 1) / (max_points - 1)
    return [points[round(index * step)] for index in range(max_points)]


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
    max_render_points: int = 0,
) -> str:
    projected = [
        project(point, box, panel_x, panel_y, panel_w, panel_h, 8)
        for point in thin_points(points, max_render_points)
    ]
    coords = " ".join(f"{x:.1f},{y:.1f}" for x, y in projected)
    return (
        f'<polyline points="{coords}" fill="none" stroke="{stroke}" '
        f'stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round" opacity="{opacity}"/>'
    )


def main_reason(reasons: list[str]) -> str:
    priority = [
        "shape_rmse_over_threshold",
        "shape_p95_over_threshold",
        "path_length_outlier",
        "pit_lap",
        "too_few_position_samples",
        "no_position_data",
    ]
    for reason in priority:
        if reason in reasons:
            return reason
    return reasons[0] if reasons else "unknown"


def reason_color(reason: str) -> str:
    if reason.startswith("shape_"):
        return "#7c3aed"
    if reason == "path_length_outlier":
        return "#dc2626"
    if reason == "pit_lap":
        return "#f97316"
    return "#64748b"


def rejection_sort_key(lap: RejectedLap) -> tuple[int, float, str, int]:
    reason = main_reason(lap.reasons)
    if reason.startswith("shape_"):
        priority = 0
    elif reason == "path_length_outlier":
        priority = 1
    else:
        priority = 2
    fit_error = -(lap.fit.rmse_m if lap.fit is not None else 0.0)
    return priority, fit_error, lap.driver, lap.lap_number


def load_session(year: int, event: str, session_name: str, cache_dir: Path) -> Any:
    import fastf1  # type: ignore[import-not-found]

    cache_dir.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(str(cache_dir))
    session = fastf1.get_session(year, event, session_name)
    session.load(laps=True, telemetry=True, weather=False, messages=False)
    return session


def classify_laps(
    session: Any,
    gps_xy: list[XY],
    *,
    length_tolerance_pct: float,
    rmse_threshold_m: float,
    p95_threshold_m: float,
    rmse_threshold_pct_of_length: float,
    p95_threshold_pct_of_length: float,
    min_position_samples: int,
    validation_samples: int,
    validation_offset_step: int,
) -> list[RejectedLap]:
    reference_length_m = analyzer.path_length(gps_xy)
    effective_rmse_threshold_m, effective_p95_threshold_m = effective_shape_thresholds(
        reference_length_m=reference_length_m,
        rmse_threshold_m=rmse_threshold_m,
        p95_threshold_m=p95_threshold_m,
        rmse_threshold_pct_of_length=rmse_threshold_pct_of_length,
        p95_threshold_pct_of_length=p95_threshold_pct_of_length,
    )
    rejected: list[RejectedLap] = []

    for driver_ref in getattr(session, "drivers", []):
        try:
            driver = str(session.get_driver(driver_ref).get("Abbreviation")).upper()
        except Exception:
            driver = str(driver_ref).upper()

        for _, lap in session.laps.pick_drivers(driver).iterlaps():
            reasons: list[str] = []
            warnings: list[str] = []
            lap_number = int(lap.get("LapNumber"))
            lap_time_ms = analyzer.value_to_ms(lap.get("LapTime"))
            is_accurate = bool(lap.get("IsAccurate"))
            is_pit_lap = str(lap.get("PitOutTime")) != "NaT" or str(lap.get("PitInTime")) != "NaT"

            if not is_accurate:
                warnings.append("fastf1_inaccurate")
            if is_pit_lap:
                reasons.append("pit_lap")

            points = analyzer.lap_position_points(lap)
            if not points:
                reasons.append("no_position_data")
                rejected.append(
                    RejectedLap(driver, lap_number, lap_time_ms, reasons, warnings, points, None, None, None)
                )
                continue

            if len(points) < min_position_samples:
                reasons.append("too_few_position_samples")

            path_length_m = analyzer.path_length(analyzer.closed_path(points)) * 0.1
            effective_points = points
            effective_path_length_m = path_length_m
            length_error_pct = (path_length_m - reference_length_m) / reference_length_m
            effective_length_error_pct = length_error_pct
            if length_error_pct > length_tolerance_pct:
                normalized = normalize_repeated_lap_segment(
                    points,
                    target_length_m=reference_length_m,
                    length_tolerance_pct=length_tolerance_pct,
                    min_points=min_position_samples,
                )
                if normalized is not None:
                    effective_points, normalization = normalized
                    effective_path_length_m = normalization.normalized_path_length_m
                    effective_length_error_pct = (effective_path_length_m - reference_length_m) / reference_length_m
            if abs(effective_length_error_pct) > length_tolerance_pct:
                reasons.append("path_length_outlier")

            fit: analyzer.FitStats | None = None
            if (
                not is_pit_lap
                and len(points) >= min_position_samples
                and abs(effective_length_error_pct) <= length_tolerance_pct
            ):
                fit = analyzer.validate_shape(
                    fastf1_xy=effective_points,
                    gps_xy=gps_xy,
                    sample_count=validation_samples,
                    offset_step=validation_offset_step,
                )
                if fit.rmse_m > effective_rmse_threshold_m:
                    reasons.append("shape_rmse_over_threshold")
                if fit.p95_m > effective_p95_threshold_m:
                    reasons.append("shape_p95_over_threshold")

            if reasons:
                rejected.append(
                    RejectedLap(
                        driver=driver,
                        lap_number=lap_number,
                        lap_time_ms=lap_time_ms,
                        reasons=reasons,
                        warnings=warnings,
                        points=effective_points,
                        path_length_m=effective_path_length_m,
                        length_error_pct=effective_length_error_pct,
                        fit=fit,
                    )
                )

    return sorted(rejected, key=lambda item: (main_reason(item.reasons), item.driver, item.lap_number))


def choose_anchor(session: Any, gps_xy: list[XY], min_position_samples: int, length_tolerance_pct: float) -> tuple[str, int, complex, complex, analyzer.FitStats]:
    reference_length_m = analyzer.path_length(gps_xy)
    candidates: list[tuple[int, str, int, list[XY]]] = []

    for driver_ref in getattr(session, "drivers", []):
        try:
            driver = str(session.get_driver(driver_ref).get("Abbreviation")).upper()
        except Exception:
            driver = str(driver_ref).upper()
        for _, lap in session.laps.pick_drivers(driver).iterlaps():
            if not bool(lap.get("IsAccurate")):
                continue
            if str(lap.get("PitOutTime")) != "NaT" or str(lap.get("PitInTime")) != "NaT":
                continue
            lap_time_ms = analyzer.value_to_ms(lap.get("LapTime"))
            if lap_time_ms is None:
                continue
            points = analyzer.lap_position_points(lap)
            if len(points) < min_position_samples:
                continue
            path_length_m = analyzer.path_length(analyzer.closed_path(points)) * 0.1
            if abs((path_length_m - reference_length_m) / reference_length_m) > length_tolerance_pct:
                continue
            candidates.append((lap_time_ms, driver, int(lap.get("LapNumber")), points))

    if not candidates:
        raise RuntimeError("Could not find a clean anchor lap")

    # Try a few fast clean candidates and use the one with the best shape fit.
    scored = []
    for lap_time_ms, driver, lap_number, points in sorted(candidates)[:20]:
        scale_rotate, translation, fit = lap_transform(points, gps_xy)
        scored.append((fit.rmse_m, lap_time_ms, driver, lap_number, scale_rotate, translation, fit))
    _, _, driver, lap_number, scale_rotate, translation, fit = min(scored, key=lambda item: item[0])
    return driver, lap_number, scale_rotate, translation, fit


def draw_gallery(
    *,
    year: int,
    round_index: int,
    session_type: str,
    event_name: str,
    circuit_id: str,
    circuit_name: str,
    gps_xy: list[XY],
    rejected: list[RejectedLap],
    anchor_label: str,
    scale_rotate: complex,
    translation: complex,
    output: Path,
    max_render_points: int,
    thresholds: dict[str, Any],
    command_args: dict[str, Any],
) -> None:
    columns = 5
    panel_w = 244
    panel_h = 218
    gap = 12
    margin = 28
    header_h = 104
    rows = (len(rejected) + columns - 1) // columns
    width = margin * 2 + columns * panel_w + (columns - 1) * gap
    height = header_h + rows * (panel_h + gap) + margin
    reference_length_m = analyzer.path_length(gps_xy)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        text_svg(margin, 42, f"{year} {event_name}: every rejected lap", size=24, weight=700),
        text_svg(
            margin,
            68,
            f"{len(rejected)} rejected laps. Anchor transform: {anchor_label}. Circuit: {circuit_name}.",
            size=13,
            fill="#475569",
        ),
        text_svg(
            margin,
            88,
            "Gray is GPS reference; color is the rejected FastF1 lap projected with the same clean anchor transform.",
            size=12,
            fill="#64748b",
        ),
    ]

    for index, lap in enumerate(rejected):
        col = index % columns
        row = index // columns
        x = margin + col * (panel_w + gap)
        y = header_h + row * (panel_h + gap)
        reason = main_reason(lap.reasons)
        color = reason_color(reason)
        transformed = apply_transform(lap.points, scale_rotate, translation) if lap.points else []
        box = merged_bbox([gps_xy, transformed]) if transformed else bbox(gps_xy)
        chart_x = x + 10
        chart_y = y + 52
        chart_w = panel_w - 20
        chart_h = 104

        reason_text = ", ".join(lap.reasons)
        if lap.warnings:
            reason_text += f" | warning: {', '.join(lap.warnings)}"
        length_text = "--"
        if lap.path_length_m is not None and lap.length_error_pct is not None:
            length_text = f"{lap.path_length_m:.0f} m ({lap.length_error_pct * 100:+.1f}%)"
        fit_text = "shape fit skipped"
        if lap.fit is not None:
            fit_text = f"RMSE {lap.fit.rmse_m:.1f} m, p95 {lap.fit.p95_m:.1f} m"

        parts.extend(
            [
                f'<rect x="{x}" y="{y}" width="{panel_w}" height="{panel_h}" rx="8" fill="#ffffff" stroke="#cbd5e1"/>',
                text_svg(x + 10, y + 22, f"{lap.driver} lap {lap.lap_number}", size=13, weight=700),
                text_svg(x + 10, y + 40, reason_text[:42], size=10, fill=color),
                polyline_svg(
                    gps_xy,
                    box,
                    chart_x,
                    chart_y,
                    chart_w,
                    chart_h,
                    stroke="#94a3b8",
                    width=1.9,
                    opacity=0.85,
                    max_render_points=max_render_points,
                ),
            ]
        )
        if transformed:
            parts.append(
                polyline_svg(
                    transformed,
                    box,
                    chart_x,
                    chart_y,
                    chart_w,
                    chart_h,
                    stroke=color,
                    width=2.1,
                    opacity=0.95,
                    max_render_points=max_render_points,
                )
            )
            start = project(transformed[0], box, chart_x, chart_y, chart_w, chart_h, 8)
            end = project(transformed[-1], box, chart_x, chart_y, chart_w, chart_h, 8)
            parts.extend(
                [
                    f'<circle cx="{start[0]:.1f}" cy="{start[1]:.1f}" r="2.8" fill="#111827"/>',
                    f'<circle cx="{end[0]:.1f}" cy="{end[1]:.1f}" r="2.8" fill="#64748b"/>',
                ]
            )
        else:
            parts.append(text_svg(x + 48, y + 108, "no position data", size=11, fill="#64748b"))

        parts.extend(
            [
                text_svg(x + 10, y + 176, f"time {format_ms(lap.lap_time_ms)}", size=10, fill="#334155"),
                text_svg(x + 10, y + 192, f"length {length_text}", size=10, fill="#334155"),
                text_svg(x + 10, y + 208, fit_text, size=10, fill="#334155"),
            ]
        )

    parts.append("</svg>")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(parts), encoding="utf-8")

    # A small sidecar JSON makes the gallery auditable without parsing SVG text.
    sidecar = output.with_suffix(".json")
    sidecar.write_text(
        json.dumps(
            {
                "schema_version": SCHEMA_VERSION,
                "artifact_kind": "rejected_lap_gallery",
                "year": year,
                "session_type": session_type,
                "event_name": event_name,
                "round": round_index,
                "circuit_id": circuit_id,
                "circuit_name": circuit_name,
                "thresholds": thresholds,
                "generation_provenance": provenance(
                    command="apexline-rejected-galleries",
                    args=command_args,
                ),
                "reference_length_m": reference_length_m,
                "anchor": anchor_label,
                "max_render_points": max_render_points,
                "rendering_note": "max_render_points <= 0 means raw points are rendered without thinning",
                "rejected_laps": [
                    {
                        "driver": lap.driver,
                        "lap_number": lap.lap_number,
                        "lap_time_ms": lap.lap_time_ms,
                        "reasons": lap.reasons,
                        "warnings": lap.warnings,
                        "path_length_m": lap.path_length_m,
                        "length_error_pct": lap.length_error_pct,
                        "fit_rmse_m": lap.fit.rmse_m if lap.fit else None,
                        "fit_p95_m": lap.fit.p95_m if lap.fit else None,
                    }
                    for lap in rejected
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def write_index(entries: list[dict[str, Any]], output: Path) -> None:
    lines = [
        "# Rejected lap galleries",
        "",
        "Each SVG shows every rejected lap for the event. Rejected laps are",
        "projected with a clean anchor-lap transform for that event; they do not",
        "learn their own rotation or translation.",
        "FastF1 timing-accuracy warnings alone do not put a lap in this gallery.",
        "",
        "| Event | Rejected laps | Gallery | Data |",
        "|---|---:|---|---|",
    ]
    for entry in entries:
        lines.append(
            f"| {entry['event_name']} | {entry['count']} | "
            f"[SVG]({entry['svg']}) | [JSON]({entry['json']}) |"
        )
    lines.append("")
    for entry in entries:
        lines.extend([f"## {entry['event_name']}", "", f"![{entry['event_name']}]({entry['svg']})", ""])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--session", default="R")
    parser.add_argument(
        "--circuits",
        nargs="+",
        default=["Canada", "Australia", "British"],
        help="Circuit/event filters to render.",
    )
    parser.add_argument("--fastf1-cache-dir", type=Path, default=PROJECT_DIR / "data" / "fastf1-cache")
    parser.add_argument("--circuits-repo", type=Path, default=Path("/tmp/f1-circuits"))
    parser.add_argument("--circuits-repo-url", default="https://github.com/bacinger/f1-circuits.git")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--index-output", type=Path, default=None)
    parser.add_argument("--lap-length-tolerance-pct", type=float, default=0.05)
    parser.add_argument("--shape-rmse-threshold-m", type=float, default=32.0)
    parser.add_argument("--shape-p95-threshold-m", type=float, default=75.0)
    parser.add_argument("--shape-rmse-threshold-pct-of-length", type=float, default=0.016)
    parser.add_argument("--shape-p95-threshold-pct-of-length", type=float, default=0.025)
    parser.add_argument("--min-position-samples", type=int, default=100)
    parser.add_argument("--validation-samples", type=int, default=240)
    parser.add_argument("--validation-offset-step", type=int, default=8)
    parser.add_argument(
        "--max-render-points",
        type=int,
        default=0,
        help="Optional per-line point cap for smaller SVGs. Default 0 renders raw points without thinning.",
    )
    args = parser.parse_args()
    args.session = normalize_session(args.session)
    output_dir = args.output_dir or default_run_dir(PROJECT_DIR / "docs" / "assets" / "rejected-laps", args.year, "selected-events", args.session)
    index_output = args.index_output or PROJECT_DIR / "docs" / f"rejected-lap-galleries-{args.year}-{slugify(args.session)}.md"
    thresholds = {
        "lap_length_tolerance_pct": args.lap_length_tolerance_pct,
        "shape_rmse_threshold_m": args.shape_rmse_threshold_m,
        "shape_p95_threshold_m": args.shape_p95_threshold_m,
        "shape_rmse_threshold_pct_of_length": args.shape_rmse_threshold_pct_of_length,
        "shape_p95_threshold_pct_of_length": args.shape_p95_threshold_pct_of_length,
        "min_position_samples": args.min_position_samples,
        "validation_samples": args.validation_samples,
        "validation_offset_step": args.validation_offset_step,
    }
    command_args = {
        "year": args.year,
        "session": args.session,
        "circuits": args.circuits,
        "fastf1_cache_dir": str(args.fastf1_cache_dir),
        "circuits_repo": str(args.circuits_repo),
        "circuits_repo_url": args.circuits_repo_url,
        "output_dir": str(output_dir),
        "index_output": str(index_output),
        "max_render_points": args.max_render_points,
        **thresholds,
    }

    analyzer.ensure_f1_circuits_repo(args.circuits_repo, args.circuits_repo_url)
    championship = analyzer.load_json(args.circuits_repo / "championships" / f"f1-locations-{args.year}.json")

    import fastf1  # type: ignore[import-not-found]

    fastf1.Cache.enable_cache(str(args.fastf1_cache_dir))
    schedule = fastf1.get_event_schedule(args.year, include_testing=False)
    entries: list[dict[str, Any]] = []

    for query in args.circuits:
        matches = analyzer.find_circuit_rounds(championship, schedule, query)
        if len(matches) != 1:
            raise SystemExit(f"Expected one match for {query!r}, found {len(matches)}")
        round_index, circuit, event = matches[0]
        event_name = str(event["EventName"])
        circuit_id = str(circuit["id"])
        circuit_points, _ = analyzer.load_circuit_latlon(args.circuits_repo, circuit_id)
        origin = analyzer.projection_origin(circuit_points)
        gps_xy = [analyzer.latlon_to_xy(point, origin) for point in circuit_points]
        session = load_session(args.year, event_name, args.session, args.fastf1_cache_dir)
        rejected = classify_laps(
            session,
            gps_xy,
            length_tolerance_pct=args.lap_length_tolerance_pct,
            rmse_threshold_m=args.shape_rmse_threshold_m,
            p95_threshold_m=args.shape_p95_threshold_m,
            rmse_threshold_pct_of_length=args.shape_rmse_threshold_pct_of_length,
            p95_threshold_pct_of_length=args.shape_p95_threshold_pct_of_length,
            min_position_samples=args.min_position_samples,
            validation_samples=args.validation_samples,
            validation_offset_step=args.validation_offset_step,
        )
        rejected.sort(key=rejection_sort_key)
        effective_rmse_threshold_m, effective_p95_threshold_m = effective_shape_thresholds(
            reference_length_m=analyzer.path_length(gps_xy),
            rmse_threshold_m=args.shape_rmse_threshold_m,
            p95_threshold_m=args.shape_p95_threshold_m,
            rmse_threshold_pct_of_length=args.shape_rmse_threshold_pct_of_length,
            p95_threshold_pct_of_length=args.shape_p95_threshold_pct_of_length,
        )
        event_thresholds = {
            **thresholds,
            "reference_length_m": analyzer.path_length(gps_xy),
            "effective_rmse_threshold_m": effective_rmse_threshold_m,
            "effective_p95_threshold_m": effective_p95_threshold_m,
        }
        anchor_driver, anchor_lap, scale_rotate, translation, anchor_fit = choose_anchor(
            session,
            gps_xy,
            min_position_samples=args.min_position_samples,
            length_tolerance_pct=args.lap_length_tolerance_pct,
        )
        anchor_label = f"{anchor_driver} lap {anchor_lap}, RMSE {anchor_fit.rmse_m:.1f} m"
        output = output_dir / f"{round_index:02d}-{slug(event_name)}.svg"
        draw_gallery(
            year=args.year,
            round_index=round_index,
            session_type=args.session,
            event_name=event_name,
            circuit_id=circuit_id,
            circuit_name=str(circuit["name"]),
            gps_xy=gps_xy,
            rejected=rejected,
            anchor_label=anchor_label,
            scale_rotate=scale_rotate,
            translation=translation,
            output=output,
            max_render_points=args.max_render_points,
            thresholds=event_thresholds,
            command_args=command_args,
        )
        entries.append(
            {
                "event_name": event_name,
                "count": len(rejected),
                "svg": relative_index_link(output, index_output),
                "json": relative_index_link(output.with_suffix(".json"), index_output),
            }
        )
        print(f"{event_name}: wrote {len(rejected)} rejected laps to {output}")

    write_index(entries, index_output)
    print(f"Wrote {index_output}")


if __name__ == "__main__":
    main()
