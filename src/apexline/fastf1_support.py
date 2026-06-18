from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from .geometry import closed_path, path_length, validate_shape
from .models import FastF1Candidate, FastF1Lap, FitStats, LapDiagnostic, ScoredFastF1Lap, XY
from .sources import value_to_ms


def get_fastf1() -> Any:
    try:
        import fastf1  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:
        raise RuntimeError("FastF1 is not installed") from exc
    return fastf1


def load_session(year: int, event: str, cache_dir: Path, session_name: str = "R") -> Any:
    fastf1 = get_fastf1()
    cache_dir.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(str(cache_dir))
    try:
        session = fastf1.get_session(year, event, session_name)
        session.load(laps=True, telemetry=True, weather=False, messages=False)
    except Exception as exc:
        raise RuntimeError(
            f"FastF1 could not load {year} {event} session {session_name}. "
            "Check that the session exists and that FastF1 cache/network access is available."
        ) from exc
    return session


def lap_position_points(lap: Any) -> list[XY]:
    try:
        position = lap.get_pos_data()[["X", "Y"]].dropna()
    except Exception:
        return []

    points: list[XY] = []
    for row in position.itertuples():
        point = (float(row.X), float(row.Y))
        if not points or point != points[-1]:
            points.append(point)
    return points


def score_fastf1_laps(
    year: int,
    event: str,
    cache_dir: Path,
    session_name: str,
    preferred_driver: str | None,
    reference_xy: list[XY],
    validation_samples: int,
    validation_offset_step: int,
    max_shape_candidates: int,
) -> list[ScoredFastF1Lap]:
    session = load_session(year, event, cache_dir, session_name)
    driver_codes: list[str] = []
    if preferred_driver:
        driver_codes.append(preferred_driver.upper())

    for driver_ref in getattr(session, "drivers", []):
        try:
            code = str(session.get_driver(driver_ref).get("Abbreviation")).upper()
        except Exception:
            code = str(driver_ref).upper()
        if code not in driver_codes:
            driver_codes.append(code)

    candidates: list[FastF1Candidate] = []
    reference_length_m = path_length(reference_xy)
    for driver in driver_codes:
        laps = session.laps.pick_drivers(driver)
        for _, lap in laps.iterlaps():
            if not bool(lap.get("IsAccurate")):
                continue
            if str(lap.get("PitOutTime")) != "NaT" or str(lap.get("PitInTime")) != "NaT":
                continue

            points = lap_position_points(lap)
            if len(points) < 100:
                continue

            path_length_m = path_length(closed_path(points)) * 0.1
            if reference_length_m and abs(path_length_m - reference_length_m) / reference_length_m > 0.15:
                continue

            candidate = FastF1Lap(
                driver=driver,
                lap_number=int(lap.get("LapNumber")),
                points=points,
                path_length_m=path_length_m,
                lap_time_ms=value_to_ms(lap.get("LapTime")),
            )
            candidates.append(
                FastF1Candidate(
                    lap=candidate,
                    length_error_m=abs(path_length_m - reference_length_m),
                )
            )

        if preferred_driver and candidates:
            break

    if not candidates:
        raise RuntimeError(f"could not find a clean FastF1 lap for {year} {event}")

    scored: list[ScoredFastF1Lap] = []
    for candidate in sorted(candidates, key=lambda item: item.length_error_m)[:max_shape_candidates]:
        fit = validate_shape(
            fastf1_xy=candidate.lap.points,
            gps_xy=reference_xy,
            sample_count=validation_samples,
            offset_step=validation_offset_step,
        )
        scored.append(
            ScoredFastF1Lap(
                lap=candidate.lap,
                fit=fit,
                length_error_m=candidate.length_error_m,
            )
        )

    if not scored:
        raise RuntimeError(f"could not score FastF1 candidate laps for {year} {event}")
    return sorted(scored, key=lambda item: item.fit.rmse_m)


