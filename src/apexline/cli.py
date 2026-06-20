from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .artifacts import (
    artifact_manifest,
    default_batch_dir,
    default_run_dir,
    normalize_session,
    provenance,
    relative_outputs,
    write_json,
)
from .fastf1_support import analyze_lap_compliance, lap_key, score_fastf1_laps
from .geometry import (
    average_fitted_laps,
    direct_line_stats,
    encode_polyline,
    latlon_to_xy,
    projection_origin,
    rdp,
    simplification_stats,
    validate_shape,
    xy_to_latlon,
)
from .schemas import SCHEMA_VERSION, validate_any_artifact
from .sources import (
    ensure_f1_circuits_repo,
    find_circuit_rounds,
    flatten_for_csv,
    list_circuit_candidates,
    load_circuit_latlon,
    load_json,
)


def common_run_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--year", type=int, required=False, default=2025)
    parser.add_argument("--session", default="R")
    parser.add_argument("--fastf1-cache-dir", type=Path, default=Path("data/fastf1-cache"))
    parser.add_argument("--circuits-repo", type=Path, default=Path("/tmp/f1-circuits"))
    parser.add_argument("--circuits-repo-url", default="https://github.com/bacinger/f1-circuits.git")
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-csv", type=Path, default=None)
    parser.add_argument("--lap-diagnostics-output", type=Path, default=None)
    parser.add_argument("--manifest-output", type=Path, default=None)
    parser.add_argument(
        "--write-mode",
        choices=["overwrite", "skip-existing", "fail-if-exists"],
        default="overwrite",
    )
    parser.add_argument("--polyline-tolerance-m", type=float, default=1.0)
    parser.add_argument("--polyline-precision", type=int, default=5)
    parser.add_argument("--validation-samples", type=int, default=720)
    parser.add_argument("--validation-offset-step", type=int, default=4)
    parser.add_argument("--max-shape-candidates", type=int, default=12)
    parser.add_argument("--average-laps", type=int, default=5)
    parser.add_argument("--average-samples", type=int, default=720)
    parser.add_argument("--preferred-driver", default=None)
    parser.add_argument("--lap-diagnostics-samples", type=int, default=240)
    parser.add_argument("--lap-diagnostics-offset-step", type=int, default=8)
    parser.add_argument("--lap-length-tolerance-pct", type=float, default=0.05)
    parser.add_argument("--shape-rmse-threshold-m", type=float, default=32.0)
    parser.add_argument("--shape-p95-threshold-m", type=float, default=75.0)
    parser.add_argument("--shape-rmse-threshold-pct-of-length", type=float, default=0.016)
    parser.add_argument("--shape-p95-threshold-pct-of-length", type=float, default=0.025)
    parser.add_argument("--min-position-samples", type=int, default=100)
    parser.add_argument("--dry-run", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="apexline")
    subparsers = parser.add_subparsers(dest="command")

    validate = subparsers.add_parser("validate", help="Validate one FastF1 event/session.")
    validate.add_argument("--event", "--circuit", dest="event", required=True)
    validate.add_argument("--circuit-id", default=None)
    common_run_args(validate)

    batch = subparsers.add_parser("batch", help="Validate every event for one year/session.")
    batch.add_argument("--all-events", action="store_true", default=True)
    batch.add_argument("--limit", type=int, default=None)
    common_run_args(batch)

    schema_check = subparsers.add_parser("schema-check", help="Validate Apexline JSON artifacts.")
    schema_check.add_argument("paths", nargs="+", type=Path)
    schema_check.add_argument("--allow-legacy", action="store_true")

    fixture = subparsers.add_parser("fixture-demo", help="Write a no-download demo artifact set.")
    fixture.add_argument("--output-dir", type=Path, default=Path("data/fixture-demo"))
    fixture.add_argument(
        "--write-mode",
        choices=["overwrite", "skip-existing", "fail-if-exists"],
        default="overwrite",
    )

    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    argv = list(sys.argv[1:] if argv is None else argv)
    commands = {"validate", "batch", "schema-check", "fixture-demo"}
    if argv and argv[0] not in commands and argv[0] not in {"-h", "--help"}:
        if "--circuit" in argv or "--event" in argv:
            argv.insert(0, "validate")
        else:
            argv.insert(0, "batch")
    return build_parser().parse_args(argv)


