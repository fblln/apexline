# 2025 lap compliance summary

Good laps are laps that pass Apexline's oracle-shape evidence checks.
Bad laps are laps rejected for at least one geometry-relevant reason
such as pit in/out, too few position samples, path-length outlier, or
shape residual over threshold.

FastF1 `IsAccurate == False` is recorded as a non-blocking warning.
Timing or track-status warnings do not prevent a lap from passing the
oracle shape fit.

## Season totals

| Metric | Value |
|---|---:|
| Circuits | 24 |
| Total laps inspected | 26,689 |
| Fitted laps | 25,022 |
| Good laps | 25,019 (93.7%) |
| Bad laps | 1,670 (6.3%) |
| Shape-threshold bad laps | 3 |

## Rejection signals

| Reason | Count |
|---|---:|
| `pit_lap` | 1,625 |
| `path_length_outlier` | 45 |
| `too_few_position_samples` | 19 |
| `shape_p95_over_threshold` | 3 |

## Non-blocking warnings

| Warning | Count |
|---|---:|
| `fastf1_inaccurate` | 3,646 |

## Circuit table

| Round | Event | Good | Bad | Total | Good % | Shape Bad | Warnings | Top rejection signals |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 1 | Australian Grand Prix | 789 | 138 | 927 | 85.1% | 2 | 359 | `pit_lap` 132, `path_length_outlier` 5, `shape_p95_over_threshold` 2 |
| 2 | Chinese Grand Prix | 1,013 | 52 | 1,065 | 95.1% | 0 | 70 | `pit_lap` 52 |
| 3 | Japanese Grand Prix | 1,017 | 42 | 1,059 | 96.0% | 0 | 62 | `pit_lap` 42 |
| 4 | Bahrain Grand Prix | 1,031 | 97 | 1,128 | 91.4% | 0 | 176 | `pit_lap` 84, `path_length_outlier` 13, `too_few_position_samples` 12 |
| 5 | Saudi Arabian Grand Prix | 858 | 40 | 898 | 95.5% | 0 | 88 | `pit_lap` 39, `path_length_outlier` 1, `too_few_position_samples` 1 |
| 6 | Miami Grand Prix | 963 | 42 | 1,005 | 95.8% | 0 | 144 | `pit_lap` 38, `path_length_outlier` 4, `too_few_position_samples` 1 |
| 7 | Emilia Romagna Grand Prix | 1,130 | 77 | 1,207 | 93.6% | 0 | 251 | `pit_lap` 75, `path_length_outlier` 2 |
| 8 | Monaco Grand Prix | 1,340 | 85 | 1,425 | 94.0% | 1 | 154 | `pit_lap` 81, `path_length_outlier` 4, `shape_p95_over_threshold` 1 |
| 9 | Spanish Grand Prix | 1,093 | 110 | 1,203 | 90.9% | 0 | 213 | `pit_lap` 109, `path_length_outlier` 1 |
| 10 | Canadian Grand Prix | 1,217 | 132 | 1,349 | 90.2% | 0 | 152 | `pit_lap` 131, `path_length_outlier` 2, `too_few_position_samples` 1 |
| 11 | Austrian Grand Prix | 1,059 | 67 | 1,126 | 94.0% | 0 | 116 | `pit_lap` 65, `path_length_outlier` 2 |
| 12 | British Grand Prix | 746 | 79 | 825 | 90.4% | 0 | 329 | `pit_lap` 76, `path_length_outlier` 3 |
| 13 | Belgian Grand Prix | 807 | 72 | 879 | 91.8% | 0 | 132 | `pit_lap` 72 |
| 14 | Hungarian Grand Prix | 1,307 | 61 | 1,368 | 95.5% | 0 | 79 | `pit_lap` 60, `path_length_outlier` 1 |
| 15 | Dutch Grand Prix | 1,282 | 82 | 1,364 | 94.0% | 0 | 323 | `pit_lap` 80, `path_length_outlier` 2, `too_few_position_samples` 1 |
| 16 | Italian Grand Prix | 933 | 41 | 974 | 95.8% | 0 | 58 | `pit_lap` 41 |
| 17 | Azerbaijan Grand Prix | 926 | 42 | 968 | 95.7% | 0 | 113 | `pit_lap` 41, `path_length_outlier` 1 |
| 18 | Singapore Grand Prix | 1,181 | 48 | 1,229 | 96.1% | 0 | 66 | `pit_lap` 48 |
| 19 | United States Grand Prix | 1,025 | 42 | 1,067 | 96.1% | 0 | 104 | `pit_lap` 42 |
| 20 | Mexico City Grand Prix | 1,206 | 57 | 1,263 | 95.5% | 0 | 110 | `pit_lap` 57 |
| 21 | São Paulo Grand Prix | 1,172 | 79 | 1,251 | 93.7% | 0 | 202 | `pit_lap` 77, `path_length_outlier` 2 |
| 22 | Las Vegas Grand Prix | 840 | 46 | 886 | 94.8% | 0 | 126 | `pit_lap` 45, `path_length_outlier` 1 |
| 23 | Qatar Grand Prix | 982 | 85 | 1,067 | 92.0% | 0 | 145 | `pit_lap` 84, `path_length_outlier` 1, `too_few_position_samples` 1 |
| 24 | Abu Dhabi Grand Prix | 1,102 | 54 | 1,156 | 95.3% | 0 | 74 | `pit_lap` 54 |