def load_fastf1_lap(
    year: int,
    event: str,
    cache_dir: Path,
    session_name: str,
    preferred_driver: str | None,
    reference_xy: list[XY],
    validation_samples: int,
    validation_offset_step: int,
    max_shape_candidates: int,
) -> tuple[FastF1Lap, FitStats]:
    best = score_fastf1_laps(
        year=year,
        event=event,
        cache_dir=cache_dir,
        session_name=session_name,
        preferred_driver=preferred_driver,
        reference_xy=reference_xy,
        validation_samples=validation_samples,
        validation_offset_step=validation_offset_step,
        max_shape_candidates=max_shape_candidates,
    )[0]
    return best.lap, best.fit


def lap_key(year: int, round_index: int, event_name: str, session_name: str, driver: str, lap_number: int) -> str:
    event_slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in event_name).strip("-")
    return f"{year}-{round_index:02d}-{event_slug}-{session_name.lower()}-{driver.lower()}-lap-{lap_number}"


def classify_lap(
    *,
    driver: str,
    lap_number: int,
    lap_time_ms: int | None,
    is_accurate: bool,
    is_pit_lap: bool,
    points: list[XY],
    reference_xy: list[XY],
    validation_samples: int,
    validation_offset_step: int,
    length_tolerance_pct: float,
    rmse_threshold_m: float,
    p95_threshold_m: float,
    min_position_samples: int,
) -> LapDiagnostic:
    reasons: list[str] = []
    if not is_accurate:
        reasons.append("fastf1_inaccurate")
    if is_pit_lap:
        reasons.append("pit_lap")
    if lap_time_ms is None:
        reasons.append("missing_lap_time")

    if not points:
        reasons.append("no_position_data")
        return LapDiagnostic(
            driver=driver,
            lap_number=lap_number,
            lap_time_ms=lap_time_ms,
            is_accurate=is_accurate,
            is_pit_lap=is_pit_lap,
            position_samples=0,
            path_length_m=None,
            length_error_m=None,
            length_error_pct=None,
            fit=None,
            compliant=False,
            reasons=reasons,
        )

    reference_length_m = path_length(reference_xy)
    position_samples = len(points)
    if position_samples < min_position_samples:
        reasons.append("too_few_position_samples")

    path_length_m = path_length(closed_path(points)) * 0.1
    length_error_m = path_length_m - reference_length_m
    length_error_pct = length_error_m / reference_length_m if reference_length_m else None
    if length_error_pct is not None and abs(length_error_pct) > length_tolerance_pct:
        reasons.append("path_length_outlier")

    fit: FitStats | None = None
    if (
        is_accurate
        and not is_pit_lap
        and position_samples >= min_position_samples
        and length_error_pct is not None
        and abs(length_error_pct) <= length_tolerance_pct
    ):
        fit = validate_shape(
            fastf1_xy=points,
            gps_xy=reference_xy,
            sample_count=validation_samples,
            offset_step=validation_offset_step,
        )
        if fit.rmse_m > rmse_threshold_m:
            reasons.append("shape_rmse_over_threshold")
        if fit.p95_m > p95_threshold_m:
            reasons.append("shape_p95_over_threshold")

    return LapDiagnostic(
        driver=driver,
        lap_number=lap_number,
        lap_time_ms=lap_time_ms,
        is_accurate=is_accurate,
        is_pit_lap=is_pit_lap,
        position_samples=position_samples,
        path_length_m=path_length_m,
        length_error_m=length_error_m,
        length_error_pct=length_error_pct,
        fit=fit,
        compliant=not reasons,
        reasons=reasons,
    )