def thresholds(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "polyline_tolerance_m": args.polyline_tolerance_m,
        "polyline_precision": args.polyline_precision,
        "validation_samples": args.validation_samples,
        "validation_offset_step": args.validation_offset_step,
        "max_shape_candidates": args.max_shape_candidates,
        "average_laps": args.average_laps,
        "average_samples": args.average_samples,
        "lap_diagnostics_samples": args.lap_diagnostics_samples,
        "lap_diagnostics_offset_step": args.lap_diagnostics_offset_step,
        "lap_length_tolerance_pct": args.lap_length_tolerance_pct,
        "shape_rmse_threshold_m": args.shape_rmse_threshold_m,
        "shape_p95_threshold_m": args.shape_p95_threshold_m,
        "shape_rmse_threshold_pct_of_length": args.shape_rmse_threshold_pct_of_length,
        "shape_p95_threshold_pct_of_length": args.shape_p95_threshold_pct_of_length,
        "min_position_samples": args.min_position_samples,
    }


def namespace_args(args: argparse.Namespace) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in vars(args).items():
        if isinstance(value, Path):
            result[key] = value.as_posix()
        else:
            result[key] = value
    return result


def guard_output_targets(paths: list[Path], write_mode: str) -> bool:
    existing = [path for path in paths if path.exists()]
    if write_mode == "overwrite":
        return True
    if write_mode == "fail-if-exists" and existing:
        names = ", ".join(str(path) for path in existing)
        raise SystemExit(f"Refusing to overwrite existing output(s): {names}")
    if write_mode == "skip-existing":
        if len(existing) == len(paths):
            print("All target outputs already exist; skipping because --write-mode=skip-existing.")
            return False
        if existing:
            names = ", ".join(str(path) for path in existing)
            raise SystemExit(f"Partial output set already exists, refusing skip-existing run: {names}")
    return True


def load_schedule(year: int, cache_dir: Path) -> Any:
    try:
        import fastf1  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:
        raise RuntimeError("FastF1 is not installed") from exc

    fastf1.Cache.enable_cache(str(cache_dir))
    return fastf1.get_event_schedule(year, include_testing=False)


def prepare_context(args: argparse.Namespace) -> tuple[list[dict[str, Any]], Any]:
    ensure_f1_circuits_repo(args.circuits_repo, args.circuits_repo_url)
    championship = load_json(args.circuits_repo / "championships" / f"f1-locations-{args.year}.json")
    schedule = load_schedule(args.year, args.fastf1_cache_dir)
    return championship, schedule


def resolve_validate_target(args: argparse.Namespace, championship: list[dict[str, Any]], schedule: Any) -> tuple[int, dict[str, Any], Any]:
    matches = find_circuit_rounds(championship, schedule, args.event)
    if not matches:
        candidates = "\n".join(f"  - {item}" for item in list_circuit_candidates(championship, schedule))
        raise SystemExit(
            f"No circuit/event matched {args.event!r} for {args.year}. "
            f"Use --circuit-id with a known f1-circuits id if the event mapping is ambiguous.\nCandidates:\n{candidates}"
        )
    if len(matches) > 1:
        candidates = "\n".join(
            f"  - round {round_index}: {event.get('EventName', '')} / {circuit.get('id', '')}"
            for round_index, circuit, event in matches[:8]
        )
        raise SystemExit(f"{args.event!r} matched multiple events. Use a more specific --event.\nMatches:\n{candidates}")
    return matches[0]


