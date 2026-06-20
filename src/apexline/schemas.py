from __future__ import annotations

from typing import Any


SCHEMA_VERSION = "1.0.0"
KNOWN_REJECTION_REASONS = {
    "compliant",
    "pit_lap",
    "too_few_position_samples",
    "path_length_outlier",
    "shape_rmse_over_threshold",
    "shape_p95_over_threshold",
    "no_position_data",
}
KNOWN_WARNING_REASONS = {"fastf1_inaccurate"}


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a JSON array")
    return value


def _require_keys(value: dict[str, Any], label: str, required: list[str]) -> None:
    missing = [key for key in required if key not in value]
    if missing:
        raise ValueError(f"{label} is missing required keys: {', '.join(missing)}")


def _validate_reason_counts(reason_counts: Any, label: str) -> None:
    mapping = _require_mapping(reason_counts, label)
    for reason, count in mapping.items():
        if reason not in KNOWN_REJECTION_REASONS:
            raise ValueError(f"{label}.{reason} is not a recognized rejection reason")
        if not isinstance(count, int):
            raise ValueError(f"{label}.{reason} must be an integer")


def _validate_warning_counts(warning_counts: Any, label: str) -> None:
    mapping = _require_mapping(warning_counts, label)
    for warning, count in mapping.items():
        if warning not in KNOWN_WARNING_REASONS:
            raise ValueError(f"{label}.{warning} is not a recognized warning")
        if not isinstance(count, int):
            raise ValueError(f"{label}.{warning} must be an integer")


def _validate_thresholds(thresholds: Any, label: str) -> None:
    mapping = _require_mapping(thresholds, label)
    _require_keys(
        mapping,
        label,
        [
            "length_tolerance_pct",
            "rmse_threshold_m",
            "p95_threshold_m",
            "rmse_threshold_pct_of_length",
            "p95_threshold_pct_of_length",
            "reference_length_m",
            "effective_rmse_threshold_m",
            "effective_p95_threshold_m",
        ],
    )


def validate_lap_diagnostic_record(record: Any, *, allow_legacy: bool = False) -> None:
    value = _require_mapping(record, "lap_diagnostic_record")
    required = [
        "driver",
        "lap_number",
        "lap_time_ms",
        "is_accurate",
        "is_pit_lap",
        "position_samples",
        "path_length_m",
        "length_error_m",
        "length_error_pct",
        "fit",
        "compliant",
        "reasons",
    ]
    if not allow_legacy:
        required.extend(["year", "round", "event_name", "session_type", "lap_key"])
        required.append("warnings")
        required.extend(
            [
                "normalized_position_samples",
                "normalized_path_length_m",
                "normalized_length_error_m",
                "normalized_length_error_pct",
                "normalization",
            ]
        )
    _require_keys(value, "lap_diagnostic_record", required)
    reasons = _require_list(value["reasons"], "lap_diagnostic_record.reasons")
    for reason in reasons:
        if reason not in KNOWN_REJECTION_REASONS:
            raise ValueError(f"lap_diagnostic_record.reasons contains unknown value {reason!r}")
    if "warnings" in value:
        warnings = _require_list(value["warnings"], "lap_diagnostic_record.warnings")
        for warning in warnings:
            if warning not in KNOWN_WARNING_REASONS:
                raise ValueError(f"lap_diagnostic_record.warnings contains unknown value {warning!r}")
    if value["fit"] is not None:
        fit = _require_mapping(value["fit"], "lap_diagnostic_record.fit")
        _require_keys(
            fit,
            "lap_diagnostic_record.fit",
            [
                "direction",
                "start_offset_samples",
                "sample_count",
                "rmse_m",
                "p50_m",
                "p95_m",
                "max_m",
                "scale_m_per_fastf1_unit",
                "rotation_degrees",
            ],
        )


