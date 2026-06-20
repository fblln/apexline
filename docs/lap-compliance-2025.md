# 2025 lap compliance summary

Good laps are laps that pass Apexline's oracle-shape evidence checks.
Bad laps are laps rejected for at least one reason such as FastF1
`IsAccurate == False`, pit in/out, too few position samples,
path-length outlier, or shape residual over threshold.

Reason counts are not mutually exclusive: one bad lap can be both a
pit lap and FastF1-inaccurate.

## Season totals

| Metric | Value |
|---|---:|
| Circuits | 24 |
| Total laps inspected | 26,689 |
| Fitted laps | 23,042 |
| Good laps | 23,042 (86.3%) |
| Bad laps | 3,647 (13.7%) |
| Shape-threshold bad laps | 0 |

## Rejection signals

| Reason | Count |
|---|---:|
| `fastf1_inaccurate` | 3,646 |
| `pit_lap` | 1,625 |
| `path_length_outlier` | 45 |
| `too_few_position_samples` | 19 |

## Circuit table

| Round | Event | Good | Bad | Total | Good % | Shape Bad | Top rejection signals |
|---:|---|---:|---:|---:|---:|---:|---|
| 1 | Australian Grand Prix | 568 | 359 | 927 | 61.3% | 0 | `fastf1_inaccurate` 359, `pit_lap` 132, `path_length_outlier` 5 |
| 2 | Chinese Grand Prix | 995 | 70 | 1,065 | 93.4% | 0 | `fastf1_inaccurate` 70, `pit_lap` 52 |
| 3 | Japanese Grand Prix | 997 | 62 | 1,059 | 94.1% | 0 | `fastf1_inaccurate` 62, `pit_lap` 42 |
| 4 | Bahrain Grand Prix | 952 | 176 | 1,128 | 84.4% | 0 | `fastf1_inaccurate` 176, `pit_lap` 84, `path_length_outlier` 13 |
| 5 | Saudi Arabian Grand Prix | 810 | 88 | 898 | 90.2% | 0 | `fastf1_inaccurate` 88, `pit_lap` 39, `path_length_outlier` 1 |
| 6 | Miami Grand Prix | 861 | 144 | 1,005 | 85.7% | 0 | `fastf1_inaccurate` 144, `pit_lap` 38, `path_length_outlier` 4 |
| 7 | Emilia Romagna Grand Prix | 956 | 251 | 1,207 | 79.2% | 0 | `fastf1_inaccurate` 251, `pit_lap` 75, `path_length_outlier` 2 |
| 8 | Monaco Grand Prix | 1,271 | 154 | 1,425 | 89.2% | 0 | `fastf1_inaccurate` 154, `pit_lap` 81, `path_length_outlier` 4 |
| 9 | Spanish Grand Prix | 990 | 213 | 1,203 | 82.3% | 0 | `fastf1_inaccurate` 213, `pit_lap` 109, `path_length_outlier` 1 |
| 10 | Canadian Grand Prix | 1,197 | 152 | 1,349 | 88.7% | 0 | `fastf1_inaccurate` 152, `pit_lap` 131, `path_length_outlier` 2 |
| 11 | Austrian Grand Prix | 1,010 | 116 | 1,126 | 89.7% | 0 | `fastf1_inaccurate` 116, `pit_lap` 65, `path_length_outlier` 2 |
| 12 | British Grand Prix | 496 | 329 | 825 | 60.1% | 0 | `fastf1_inaccurate` 329, `pit_lap` 76, `path_length_outlier` 3 |
| 13 | Belgian Grand Prix | 747 | 132 | 879 | 85.0% | 0 | `fastf1_inaccurate` 132, `pit_lap` 72 |
| 14 | Hungarian Grand Prix | 1,288 | 80 | 1,368 | 94.2% | 0 | `fastf1_inaccurate` 79, `pit_lap` 60, `path_length_outlier` 1 |
| 15 | Dutch Grand Prix | 1,041 | 323 | 1,364 | 76.3% | 0 | `fastf1_inaccurate` 323, `pit_lap` 80, `path_length_outlier` 2 |
| 16 | Italian Grand Prix | 916 | 58 | 974 | 94.0% | 0 | `fastf1_inaccurate` 58, `pit_lap` 41 |
| 17 | Azerbaijan Grand Prix | 855 | 113 | 968 | 88.3% | 0 | `fastf1_inaccurate` 113, `pit_lap` 41, `path_length_outlier` 1 |
| 18 | Singapore Grand Prix | 1,163 | 66 | 1,229 | 94.6% | 0 | `fastf1_inaccurate` 66, `pit_lap` 48 |
| 19 | United States Grand Prix | 963 | 104 | 1,067 | 90.3% | 0 | `fastf1_inaccurate` 104, `pit_lap` 42 |
| 20 | Mexico City Grand Prix | 1,153 | 110 | 1,263 | 91.3% | 0 | `fastf1_inaccurate` 110, `pit_lap` 57 |
| 21 | São Paulo Grand Prix | 1,049 | 202 | 1,251 | 83.9% | 0 | `fastf1_inaccurate` 202, `pit_lap` 77, `path_length_outlier` 2 |
| 22 | Las Vegas Grand Prix | 760 | 126 | 886 | 85.8% | 0 | `fastf1_inaccurate` 126, `pit_lap` 45, `path_length_outlier` 1 |
| 23 | Qatar Grand Prix | 922 | 145 | 1,067 | 86.4% | 0 | `fastf1_inaccurate` 145, `pit_lap` 84, `path_length_outlier` 1 |
| 24 | Abu Dhabi Grand Prix | 1,082 | 74 | 1,156 | 93.6% | 0 | `fastf1_inaccurate` 74, `pit_lap` 54 |