def output_paths(args: argparse.Namespace, *, event_name: str | None, batch: bool = False) -> dict[str, Path]:
    session_type = normalize_session(args.session)
    if batch:
        run_dir = default_batch_dir(args.output_dir, args.year, session_type)
    elif event_name is not None:
        run_dir = default_run_dir(args.output_dir, args.year, event_name, session_type)
    else:
        run_dir = args.output_dir
    return {
        "circuit_analysis_json": args.output_json or run_dir / "circuit-analysis.json",
        "circuit_analysis_csv": args.output_csv or run_dir / "circuit-analysis.csv",
        "lap_diagnostics_json": args.lap_diagnostics_output or run_dir / "lap-diagnostics.json",
        "manifest_json": args.manifest_output or run_dir / "artifact-manifest.json",
    }


def circuit_analysis_incomplete(
    *,
    args: argparse.Namespace,
    round_index: int,
    circuit: dict[str, Any],
    event: Any,
    reason: str,
    lap_diagnostics: dict[str, Any],
    provenance_payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "circuit_analysis_row",
        "provenance": provenance_payload,
        "validation_complete": False,
        "analysis_status": "incomplete",
        "incomplete_reason": reason,
        "year": args.year,
        "round": round_index,
        "event_name": str(event["EventName"]),
        "session_type": normalize_session(args.session),
        "fastf1_location": str(event["Location"]),
        "circuit_id": str(circuit["id"]),
        "circuit_name": circuit["name"],
        "repo_location": circuit["location"],
        "declared_length_m": None,
        "fastf1_driver": None,
        "fastf1_lap": None,
        "fastf1_points": 0,
        "fastf1_path_length_m": None,
        "repo_vs_fastf1": None,
        "averaged_fastf1_laps": [],
        "repo_vs_fastf1_average": None,
        "lap_compliance_summary": lap_diagnostics,
        "averaged_fastf1_polyline_vs_source": None,
        "polyline_vs_source": None,
        "polyline_vs_fastf1": None,
        "encoded_polyline": None,
        "averaged_fastf1_encoded_polyline": None,
    }


