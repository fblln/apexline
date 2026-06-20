from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from .artifacts import default_run_dir, normalize_session


def text_svg(x: float, y: float, text: str, *, size: int = 13, weight: int = 400, fill: str = "#111827") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Inter, Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}">{escape(text)}</text>'
    )


def load_event_diagnostics(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        if len(data) != 1:
            raise ValueError(f"{path} contains {len(data)} events; pass a single-event diagnostics file")
        return data[0]
    if isinstance(data, dict):
        return data
    raise ValueError(f"{path} must contain a diagnostics object or single-item list")


def render_svg(row: dict[str, Any], *, anchor_driver: str | None, highlighted_laps: list[str]) -> str:
    total = int(row["total_laps"])
    compliant = int(row["compliant_laps"])
    rejected = int(row["non_compliant_laps"])
    good_pct = compliant / total * 100 if total else 0.0
    reasons = [
        (reason, count)
        for reason, count in row.get("reason_counts", {}).items()
        if reason != "compliant" and count
    ]
    reasons.sort(key=lambda item: item[1], reverse=True)
    warning_count = sum(row.get("warning_counts", {}).values())

    width = 1100
    height = 520
    bar_x = 60
    bar_y = 168
    bar_w = 860
    good_w = bar_w * compliant / total if total else 0
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        text_svg(60, 58, f"{row['year']} {row['event_name']} {row['session_type']}: lap-geometry evidence", size=26, weight=700),
        text_svg(60, 88, f"{row['circuit_name']} / {row['circuit_id']}", size=14, fill="#475569"),
        text_svg(60, 132, f"{compliant:,} compliant laps / {rejected:,} rejected laps / {total:,} total", size=18, weight=700),
        text_svg(650, 132, f"{warning_count:,} non-blocking FastF1 warnings", size=14, fill="#2563eb"),
        f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="28" rx="4" fill="#dc2626"/>',
        f'<rect x="{bar_x}" y="{bar_y}" width="{good_w:.1f}" height="28" rx="4" fill="#059669"/>',
        text_svg(940, 189, f"{good_pct:.1f}% usable", size=14, weight=700, fill="#334155"),
        text_svg(60, 236, "Top rejection signals", size=17, weight=700),
    ]
    y = 270
    for reason, count in reasons[:6]:
        parts.extend(
            [
                f'<rect x="60" y="{y - 14}" width="{min(520, 8 + count * 2):.1f}" height="18" rx="3" fill="#cbd5e1"/>',
                text_svg(72, y, f"{reason}: {count:,}", size=13, fill="#111827"),
            ]
        )
        y += 32

    fastest = row.get("fastest_compliant_lap") or row.get("fastest_lap_with_position")
    if fastest:
        lap_time = fastest.get("lap_time_ms")
        lap_label = f"{fastest['driver']} lap {fastest['lap_number']}"
        if lap_time is not None:
            lap_label += f", {lap_time / 1000:.3f}s"
        parts.extend(
            [
                text_svg(650, 236, "Reference candidate", size=17, weight=700),
                text_svg(650, 270, lap_label, size=14),
                text_svg(650, 302, f"lap_key: {fastest.get('lap_key', 'legacy artifact')}", size=12, fill="#475569"),
            ]
        )
    if anchor_driver:
        parts.append(text_svg(650, 354, f"Requested anchor driver: {anchor_driver.upper()}", size=13, fill="#475569"))
    if highlighted_laps:
        parts.append(text_svg(650, 386, f"Highlighted laps: {', '.join(highlighted_laps)}", size=13, fill="#475569"))
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--event", required=True)
    parser.add_argument("--session", default="R")
    parser.add_argument("--diagnostics-json", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--base-output-dir", type=Path, default=Path("data"))
    parser.add_argument("--anchor-driver", default=None)
    parser.add_argument("--highlight-lap", action="append", default=[])
    args = parser.parse_args()

    session_type = normalize_session(args.session)
    run_dir = default_run_dir(args.base_output_dir, args.year, args.event, session_type)
    diagnostics_json = args.diagnostics_json or run_dir / "lap-diagnostics.json"
    output = args.output or run_dir / "evidence.svg"
    row = load_event_diagnostics(diagnostics_json)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        render_svg(row, anchor_driver=args.anchor_driver, highlighted_laps=args.highlight_lap),
        encoding="utf-8",
    )
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
