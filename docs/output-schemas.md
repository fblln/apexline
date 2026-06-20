# Output Schemas

Apexline writes versioned JSON artifacts with `schema_version: "1.0.0"` in new
CLI runs. Downstream consumers should validate both `schema_version` and
`artifact_kind` before importing. Single-session outputs default to
`data/<year>/<event>/<session>/`.

Machine-readable JSON Schemas for every public artifact kind live in
[`schemas/`](../schemas/).

## Stable IDs

Per-event and per-lap records use these stable identifiers:

| Field | Meaning |
|---|---|
| `year` | championship season |
| `round` | event round number in the championship |
| `event_name` | FastF1 event name |
| `session_type` | FastF1 session code, usually `R` |
| `driver` | three-letter driver code |
| `lap_number` | session lap number |
| `lap_key` | deterministic Apexline lap identifier |

`lap_key` format:

```text
{year}-{round:02d}-{event-slug}-{session_type}-{driver}-lap-{lap_number}
```

## Units And Thresholds

Metrics are reported in meters unless otherwise noted:

| Field | Unit |
|---|---|
| `rmse_m` | meters |
| `p50_m` | meters |
| `p95_m` | meters |
| `max_m` | meters |
| `path_length_m` | meters |
| `length_error_m` | meters |
| `length_error_pct` | fraction of reference path length |
| `normalized_path_length_m` | meters after overlap trimming, or null |
| `normalized_length_error_m` | meters after overlap trimming, or null |
| `normalized_length_error_pct` | fraction after overlap trimming, or null |
| `scale_m_per_fastf1_unit` | meters per FastF1 local XY unit |

Default thresholds in the CLI:

| Threshold | Default |
|---|---:|
| `length_tolerance_pct` | `0.05` |
| `rmse_threshold_m` | `32.0` |
| `p95_threshold_m` | `75.0` |
| `rmse_threshold_pct_of_length` | `0.016` |
| `p95_threshold_pct_of_length` | `0.025` |
| `min_position_samples` | `100` |

The effective shape thresholds are the greater of the fixed meter floor and
the circuit-length proportion. Generated diagnostics record the oracle length
and both effective thresholds for reproducibility.

Known rejection reasons:

- `fastf1_inaccurate`
- `pit_lap`
- `too_few_position_samples`
- `path_length_outlier`
- `shape_rmse_over_threshold`
- `shape_p95_over_threshold`
- `no_position_data`

## Artifact Kinds

### `circuit_analysis_row`

One row per event/session in `circuit-analysis.json`.

Required top-level fields:

- `schema_version`
- `artifact_kind`
- `provenance`
- `validation_complete`
- `analysis_status`
- `year`
- `round`
- `event_name`
- `session_type`
- `circuit_id`
- `circuit_name`
- `fastf1_driver`
- `fastf1_lap`
- `repo_vs_fastf1`
- `repo_vs_fastf1_average`
- `lap_compliance_summary`
- `polyline_vs_source`
- `polyline_vs_fastf1`
- `encoded_polyline`

### `lap_diagnostics_event`

One row per event/session in `lap-diagnostics.json`.

Required top-level fields:

- `schema_version`
- `artifact_kind`
- `provenance`
- `year`
- `round`
- `event_name`
- `session_type`
- `circuit_id`
- `circuit_name`
- `total_laps`
- `fitted_laps`
- `compliant_laps`
- `non_compliant_laps`
- `shape_non_compliant_laps`
- `reason_counts`
- `thresholds`
- `fastest_lap_with_position`
- `fastest_compliant_lap`
- `worst_shape_laps`
- `worst_fitted_laps`

Embedded lap records include the stable lap identifiers, raw path length, any
overlap-normalized path length, and fit metrics when a lap passed the pre-fit
checks. `normalization` records how much prefix/suffix distance was trimmed from
an over-long lap before shape matching.

### `rejected_lap_gallery`

JSON sidecar metadata for `docs/assets/rejected-laps-<year>/*.svg`.

Required top-level fields:

- `schema_version`
- `artifact_kind`
- `year`
- `event_name`
- `round`
- `session_type`
- `circuit_id`
- `circuit_name`
- `thresholds`
- `generation_provenance`
- `reference_length_m`
- `anchor`
- `max_render_points`
- `rendering_note`
- `rejected_laps`

### `artifact_manifest`

One manifest per run in `artifact-manifest.json`.

Required top-level fields:

- `schema_version`
- `artifact_kind`
- `run_mode`
- `year`
- `event_name`
- `session_type`
- `circuit_id`
- `thresholds`
- `outputs`
- `provenance`

## Validation

`src/apexline/schemas.py` contains the repo's schema validators. The test suite
uses those validators against the checked-in example artifacts.