def analyze_event(
    *,
    args: argparse.Namespace,
    round_index: int,
    circuit: dict[str, Any],
    event: Any,
    provenance_payload: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    event_name = str(event["EventName"])
    circuit_id = getattr(args, "circuit_id", None) or str(circuit["id"])
    circuit_points, properties = load_circuit_latlon(args.circuits_repo, circuit_id)
    origin = projection_origin(circuit_points)
    gps_xy = [latlon_to_xy(point, origin) for point in circuit_points]
    session_type = normalize_session(args.session)

    lap_diagnostics = analyze_lap_compliance(
        year=args.year,
        round_index=round_index,
        event=event_name,
        cache_dir=args.fastf1_cache_dir,
        session_name=session_type,
        reference_xy=gps_xy,
        validation_samples=args.lap_diagnostics_samples,
        validation_offset_step=args.lap_diagnostics_offset_step,
        length_tolerance_pct=args.lap_length_tolerance_pct,
        rmse_threshold_m=args.shape_rmse_threshold_m,
        p95_threshold_m=args.shape_p95_threshold_m,
        rmse_threshold_pct_of_length=args.shape_rmse_threshold_pct_of_length,
        p95_threshold_pct_of_length=args.shape_p95_threshold_pct_of_length,
        min_position_samples=args.min_position_samples,
    )
    lap_event = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "lap_diagnostics_event",
        "provenance": provenance_payload,
        "year": args.year,
        "session_type": session_type,
        "round": round_index,
        "event_name": event_name,
        "circuit_id": circuit_id,
        "circuit_name": circuit["name"],
        **lap_diagnostics,
    }

    try:
        scored_laps = score_fastf1_laps(
            year=args.year,
            event=event_name,
            cache_dir=args.fastf1_cache_dir,
            session_name=session_type,
            preferred_driver=args.preferred_driver,
            reference_xy=gps_xy,
            validation_samples=args.validation_samples,
            validation_offset_step=args.validation_offset_step,
            max_shape_candidates=args.max_shape_candidates,
        )
    except RuntimeError as exc:
        return (
            circuit_analysis_incomplete(
                args=args,
                round_index=round_index,
                circuit={**circuit, "id": circuit_id},
                event=event,
                reason=str(exc),
                lap_diagnostics={
                    key: lap_diagnostics[key]
                    for key in (
                        "total_laps",
                        "fitted_laps",
                        "compliant_laps",
                        "non_compliant_laps",
                        "shape_non_compliant_laps",
                        "reason_counts",
                        "warning_counts",
                        "thresholds",
                        "fastest_lap_with_position",
                        "fastest_compliant_lap",
                    )
                },
                provenance_payload=provenance_payload,
            ),
            lap_event,
        )

    best_scored_lap = scored_laps[0]
    fastf1_lap = best_scored_lap.lap
    fit = best_scored_lap.fit
    averaged_source_xy = average_fitted_laps(
        scored_laps[: args.average_laps],
        gps_xy=gps_xy,
        sample_count=args.average_samples,
    )
    averaged_simplified_xy = rdp(averaged_source_xy, args.polyline_tolerance_m)
    averaged_latlon = [xy_to_latlon(point, origin) for point in averaged_simplified_xy]
    averaged_encoded = encode_polyline(averaged_latlon, args.polyline_precision)
    averaged_simplification = simplification_stats(
        averaged_source_xy,
        averaged_simplified_xy,
        args.polyline_tolerance_m,
        averaged_encoded,
    )
    averaged_vs_repo = direct_line_stats(
        averaged_source_xy,
        gps_xy,
        sample_count=args.validation_samples,
    )
    simplified_xy = rdp(gps_xy, args.polyline_tolerance_m)
    simplified_latlon = [xy_to_latlon(point, origin) for point in simplified_xy]
    encoded = encode_polyline(simplified_latlon, args.polyline_precision)
    simp = simplification_stats(gps_xy, simplified_xy, args.polyline_tolerance_m, encoded)
    simplified_fit = validate_shape(
        fastf1_xy=fastf1_lap.points,
        gps_xy=simplified_xy,
        sample_count=args.validation_samples,
        offset_step=args.validation_offset_step,
    )

    row = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "circuit_analysis_row",
        "provenance": provenance_payload,
        "validation_complete": True,
        "analysis_status": "complete",
        "incomplete_reason": None,
        "year": args.year,
        "round": round_index,
        "event_name": event_name,
        "session_type": session_type,
        "fastf1_location": str(event["Location"]),
        "circuit_id": circuit_id,
        "circuit_name": circuit["name"],
        "repo_location": circuit["location"],
        "declared_length_m": properties.get("length"),
        "fastf1_driver": fastf1_lap.driver,
        "fastf1_lap": fastf1_lap.lap_number,
        "fastf1_lap_key": lap_key(args.year, round_index, event_name, session_type, fastf1_lap.driver, fastf1_lap.lap_number),
        "fastf1_points": len(fastf1_lap.points),
        "fastf1_path_length_m": fastf1_lap.path_length_m,
        "fastf1_raw_path_length_m": fastf1_lap.raw_path_length_m,
        "fastf1_normalization": asdict(fastf1_lap.normalization) if fastf1_lap.normalization is not None else None,
        "repo_vs_fastf1": asdict(fit),
        "averaged_fastf1_laps": [
            {
                "driver": item.lap.driver,
                "lap": item.lap.lap_number,
                "lap_key": lap_key(args.year, round_index, event_name, session_type, item.lap.driver, item.lap.lap_number),
                "path_length_m": item.lap.path_length_m,
                "raw_path_length_m": item.lap.raw_path_length_m,
                "normalization": asdict(item.lap.normalization) if item.lap.normalization is not None else None,
                "length_error_m": item.length_error_m,
                "rmse_m": item.fit.rmse_m,
                "p95_m": item.fit.p95_m,
            }
            for item in scored_laps[: args.average_laps]
        ],
        "repo_vs_fastf1_average": asdict(averaged_vs_repo),
        "lap_compliance_summary": {
            key: lap_diagnostics[key]
            for key in (
                "total_laps",
                "fitted_laps",
                "compliant_laps",
                "non_compliant_laps",
                "shape_non_compliant_laps",
                "reason_counts",
                "warning_counts",
                "thresholds",
                "fastest_lap_with_position",
                "fastest_compliant_lap",
            )
        },
        "averaged_fastf1_polyline_vs_source": asdict(averaged_simplification),
        "polyline_vs_source": asdict(simp),
        "polyline_vs_fastf1": asdict(simplified_fit),
        "encoded_polyline": encoded,
        "averaged_fastf1_encoded_polyline": averaged_encoded,
    }
    return row, lap_event


