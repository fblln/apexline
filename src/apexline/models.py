from __future__ import annotations

from dataclasses import dataclass


LatLon = tuple[float, float]
XY = tuple[float, float]


@dataclass(frozen=True)
class FitStats:
    direction: str
    start_offset_samples: int
    sample_count: int
    rmse_m: float
    p50_m: float
    p95_m: float
    max_m: float
    scale_m_per_fastf1_unit: float
    rotation_degrees: float


@dataclass(frozen=True)
class SimplificationStats:
    source_points: int
    simplified_points: int
    encoded_chars: int
    tolerance_m: float
    rmse_m: float
    p95_m: float
    max_m: float
    source_length_m: float
    simplified_length_m: float
    length_delta_m: float
    length_delta_pct: float


@dataclass(frozen=True)
class LapNormalization:
    original_points: int
    normalized_points: int
    original_path_length_m: float
    normalized_path_length_m: float
    target_length_m: float
    trimmed_prefix_m: float
    trimmed_suffix_m: float
    endpoint_gap_m: float


@dataclass(frozen=True)
class FastF1Lap:
    driver: str
    lap_number: int
    points: list[XY]
    path_length_m: float
    lap_time_ms: int | None = None
    raw_path_length_m: float | None = None
    normalization: LapNormalization | None = None


@dataclass(frozen=True)
class FastF1Candidate:
    lap: FastF1Lap
    length_error_m: float


@dataclass(frozen=True)
class ScoredFastF1Lap:
    lap: FastF1Lap
    fit: FitStats
    length_error_m: float


@dataclass(frozen=True)
class DirectLineStats:
    sample_count: int
    rmse_m: float
    p50_m: float
    p95_m: float
    max_m: float


@dataclass(frozen=True)
class LapDiagnostic:
    driver: str
    lap_number: int
    lap_time_ms: int | None
    is_accurate: bool
    is_pit_lap: bool
    position_samples: int
    path_length_m: float | None
    length_error_m: float | None
    length_error_pct: float | None
    normalized_position_samples: int | None
    normalized_path_length_m: float | None
    normalized_length_error_m: float | None
    normalized_length_error_pct: float | None
    normalization: LapNormalization | None
    fit: FitStats | None
    compliant: bool
    reasons: list[str]
    warnings: list[str]