def analyze_lap_compliance(
    *,
    year: int,
    round_index: int,
    event: str,
    cache_dir: Path,
    session_name: str,
    reference_xy: list[XY],
    validation_samples: int,
    validation_offset_step: int,
    length_tolerance_pct: float,
    rmse_threshold_m: float,
    p95_threshold_m: float,
    min_position_samples: int,
) -> dict[str, Any]:
    session = load_session(year, event, cache_dir, session_name)
    diagnostics: list[LapDiagnostic] = []

    for driver_ref in getattr(session, "drivers", []):
        try:
            driver = str(session.get_driver(driver_ref).get("Abbreviation")).upper()
        except Exception:
            driver = str(driver_ref).upper()

        laps = session.laps.pick_drivers(driver)
        for _, lap in laps.iterlaps():
            lap_number = int(lap.get("LapNumber"))
            lap_time_ms = value_to_ms(lap.get("LapTime"))
            is_accurate = bool(lap.get("IsAccurate"))
            is_pit_lap = str(lap.get("PitOutTime")) != "NaT" or str(lap.get("PitInTime")) != "NaT"
            points = lap_position_points(lap)
            diagnostics.append(
                classify_lap(
                    driver=driver,
                    lap_number=lap_number,
                    lap_time_ms=lap_time_ms,
                    is_accurate=is_accurate,
                    is_pit_lap=is_pit_lap,
                    points=points,
                    reference_xy=reference_xy,
                    validation_samples=validation_samples,
                    validation_offset_step=validation_offset_step,
                    length_tolerance_pct=length_tolerance_pct,
                    rmse_threshold_m=rmse_threshold_m,
                    p95_threshold_m=p95_threshold_m,
                    min_position_samples=min_position_samples,
                )
            )

    reason_counts: dict[str, int] = {}
    for diagnostic in diagnostics:
        if diagnostic.compliant:
            reason_counts["compliant"] = reason_counts.get("compliant", 0) + 1
        for reason in diagnostic.reasons:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

    fitted = [diag for diag in diagnostics if diag.fit is not None]
    compliant = [diag for diag in diagnostics if diag.compliant]
    fastest_with_position = min(
        (
            diag
            for diag in diagnostics
            if diag.lap_time_ms is not None and diag.position_samples >= min_position_samples and not diag.is_pit_lap
        ),
        key=lambda diag: diag.lap_time_ms,
        default=None,
    )
    fastest_compliant = min(
        (diag for diag in compliant if diag.lap_time_ms is not None),
        key=lambda diag: diag.lap_time_ms,
        default=None,
    )

    shape_non_compliant = [
        diag
        for diag in fitted
        if "shape_rmse_over_threshold" in diag.reasons or "shape_p95_over_threshold" in diag.reasons
    ]
    worst_shape = sorted(
        shape_non_compliant,
        key=lambda diag: diag.fit.rmse_m if diag.fit is not None else -1,
        reverse=True,
    )[:10]
    worst_fitted = sorted(
        fitted,
        key=lambda diag: diag.fit.rmse_m if diag.fit is not None else -1,
        reverse=True,
    )[:10]

    def diag_to_dict(diag: LapDiagnostic | None) -> dict[str, Any] | None:
        if diag is None:
            return None
        data = asdict(diag)
        data["fit"] = asdict(diag.fit) if diag.fit is not None else None
        data["year"] = year
        data["round"] = round_index
        data["event_name"] = event
        data["session_type"] = session_name
        data["lap_key"] = lap_key(year, round_index, event, session_name, diag.driver, diag.lap_number)
        return data

    return {
        "total_laps": len(diagnostics),
        "fitted_laps": len(fitted),
        "compliant_laps": len(compliant),
        "non_compliant_laps": len(diagnostics) - len(compliant),
        "shape_non_compliant_laps": len(shape_non_compliant),
        "reason_counts": dict(sorted(reason_counts.items())),
        "thresholds": {
            "length_tolerance_pct": length_tolerance_pct,
            "rmse_threshold_m": rmse_threshold_m,
            "p95_threshold_m": p95_threshold_m,
            "min_position_samples": min_position_samples,
            "validation_samples": validation_samples,
            "validation_offset_step": validation_offset_step,
        },
        "fastest_lap_with_position": diag_to_dict(fastest_with_position),
        "fastest_compliant_lap": diag_to_dict(fastest_compliant),
        "worst_shape_laps": [diag_to_dict(diag) for diag in worst_shape],
        "worst_fitted_laps": [diag_to_dict(diag) for diag in worst_fitted],
    }