def write_run_outputs(
    *,
    args: argparse.Namespace,
    paths: dict[str, Path],
    circuit_rows: list[dict[str, Any]],
    lap_rows: list[dict[str, Any]],
    manifest: dict[str, Any],
) -> None:
    if getattr(args, "dry_run", False):
        print("Dry run: outputs would be written to:")
        for path in paths.values():
            print(f"  {path}")
        return
    if not guard_output_targets(list(paths.values()), args.write_mode):
        return

    write_json(paths["circuit_analysis_json"], circuit_rows)
    write_json(paths["lap_diagnostics_json"], lap_rows)
    write_json(paths["manifest_json"], manifest)

    csv_rows = [flatten_for_csv(row) for row in circuit_rows]
    paths["circuit_analysis_csv"].parent.mkdir(parents=True, exist_ok=True)
    if csv_rows:
        with paths["circuit_analysis_csv"].open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(csv_rows[0].keys()), lineterminator="\n")
            writer.writeheader()
            writer.writerows(csv_rows)


def run_validate(args: argparse.Namespace) -> None:
    args.session = normalize_session(args.session)
    championship, schedule = prepare_context(args)
    round_index, circuit, event = resolve_validate_target(args, championship, schedule)
    event_name = str(event["EventName"])
    paths = output_paths(args, event_name=event_name)
    prov = provenance(command="validate", args=namespace_args(args))
    if args.dry_run:
        print(f"Resolved {args.year} {event_name} session {args.session}")
        print(f"Output directory: {paths['manifest_json'].parent}")
        return

    circuit_row, lap_row = analyze_event(args=args, round_index=round_index, circuit=circuit, event=event, provenance_payload=prov)
    manifest = artifact_manifest(
        run_mode="single-event",
        year=args.year,
        event_name=event_name,
        session_type=args.session,
        circuit_id=circuit_row.get("circuit_id"),
        thresholds=thresholds(args),
        outputs=relative_outputs(paths, Path.cwd()),
        provenance_payload=prov,
    )
    write_run_outputs(args=args, paths=paths, circuit_rows=[circuit_row], lap_rows=[lap_row], manifest=manifest)
    print(f"{args.year} {event_name} {args.session}: {circuit_row['analysis_status']}")
    print(f"Wrote {paths['manifest_json']}")