def validate_lap_diagnostics_event(record: Any, *, allow_legacy: bool = False) -> None:
    value = _require_mapping(record, "lap_diagnostics_event")
    if not allow_legacy:
        _require_keys(value, "lap_diagnostics_event", ["schema_version", "artifact_kind", "year", "session_type", "provenance"])
        if value["schema_version"] != SCHEMA_VERSION:
            raise ValueError(f"unexpected schema version {value['schema_version']!r}")
        if value["artifact_kind"] != "lap_diagnostics_event":
            raise ValueError(f"unexpected artifact kind {value['artifact_kind']!r}")
    _require_keys(
        value,
        "lap_diagnostics_event",
        [
            "round",
            "event_name",
            "circuit_id",
            "circuit_name",
            "total_laps",
            "fitted_laps",
            "compliant_laps",
            "non_compliant_laps",
            "shape_non_compliant_laps",
            "reason_counts",
            "thresholds",
            "fastest_lap_with_position",
            "fastest_compliant_lap",
            "worst_shape_laps",
            "worst_fitted_laps",
        ],
    )
    _validate_reason_counts(value["reason_counts"], "lap_diagnostics_event.reason_counts")
    if not allow_legacy:
        _require_keys(value, "lap_diagnostics_event", ["warning_counts"])
    if "warning_counts" in value:
        _validate_warning_counts(value["warning_counts"], "lap_diagnostics_event.warning_counts")
    _validate_thresholds(value["thresholds"], "lap_diagnostics_event.thresholds")
    if value["fastest_lap_with_position"] is not None:
        validate_lap_diagnostic_record(value["fastest_lap_with_position"], allow_legacy=allow_legacy)
    if value["fastest_compliant_lap"] is not None:
        validate_lap_diagnostic_record(value["fastest_compliant_lap"], allow_legacy=allow_legacy)
    for item in _require_list(value["worst_shape_laps"], "lap_diagnostics_event.worst_shape_laps"):
        validate_lap_diagnostic_record(item, allow_legacy=allow_legacy)
    for item in _require_list(value["worst_fitted_laps"], "lap_diagnostics_event.worst_fitted_laps"):
        validate_lap_diagnostic_record(item, allow_legacy=allow_legacy)


def validate_lap_diagnostics_season(records: Any, *, allow_legacy: bool = False) -> None:
    for item in _require_list(records, "lap_diagnostics_season"):
        validate_lap_diagnostics_event(item, allow_legacy=allow_legacy)


def validate_circuit_analysis_row(record: Any, *, allow_legacy: bool = False) -> None:
    value = _require_mapping(record, "circuit_analysis_row")
    if not allow_legacy:
        _require_keys(
            value,
            "circuit_analysis_row",
            ["schema_version", "artifact_kind", "year", "session_type", "provenance", "validation_complete", "analysis_status"],
        )
        if value["schema_version"] != SCHEMA_VERSION:
            raise ValueError(f"unexpected schema version {value['schema_version']!r}")
        if value["artifact_kind"] != "circuit_analysis_row":
            raise ValueError(f"unexpected artifact kind {value['artifact_kind']!r}")
    _require_keys(
        value,
        "circuit_analysis_row",
        [
            "round",
            "event_name",
            "fastf1_location",
            "circuit_id",
            "circuit_name",
            "repo_location",
            "declared_length_m",
            "fastf1_driver",
            "fastf1_lap",
            "fastf1_points",
            "fastf1_path_length_m",
            "repo_vs_fastf1",
            "repo_vs_fastf1_average",
            "lap_compliance_summary",
            "averaged_fastf1_polyline_vs_source",
            "polyline_vs_source",
            "polyline_vs_fastf1",
            "encoded_polyline",
        ],
    )
    if value["repo_vs_fastf1"] is not None:
        _require_mapping(value["repo_vs_fastf1"], "circuit_analysis_row.repo_vs_fastf1")
    if value["repo_vs_fastf1_average"] is not None:
        _require_mapping(value["repo_vs_fastf1_average"], "circuit_analysis_row.repo_vs_fastf1_average")
    compliance_summary = _require_mapping(
        value["lap_compliance_summary"],
        "circuit_analysis_row.lap_compliance_summary",
    )
    if not allow_legacy:
        _require_keys(
            compliance_summary,
            "circuit_analysis_row.lap_compliance_summary",
            ["reason_counts", "warning_counts"],
        )
    if "reason_counts" in compliance_summary:
        _validate_reason_counts(
            compliance_summary["reason_counts"],
            "circuit_analysis_row.lap_compliance_summary.reason_counts",
        )
    if "warning_counts" in compliance_summary:
        _validate_warning_counts(
            compliance_summary["warning_counts"],
            "circuit_analysis_row.lap_compliance_summary.warning_counts",
        )


def validate_circuit_analysis(records: Any, *, allow_legacy: bool = False) -> None:
    for item in _require_list(records, "circuit_analysis"):
        validate_circuit_analysis_row(item, allow_legacy=allow_legacy)


