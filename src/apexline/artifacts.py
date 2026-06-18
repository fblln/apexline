from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .schemas import SCHEMA_VERSION


SESSION_ALIASES = {
    "RACE": "R",
    "QUALIFYING": "Q",
    "SPRINT": "S",
    "SPRINT QUALIFYING": "SQ",
    "SPRINT SHOOTOUT": "SQ",
    "PRACTICE 1": "FP1",
    "PRACTICE 2": "FP2",
    "PRACTICE 3": "FP3",
}


def slugify(value: object) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
    return slug or "unknown"


def normalize_session(value: str) -> str:
    cleaned = " ".join(value.strip().upper().replace("_", " ").replace("-", " ").split())
    return SESSION_ALIASES.get(cleaned, cleaned)


def session_slug(value: str) -> str:
    return slugify(normalize_session(value).lower())


def default_run_dir(base_dir: Path, year: int, event_name: str, session_type: str) -> Path:
    return base_dir / str(year) / slugify(event_name) / session_slug(session_type)


def default_batch_dir(base_dir: Path, year: int, session_type: str) -> Path:
    return base_dir / str(year) / "all-events" / session_slug(session_type)


def generated_at() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def provenance(*, command: str, args: dict[str, Any]) -> dict[str, Any]:
    return {
        "generated_at": generated_at(),
        "generator": "apexline",
        "schema_version": SCHEMA_VERSION,
        "command": command,
        "args": args,
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def artifact_manifest(
    *,
    run_mode: str,
    year: int,
    event_name: str | None,
    session_type: str,
    circuit_id: str | None,
    thresholds: dict[str, Any],
    outputs: dict[str, str],
    provenance_payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "artifact_manifest",
        "run_mode": run_mode,
        "year": year,
        "event_name": event_name,
        "session_type": normalize_session(session_type),
        "circuit_id": circuit_id,
        "thresholds": thresholds,
        "outputs": outputs,
        "provenance": provenance_payload,
    }


def relative_outputs(paths: dict[str, Path], base_dir: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for name, path in paths.items():
        try:
            result[name] = path.relative_to(base_dir).as_posix()
        except ValueError:
            result[name] = path.as_posix()
    return result
