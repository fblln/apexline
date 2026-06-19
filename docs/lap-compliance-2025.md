# 2025 lap compliance summary

Good laps are laps that pass Apexline's oracle-shape evidence checks.
Bad laps are laps rejected for at least one reason such as FastF1
`IsAccurate == False`, pit in/out, missing time, too few position
samples, path-length outlier, or shape residual over threshold.

Reason counts are not mutually exclusive: one bad lap can be both a
pit lap and FastF1-inaccurate.

## Season totals

| Metric | Value |
|---|---:|
| Circuits | 24 |
| Total laps inspected | 26,689 |
| Fitted laps | 23,042 |
| Good laps | 21,119 (79.1%) |
| Bad laps | 5,570 (20.9%) |
| Shape-threshold bad laps | 1,923 |

## Rejection signals

| Reason | Count |
|---|---:|
| `fastf1_inaccurate` | 3,646 |
| `shape_rmse_over_threshold` | 1,923 |
| `pit_lap` | 1,625 |
| `shape_p95_over_threshold` | 701 |
| `missing_lap_time` | 352 |
| `path_length_outlier` | 45 |
| `too_few_position_samples` | 19 |

## Circuit table

| Round | Event | Good | Bad | Total | Good % | Shape Bad | Top rejection signals |
|---:|---|---:|---:|---:|---:|---:|---|
| 1 | Australian Grand Prix | 568 | 359 | 927 | 61.3% | 0 | `fastf1_inaccurate` 359, `pit_lap` 132, `missing_lap_time` 69 |
| 2 | Chinese Grand Prix | 995 | 70 | 1,065 | 93.4% | 0 | `fastf1_inaccurate` 70, `pit_lap` 52 |
| 3 | Japanese Grand Prix | 997 | 62 | 1,059 | 94.1% | 0 | `fastf1_inaccurate` 62, `pit_lap` 42 |
| 4 | Bahrain Grand Prix | 942 | 186 | 1,128 | 83.5% | 10 | `fastf1_inaccurate` 176, `pit_lap` 84, `missing_lap_time` 13 |
| 5 | Saudi Arabian Grand Prix | 476 | 422 | 898 | 53.0% | 334 | `shape_rmse_over_threshold` 334, `fastf1_inaccurate` 88, `pit_lap` 39 |
| 6 | Miami Grand Prix | 835 | 170 | 1,005 | 83.1% | 26 | `fastf1_inaccurate` 144, `pit_lap` 38, `shape_rmse_over_threshold` 26 |
| 7 | Emilia Romagna Grand Prix | 956 | 251 | 1,207 | 79.2% | 0 | `fastf1_inaccurate` 251, `pit_lap` 75, `missing_lap_time` 2 |
| 8 | Monaco Grand Prix | 1,271 | 154 | 1,425 | 89.2% | 0 | `fastf1_inaccurate` 154, `pit_lap` 81, `path_length_outlier` 4 |
| 9 | Spanish Grand Prix | 892 | 311 | 1,203 | 74.1% | 98 | `fastf1_inaccurate` 213, `pit_lap` 109, `shape_rmse_over_threshold` 98 |
| 10 | Canadian Grand Prix | 1,197 | 152 | 1,349 | 88.7% | 0 | `fastf1_inaccurate` 152, `pit_lap` 131, `missing_lap_time` 3 |
| 11 | Austrian Grand Prix | 987 | 139 | 1,126 | 87.7% | 23 | `fastf1_inaccurate` 116, `pit_lap` 65, `shape_rmse_over_threshold` 23 |
| 12 | British Grand Prix | 496 | 329 | 825 | 60.1% | 0 | `fastf1_inaccurate` 329, `missing_lap_time` 91, `pit_lap` 76 |
| 13 | Belgian Grand Prix | 589 | 290 | 879 | 67.0% | 158 | `shape_rmse_over_threshold` 158, `shape_p95_over_threshold` 156, `fastf1_inaccurate` 132 |
| 14 | Hungarian Grand Prix | 1,288 | 80 | 1,368 | 94.2% | 0 | `fastf1_inaccurate` 79, `pit_lap` 60, `path_length_outlier` 1 |
| 15 | Dutch Grand Prix | 1,041 | 323 | 1,364 | 76.3% | 0 | `fastf1_inaccurate` 323, `pit_lap` 80, `missing_lap_time` 2 |
| 16 | Italian Grand Prix | 916 | 58 | 974 | 94.0% | 0 | `fastf1_inaccurate` 58, `pit_lap` 41 |
| 17 | Azerbaijan Grand Prix | 472 | 496 | 968 | 48.8% | 383 | `shape_rmse_over_threshold` 383, `shape_p95_over_threshold` 372, `fastf1_inaccurate` 113 |
| 18 | Singapore Grand Prix | 1,153 | 76 | 1,229 | 93.8% | 10 | `fastf1_inaccurate` 66, `pit_lap` 48, `shape_rmse_over_threshold` 10 |
| 19 | United States Grand Prix | 963 | 104 | 1,067 | 90.3% | 0 | `fastf1_inaccurate` 104, `pit_lap` 42, `missing_lap_time` 1 |
| 20 | Mexico City Grand Prix | 610 | 653 | 1,263 | 48.3% | 543 | `shape_rmse_over_threshold` 543, `fastf1_inaccurate` 110, `pit_lap` 57 |
| 21 | São Paulo Grand Prix | 747 | 504 | 1,251 | 59.7% | 302 | `shape_rmse_over_threshold` 302, `fastf1_inaccurate` 202, `pit_lap` 77 |
| 22 | Las Vegas Grand Prix | 746 | 140 | 886 | 84.2% | 14 | `fastf1_inaccurate` 126, `pit_lap` 45, `shape_rmse_over_threshold` 14 |
| 23 | Qatar Grand Prix | 921 | 146 | 1,067 | 86.3% | 1 | `fastf1_inaccurate` 145, `pit_lap` 84, `missing_lap_time` 3 |
| 24 | Abu Dhabi Grand Prix | 1,061 | 95 | 1,156 | 91.8% | 21 | `fastf1_inaccurate` 74, `pit_lap` 54, `shape_rmse_over_threshold` 21 |
