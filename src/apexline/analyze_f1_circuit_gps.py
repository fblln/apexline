"""Compatibility exports for legacy Apexline scripts."""

from .cli import main
from .fastf1_support import analyze_lap_compliance, lap_position_points, load_fastf1_lap, load_session, score_fastf1_laps
from .geometry import (
    average_fitted_laps,
    closed_path,
    direct_line_stats,
    encode_polyline,
    fit_aligned_samples,
    latlon_to_xy,
    path_length,
    percentile,
    projection_origin,
    rdp,
    resample_closed,
    rotate_samples,
    similarity_fit,
    simplification_stats,
    validate_shape,
    xy_to_latlon,
)
from .models import DirectLineStats, FastF1Candidate, FastF1Lap, FitStats, LapDiagnostic, ScoredFastF1Lap, SimplificationStats
from .sources import ensure_f1_circuits_repo, find_circuit_rounds, flatten_for_csv, load_circuit_latlon, load_json, normalize_key, value_to_ms