def validate_rejected_lap_gallery(record: Any, *, allow_legacy: bool = False) -> None:
    value = _require_mapping(record, "rejected_lap_gallery")
    if not allow_legacy:
        _require_keys(value, "rejected_lap_gallery", ["schema_version", "artifact_kind"])
        if value["schema_version"] != SCHEMA_VERSION:
            raise ValueError(f"unexpected schema version {value['schema_version']!r}")
        if value["artifact_kind"] != "rejected_lap_gallery":
            raise ValueError(f"unexpected artifact kind {value['artifact_kind']!r}")
    required = [
        "year",
        "event_name",
        "round",
        "session_type",
        "circuit_id",
        "circuit_name",
        "thresholds",
        "generation_provenance",
        "reference_length_m",
        "anchor",
        "max_render_points",
        "rendering_note",
        "rejected_laps",
    ]
    _require_keys(value, "rejected_lap_gallery", required)
    _require_mapping(value["thresholds"], "rejected_lap_gallery.thresholds")
    _require_mapping(value["generation_provenance"], "rejected_lap_gallery.generation_provenance")
    for lap in _require_list(value["rejected_laps"], "rejected_lap_gallery.rejected_laps"):
        lap_value = _require_mapping(lap, "rejected_lap")
        _require_keys(
            lap_value,
            "rejected_lap",
            [
                "driver",
                "lap_number",
                "lap_time_ms",
                "reasons",
                "path_length_m",
                "length_error_pct",
                "fit_rmse_m",
                "fit_p95_m",
            ],
        )
        if not allow_legacy:
            _require_keys(lap_value, "rejected_lap", ["warnings"])
        reasons = _require_list(lap_value["reasons"], "rejected_lap.reasons")
        for reason in reasons:
            if reason not in KNOWN_REJECTION_REASONS or reason == "compliant":
                raise ValueError(f"rejected_lap.reasons contains unknown value {reason!r}")
        if "warnings" in lap_value:
            warnings = _require_list(lap_value["warnings"], "rejected_lap.warnings")
            for warning in warnings:
                if warning not in KNOWN_WARNING_REASONS:
                    raise ValueError(f"rejected_lap.warnings contains unknown value {warning!r}")


def validate_artifact_manifest(record: Any, *, allow_legacy: bool = False) -> None:
    value = _require_mapping(record, "artifact_manifest")
    if not allow_legacy:
        _require_keys(value, "artifact_manifest", ["schema_version", "artifact_kind"])
        if value["schema_version"] != SCHEMA_VERSION:
            raise ValueError(f"unexpected schema version {value['schema_version']!r}")
        if value["artifact_kind"] != "artifact_manifest":
            raise ValueError(f"unexpected artifact kind {value['artifact_kind']!r}")
    _require_keys(
        value,
        "artifact_manifest",
        [
            "run_mode",
            "year",
            "event_name",
            "session_type",
            "circuit_id",
            "thresholds",
            "outputs",
            "provenance",
        ],
    )
    _require_mapping(value["thresholds"], "artifact_manifest.thresholds")
    _require_mapping(value["outputs"], "artifact_manifest.outputs")
    _require_mapping(value["provenance"], "artifact_manifest.provenance")


def validate_any_artifact(payload: Any, *, allow_legacy: bool = False) -> None:
    if isinstance(payload, list):
        if not payload:
            return
        first = _require_mapping(payload[0], "artifact[0]")
        kind = first.get("artifact_kind")
        if kind == "circuit_analysis_row" or (allow_legacy and "encoded_polyline" in first):
            validate_circuit_analysis(payload, allow_legacy=allow_legacy)
            return
        if kind == "lap_diagnostics_event" or (allow_legacy and "reason_counts" in first):
            validate_lap_diagnostics_season(payload, allow_legacy=allow_legacy)
            return
        raise ValueError(f"cannot infer artifact kind from list payload: {kind!r}")

    value = _require_mapping(payload, "artifact")
    kind = value.get("artifact_kind")
    if kind == "artifact_manifest":
        validate_artifact_manifest(value, allow_legacy=allow_legacy)
        return
    if kind == "rejected_lap_gallery" or (allow_legacy and "rejected_laps" in value):
        validate_rejected_lap_gallery(value, allow_legacy=allow_legacy)
        return
    if kind == "lap_diagnostics_event":
        validate_lap_diagnostics_event(value, allow_legacy=allow_legacy)
        return
    if kind == "circuit_analysis_row":
        validate_circuit_analysis_row(value, allow_legacy=allow_legacy)
        return
    raise ValueError(f"cannot infer artifact kind: {kind!r}")