def run_batch(args: argparse.Namespace) -> None:
    args.session = normalize_session(args.session)
    championship, schedule = prepare_context(args)
    target_rounds = find_circuit_rounds(championship, schedule, None)
    if args.limit is not None:
        target_rounds = target_rounds[: args.limit]
    paths = output_paths(args, event_name=None, batch=True)
    prov = provenance(command="batch", args=namespace_args(args))
    if args.dry_run:
        print(f"Resolved {len(target_rounds)} events for {args.year} session {args.session}")
        print(f"Output directory: {paths['manifest_json'].parent}")
        return

    circuit_rows: list[dict[str, Any]] = []
    lap_rows: list[dict[str, Any]] = []
    for round_index, circuit, event in target_rounds:
        circuit_row, lap_row = analyze_event(
            args=args,
            round_index=round_index,
            circuit=circuit,
            event=event,
            provenance_payload=prov,
        )
        circuit_rows.append(circuit_row)
        lap_rows.append(lap_row)
        print(f"{round_index:02d} {event['EventName']}: {circuit_row['analysis_status']}")

    manifest = artifact_manifest(
        run_mode="batch",
        year=args.year,
        event_name=None,
        session_type=args.session,
        circuit_id=None,
        thresholds=thresholds(args),
        outputs=relative_outputs(paths, Path.cwd()),
        provenance_payload=prov,
    )
    write_run_outputs(args=args, paths=paths, circuit_rows=circuit_rows, lap_rows=lap_rows, manifest=manifest)
    print(f"Wrote {paths['manifest_json']}")


def run_schema_check(args: argparse.Namespace) -> None:
    for path in args.paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        validate_any_artifact(payload, allow_legacy=args.allow_legacy)
        print(f"ok {path}")


