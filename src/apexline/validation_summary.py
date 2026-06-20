#!/usr/bin/env python3
"""Summarize Apexline circuit-analysis outputs into markdown and SVG artifacts."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from .artifacts import session_slug


PROJECT_DIR = Path.cwd()


def load_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError(f"{path} should contain a list of circuit analysis rows")
    return data


def analysis_from_manifest(path: Path) -> tuple[Path, int]:
    with path.open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    outputs = manifest.get("outputs", {})
    analysis = outputs.get("circuit_analysis_json")
    if not analysis:
        raise ValueError(f"{path} does not declare outputs.circuit_analysis_json")
    analysis_path = Path(analysis)
    if not analysis_path.is_absolute():
        analysis_path = Path.cwd() / analysis_path
    return analysis_path, int(manifest.get("year", 0))


def fmt_m(value: float) -> str:
    return f"{value:.1f} m"


def short_event_name(name: str) -> str:
    return (
        name.replace("Grand Prix", "GP")
        .replace("Emilia Romagna GP", "Emilia Romagna GP")
        .replace("Mexico City GP", "Mexico City GP")
    )


def complete_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("validation_complete")]


def best_rmse(row: dict[str, Any]) -> float:
    return float(row["repo_vs_fastf1"]["rmse_m"])


def best_p95(row: dict[str, Any]) -> float:
    return float(row["repo_vs_fastf1"]["p95_m"])


def avg_rmse(row: dict[str, Any]) -> float:
    return float(row["repo_vs_fastf1_average"]["rmse_m"])


def polyline_points(row: dict[str, Any]) -> int:
    return int(row["polyline_vs_source"]["simplified_points"])


def polyline_chars(row: dict[str, Any]) -> int:
    return int(row["polyline_vs_source"]["encoded_chars"])


def polyline_max_err(row: dict[str, Any]) -> float:
    return float(row["polyline_vs_source"]["max_m"])


def declared_length_km(row: dict[str, Any]) -> float:
    length_m = row.get("declared_length_m")
    if isinstance(length_m, (int, float)) and length_m > 0:
        return float(length_m) / 1000.0
    return max(float(row["polyline_vs_source"]["source_length_m"]) / 1000.0, 1e-9)


def compactness_chars_per_km(row: dict[str, Any]) -> float:
    return polyline_chars(row) / declared_length_km(row)


def build_markdown(rows: list[dict[str, Any]], year: int) -> str:
    rows = sorted(complete_rows(rows), key=lambda item: item["round"])
    best_rmses = [best_rmse(row) for row in rows]
    avg_rmses = [avg_rmse(row) for row in rows]
    improved = [row for row in rows if avg_rmse(row) < best_rmse(row)]
    worsened = [row for row in rows if avg_rmse(row) > best_rmse(row)]
    compact = sorted(rows, key=compactness_chars_per_km)[:5]

    lines = [
        f"# {year} Validation Summary",
        "",
        "This run compares oracle circuit GPS LineStrings against FastF1 race-lap",
        "`X/Y` shapes after Apexline's lap filtering, overlap repair, phase search,",
        "and similarity fit.",
        "",
        "The residuals are shape-fit errors, not car GPS errors.",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Circuits processed | {len(rows)} |",
        f"| Best single-lap mean RMSE | {statistics.mean(best_rmses):.1f} m |",
        f"| Best single-lap median RMSE | {statistics.median(best_rmses):.1f} m |",
        f"| Worst best-lap RMSE | {max(best_rmses):.1f} m |",
        f"| Average-of-5 mean RMSE | {statistics.mean(avg_rmses):.1f} m |",
        f"| Average-of-5 median RMSE | {statistics.median(avg_rmses):.1f} m |",
        f"| Averaging improved | {len(improved)} / {len(rows)} |",
        f"| Averaging worsened | {len(worsened)} / {len(rows)} |",
        f"| Polyline simplification tolerance | {rows[0]['polyline_vs_source']['tolerance_m']:.1f} m |",
        f"| Worst simplification error | <= {max(polyline_max_err(row) for row in rows):.1f} m |",
        "",
        "## Full Table",
        "",
        "| Round | Event | Circuit | Best RMSE | Best p95 | Avg-5 RMSE | Polyline pts | Chars | Max simpl. err |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {round} | {event} | {circuit} | {best} | {p95} | {avg} | {points} | {chars} | {err} |".format(
                round=row["round"],
                event=short_event_name(row["event_name"]),
                circuit=row["circuit_name"],
                best=fmt_m(best_rmse(row)),
                p95=fmt_m(best_p95(row)),
                avg=fmt_m(avg_rmse(row)),
                points=polyline_points(row),
                chars=polyline_chars(row),
                err=fmt_m(polyline_max_err(row)),
            )
        )

    lines.extend(
        [
            "",
            "## Biggest Deviations",
            "",
            "Using the best single FastF1 lap:",
            "",
            "| Rank | Event | RMSE | p95 |",
            "|---:|---|---:|---:|",
        ]
    )
    for index, row in enumerate(sorted(rows, key=best_rmse, reverse=True)[:5], start=1):
        lines.append(f"| {index} | {short_event_name(row['event_name'])} | {fmt_m(best_rmse(row))} | {fmt_m(best_p95(row))} |")

    lines.extend(
        [
            "",
            "## Averaging Helps vs Hurts",
            "",
            "| Event | Best RMSE | Avg-5 RMSE | Delta |",
            "|---|---:|---:|---:|",
        ]
    )
    deltas = sorted(rows, key=lambda row: avg_rmse(row) - best_rmse(row), reverse=True)
    for row in deltas[:5]:
        delta = avg_rmse(row) - best_rmse(row)
        lines.append(
            f"| {short_event_name(row['event_name'])} | {fmt_m(best_rmse(row))} | {fmt_m(avg_rmse(row))} | +{delta:.1f} m |"
        )
    for row in sorted(rows, key=lambda row: avg_rmse(row) - best_rmse(row))[:5]:
        delta = avg_rmse(row) - best_rmse(row)
        lines.append(
            f"| {short_event_name(row['event_name'])} | {fmt_m(best_rmse(row))} | {fmt_m(avg_rmse(row))} | {delta:.1f} m |"
        )

    lines.extend(
        [
            "",
            "## Most Compact Oracle Polylines",
            "",
            "| Event | Circuit km | Points | Chars | Chars / km |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in compact:
        lines.append(
            "| {event} | {km:.3f} | {points} | {chars} | {ratio:.1f} |".format(
                event=short_event_name(row["event_name"]),
                km=declared_length_km(row),
                points=polyline_points(row),
                chars=polyline_chars(row),
                ratio=compactness_chars_per_km(row),
            )
        )

    return "\n".join(lines) + "\n"


def text_svg(x: float, y: float, text: str, *, size: int = 13, weight: int = 400, fill: str = "#111827") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Inter, Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}">{escape(text)}</text>'
    )


def build_svg(rows: list[dict[str, Any]], year: int) -> str:
    rows = sorted(complete_rows(rows), key=lambda item: item["round"])
    width = 1380
    row_h = 24
    header_h = 150
    footer_h = 40
    height = header_h + len(rows) * row_h + footer_h
    chart_x = 390
    chart_w = 790
    value_x = 1230
    max_rmse = max(max(best_rmse(row), avg_rmse(row)) for row in rows)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        text_svg(34, 42, f"{year} oracle-vs-FastF1 shape RMSE by circuit", size=24, weight=700),
        text_svg(34, 68, "Green is the best single validated lap. Slate is the average of the best five fitted laps.", size=14, fill="#475569"),
        text_svg(34, 90, "Lower is better. Averaging can help or hurt because racing lines are not centerlines.", size=14, fill="#475569"),
    ]

    for tick in range(0, int(max_rmse // 5 + 2) * 5, 5):
        x = chart_x + chart_w * tick / max_rmse
        parts.append(f'<line x1="{x:.1f}" y1="{header_h - 12}" x2="{x:.1f}" y2="{height - footer_h}" stroke="#e2e8f0"/>')
        parts.append(text_svg(x - 6, header_h - 18, str(tick), size=11, fill="#64748b"))
    parts.append(text_svg(chart_x, 116, "RMSE (m)", size=12, fill="#64748b"))

    for index, row in enumerate(rows):
        y = header_h + index * row_h
        parts.append(text_svg(34, y + 14, f"{row['round']:02d} {short_event_name(row['event_name'])}", size=12, fill="#334155"))
        best_x = chart_x + chart_w * best_rmse(row) / max_rmse
        avg_x = chart_x + chart_w * avg_rmse(row) / max_rmse
        parts.append(f'<line x1="{chart_x}" y1="{y + 10:.1f}" x2="{avg_x:.1f}" y2="{y + 10:.1f}" stroke="#94a3b8" stroke-width="3" opacity="0.9"/>')
        parts.append(f'<circle cx="{best_x:.1f}" cy="{y + 10:.1f}" r="4.4" fill="#059669"/>')
        parts.append(f'<circle cx="{avg_x:.1f}" cy="{y + 10:.1f}" r="4.0" fill="#334155"/>')
        parts.append(text_svg(value_x, y + 14, f"{best_rmse(row):.1f} / {avg_rmse(row):.1f}", size=11, fill="#475569"))

    parts.extend(
        [
            '<rect x="650" y="102" width="18" height="8" fill="#059669"/>',
            text_svg(675, 110, "best lap", size=12, fill="#475569"),
            '<rect x="748" y="102" width="18" height="8" fill="#334155"/>',
            text_svg(773, 110, "avg of best 5", size=12, fill="#475569"),
            "</svg>",
        ]
    )
    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--session", default="R")
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--circuit-analysis-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    parser.add_argument("--output-svg", type=Path, default=None)
    args = parser.parse_args()

    year = args.year
    if args.manifest is not None:
        analysis_json, manifest_year = analysis_from_manifest(args.manifest)
        year = manifest_year or year
    else:
        analysis_json = args.circuit_analysis_json or (
            PROJECT_DIR / "data" / str(year) / "all-events" / session_slug(args.session) / "circuit-analysis.json"
        )
    output_md = args.output_md or PROJECT_DIR / "docs" / f"{year}-validation-summary.md"
    output_svg = args.output_svg or PROJECT_DIR / "docs" / "assets" / f"validation-rmse-{year}.svg"

    rows = load_rows(analysis_json)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_svg.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(build_markdown(rows, year), encoding="utf-8")
    output_svg.write_text(build_svg(rows, year), encoding="utf-8")

    print(f"Wrote {output_md}")
    print(f"Wrote {output_svg}")


if __name__ == "__main__":
    main()
