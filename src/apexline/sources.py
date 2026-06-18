from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from .models import LatLon


def ensure_f1_circuits_repo(repo_dir: Path, repo_url: str) -> None:
    if (repo_dir / "championships").is_dir() and (repo_dir / "circuits").is_dir():
        return

    repo_dir.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, str(repo_dir)],
        check=True,
    )


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_circuit_latlon(repo_dir: Path, circuit_id: str) -> tuple[list[LatLon], dict[str, Any]]:
    geojson = load_json(repo_dir / "circuits" / f"{circuit_id}.geojson")
    feature = geojson["features"][0]
    geometry = feature["geometry"]
    if geometry["type"] != "LineString":
        raise ValueError(f"{circuit_id} geometry is {geometry['type']}, expected LineString")

    points = [(float(lat), float(lon)) for lon, lat in geometry["coordinates"]]
    if points[-1] != points[0]:
        points.append(points[0])
    return points, feature.get("properties", {})


def normalize_key(value: object) -> str:
    return "".join(ch.lower() for ch in str(value) if ch.isalnum())


def find_circuit_rounds(championship: list[dict[str, Any]], schedule: Any, query: str | None) -> list[tuple[int, dict[str, Any], Any]]:
    matches: list[tuple[int, dict[str, Any], Any]] = []
    normalized_query = normalize_key(query or "")
    for round_index, circuit in enumerate(championship, start=1):
        event = schedule.iloc[round_index - 1]
        if not normalized_query:
            matches.append((round_index, circuit, event))
            continue

        haystack = [
            circuit.get("id", ""),
            circuit.get("name", ""),
            circuit.get("location", ""),
            event.get("EventName", ""),
            event.get("Location", ""),
            event.get("Country", ""),
        ]
        if any(normalized_query in normalize_key(item) for item in haystack):
            matches.append((round_index, circuit, event))

    return matches


def list_circuit_candidates(championship: list[dict[str, Any]], schedule: Any, limit: int = 8) -> list[str]:
    candidates: list[str] = []
    for round_index, circuit in enumerate(championship[:limit], start=1):
        event = schedule.iloc[round_index - 1]
        candidates.append(
            "{round}: {event} / {circuit_id} / {circuit_name}".format(
                round=round_index,
                event=event.get("EventName", ""),
                circuit_id=circuit.get("id", ""),
                circuit_name=circuit.get("name", ""),
            )
        )
    return candidates


def value_to_ms(value: Any) -> int | None:
    if value is None or str(value) == "NaT" or str(value) == "nan":
        return None
    try:
        total_seconds = value.total_seconds()
    except AttributeError:
        return None
    return int(round(total_seconds * 1000))


def flatten_for_csv(row: dict[str, Any]) -> dict[str, Any]:
    flattened: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, dict):
            for inner_key, inner_value in value.items():
                flattened[f"{key}_{inner_key}"] = inner_value
        elif key != "encoded_polyline":
            flattened[key] = value
    return flattened