def run_fixture_demo(args: argparse.Namespace) -> None:
    paths = {
        "circuit_analysis_json": args.output_dir / "circuit-analysis.json",
        "circuit_analysis_csv": args.output_dir / "circuit-analysis.csv",
        "lap_diagnostics_json": args.output_dir / "lap-diagnostics.json",
        "manifest_json": args.output_dir / "artifact-manifest.json",
    }
    if not guard_output_targets(list(paths.values()), args.write_mode):
        return
    prov = provenance(command="fixture-demo", args=namespace_args(args))
    lap_record = {
        "driver": "TST",
        "lap_number": 1,
        "lap_time_ms": 90000,
        "is_accurate": True,
        "is_pit_lap": False,
        "position_samples": 4,
        "path_length_m": 40.0,
        "length_error_m": 0.0,
        "length_error_pct": 0.0,
        "normalized_position_samples": None,
        "normalized_path_length_m": None,
        "normalized_length_error_m": None,
        "normalized_length_error_pct": None,
        "normalization": None,
        "fit": {
            "direction": "forward",
            "start_offset_samples": 0,
            "sample_count": 4,
            "rmse_m": 0.0,
            "p50_m": 0.0,
            "p95_m": 0.0,
            "max_m": 0.0,
            "scale_m_per_fastf1_unit": 0.1,
            "rotation_degrees": 0.0,
        },
        "compliant": True,
        "reasons": [],
        "warnings": [],
        "year": 2099,
        "round": 1,
        "event_name": "Fixture Grand Prix",
        "session_type": "R",
        "lap_key": "2099-01-fixture-grand-prix-r-tst-lap-1",
    }
    lap_rows = [
        {
            "schema_version": SCHEMA_VERSION,
            "artifact_kind": "lap_diagnostics_event",
            "provenance": prov,
            "year": 2099,
            "session_type": "R",
            "round": 1,
            "event_name": "Fixture Grand Prix",
            "circuit_id": "fixture-circuit",
            "circuit_name": "Fixture Circuit",
            "total_laps": 1,
            "fitted_laps": 1,
            "compliant_laps": 1,
            "non_compliant_laps": 0,
            "shape_non_compliant_laps": 0,
            "reason_counts": {"compliant": 1},
            "warning_counts": {},
            "thresholds": {
                "length_tolerance_pct": 0.05,
                "rmse_threshold_m": 32.0,
                "p95_threshold_m": 75.0,
                "rmse_threshold_pct_of_length": 0.016,
                "p95_threshold_pct_of_length": 0.025,
                "reference_length_m": 40.0,
                "effective_rmse_threshold_m": 32.0,
                "effective_p95_threshold_m": 75.0,
            },
            "fastest_lap_with_position": lap_record,
            "fastest_compliant_lap": lap_record,
            "worst_shape_laps": [],
            "worst_fitted_laps": [lap_record],
        }
    ]
    circuit_rows = [
        {
            "schema_version": SCHEMA_VERSION,
            "artifact_kind": "circuit_analysis_row",
            "provenance": prov,
            "validation_complete": True,
            "analysis_status": "complete",
            "incomplete_reason": None,
            "year": 2099,
            "round": 1,
            "event_name": "Fixture Grand Prix",
            "session_type": "R",
            "fastf1_location": "Fixture",
            "circuit_id": "fixture-circuit",
            "circuit_name": "Fixture Circuit",
            "repo_location": "Fixture",
            "declared_length_m": 40.0,
            "fastf1_driver": "TST",
            "fastf1_lap": 1,
            "fastf1_lap_key": "2099-01-fixture-grand-prix-r-tst-lap-1",
            "fastf1_points": 4,
            "fastf1_path_length_m": 40.0,
            "fastf1_raw_path_length_m": 40.0,
            "fastf1_normalization": None,
            "repo_vs_fastf1": lap_record["fit"],
            "averaged_fastf1_laps": [{"driver": "TST", "lap": 1, "lap_key": lap_record["lap_key"], "path_length_m": 40.0, "raw_path_length_m": 40.0, "normalization": None, "length_error_m": 0.0, "rmse_m": 0.0, "p95_m": 0.0}],
            "repo_vs_fastf1_average": {"sample_count": 4, "rmse_m": 0.0, "p50_m": 0.0, "p95_m": 0.0, "max_m": 0.0},
            "lap_compliance_summary": {key: lap_rows[0][key] for key in ("total_laps", "fitted_laps", "compliant_laps", "non_compliant_laps", "shape_non_compliant_laps", "reason_counts", "warning_counts", "thresholds", "fastest_lap_with_position", "fastest_compliant_lap")},
            "averaged_fastf1_polyline_vs_source": {"source_points": 4, "simplified_points": 4, "encoded_chars": 12, "tolerance_m": 1.0, "rmse_m": 0.0, "p95_m": 0.0, "max_m": 0.0, "source_length_m": 40.0, "simplified_length_m": 40.0, "length_delta_m": 0.0, "length_delta_pct": 0.0},
            "polyline_vs_source": {"source_points": 4, "simplified_points": 4, "encoded_chars": 12, "tolerance_m": 1.0, "rmse_m": 0.0, "p95_m": 0.0, "max_m": 0.0, "source_length_m": 40.0, "simplified_length_m": 40.0, "length_delta_m": 0.0, "length_delta_pct": 0.0},
            "polyline_vs_fastf1": lap_record["fit"],
            "encoded_polyline": "fixture",
            "averaged_fastf1_encoded_polyline": "fixture",
        }
    ]
    manifest = artifact_manifest(
        run_mode="fixture",
        year=2099,
        event_name="Fixture Grand Prix",
        session_type="R",
        circuit_id="fixture-circuit",
        thresholds=lap_rows[0]["thresholds"],
        outputs=relative_outputs(paths, Path.cwd()),
        provenance_payload=prov,
    )
    write_run_outputs(args=args, paths=paths, circuit_rows=circuit_rows, lap_rows=lap_rows, manifest=manifest)
    print(f"Wrote fixture demo to {args.output_dir}")


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.command is None:
        build_parser().print_help()
        return
    command = args.command
    if command == "validate":
        run_validate(args)
    elif command == "batch":
        run_batch(args)
    elif command == "schema-check":
        run_schema_check(args)
    elif command == "fixture-demo":
        run_fixture_demo(args)
    else:
        build_parser().print_help()


if __name__ == "__main__":
    main()
