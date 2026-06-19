# 2025 Validation Summary

This run compares oracle circuit GPS LineStrings against FastF1 race-lap
`X/Y` shapes after Apexline's lap filtering, overlap repair, phase search,
and similarity fit.

The residuals are shape-fit errors, not car GPS errors.

## Summary

| Metric | Value |
|---|---:|
| Circuits processed | 24 |
| Best single-lap mean RMSE | 6.5 m |
| Best single-lap median RMSE | 6.1 m |
| Worst best-lap RMSE | 13.5 m |
| Average-of-5 mean RMSE | 7.2 m |
| Average-of-5 median RMSE | 6.7 m |
| Averaging improved | 10 / 24 |
| Averaging worsened | 14 / 24 |
| Polyline simplification tolerance | 1.0 m |
| Worst simplification error | <= 1.0 m |

## Full Table

| Round | Event | Circuit | Best RMSE | Best p95 | Avg-5 RMSE | Polyline pts | Chars | Max simpl. err |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | Australian GP | Albert Park Circuit | 7.8 m | 13.8 m | 8.1 m | 108 | 335 | 1.0 m |
| 2 | Chinese GP | Shanghai International Circuit | 9.5 m | 15.9 m | 10.6 m | 117 | 337 | 0.9 m |
| 3 | Japanese GP | Suzuka International Racing Course | 4.3 m | 6.8 m | 3.9 m | 148 | 451 | 1.0 m |
| 4 | Bahrain GP | Bahrain International Circuit | 7.2 m | 12.2 m | 9.9 m | 84 | 244 | 0.7 m |
| 5 | Saudi Arabian GP | Jeddah Corniche Circuit | 5.4 m | 10.4 m | 7.5 m | 129 | 394 | 1.0 m |
| 6 | Miami GP | Miami International Autodrome | 5.5 m | 10.2 m | 6.5 m | 96 | 296 | 0.8 m |
| 7 | Emilia Romagna GP | Autodromo Enzo e Dino Ferrari | 4.5 m | 7.4 m | 4.8 m | 75 | 228 | 0.5 m |
| 8 | Monaco GP | Circuit de Monaco | 6.2 m | 14.5 m | 6.1 m | 117 | 323 | 1.0 m |
| 9 | Spanish GP | Circuit de Barcelona-Catalunya | 4.7 m | 7.9 m | 4.2 m | 111 | 315 | 1.0 m |
| 10 | Canadian GP | Circuit Gilles-Villeneuve | 5.0 m | 8.7 m | 12.4 m | 84 | 242 | 0.9 m |
| 11 | Austrian GP | Red Bull Ring | 3.9 m | 6.7 m | 3.6 m | 75 | 237 | 1.0 m |
| 12 | British GP | Silverstone Circuit | 7.1 m | 12.3 m | 7.6 m | 121 | 380 | 0.9 m |
| 13 | Belgian GP | Circuit de Spa-Francorchamps | 7.2 m | 14.6 m | 6.5 m | 133 | 417 | 0.9 m |
| 14 | Hungarian GP | Hungaroring | 4.4 m | 9.0 m | 5.6 m | 110 | 305 | 1.0 m |
| 15 | Dutch GP | Circuit Zandvoort | 8.2 m | 13.5 m | 7.5 m | 111 | 336 | 1.0 m |
| 16 | Italian GP | Autodromo Nazionale Monza | 6.0 m | 10.7 m | 6.6 m | 90 | 277 | 1.0 m |
| 17 | Azerbaijan GP | Baku City Circuit | 4.7 m | 8.3 m | 4.6 m | 79 | 254 | 1.0 m |
| 18 | Singapore GP | Marina Bay Street Circuit | 13.5 m | 27.8 m | 10.6 m | 90 | 254 | 0.9 m |
| 19 | United States GP | Circuit of the Americas | 6.4 m | 12.2 m | 6.7 m | 131 | 361 | 1.0 m |
| 20 | Mexico City GP | Autódromo Hermanos Rodríguez | 5.9 m | 9.6 m | 5.9 m | 87 | 237 | 0.9 m |
| 21 | São Paulo GP | Autódromo José Carlos Pace - Interlagos | 9.4 m | 15.1 m | 10.0 m | 121 | 334 | 1.0 m |
| 22 | Las Vegas GP | Las Vegas Street Circuit | 7.1 m | 12.7 m | 10.9 m | 88 | 274 | 1.0 m |
| 23 | Qatar GP | Losail International Circuit | 4.9 m | 9.3 m | 3.9 m | 101 | 289 | 0.8 m |
| 24 | Abu Dhabi GP | Yas Marina Circuit | 6.2 m | 10.8 m | 7.5 m | 106 | 302 | 1.0 m |

## Biggest Deviations

Using the best single FastF1 lap:

| Rank | Event | RMSE | p95 |
|---:|---|---:|---:|
| 1 | Singapore GP | 13.5 m | 27.8 m |
| 2 | Chinese GP | 9.5 m | 15.9 m |
| 3 | São Paulo GP | 9.4 m | 15.1 m |
| 4 | Dutch GP | 8.2 m | 13.5 m |
| 5 | Australian GP | 7.8 m | 13.8 m |

## Averaging Helps vs Hurts

| Event | Best RMSE | Avg-5 RMSE | Delta |
|---|---:|---:|---:|
| Canadian GP | 5.0 m | 12.4 m | +7.4 m |
| Las Vegas GP | 7.1 m | 10.9 m | +3.9 m |
| Bahrain GP | 7.2 m | 9.9 m | +2.7 m |
| Saudi Arabian GP | 5.4 m | 7.5 m | +2.1 m |
| Abu Dhabi GP | 6.2 m | 7.5 m | +1.3 m |
| Singapore GP | 13.5 m | 10.6 m | -2.9 m |
| Qatar GP | 4.9 m | 3.9 m | -1.0 m |
| Dutch GP | 8.2 m | 7.5 m | -0.7 m |
| Belgian GP | 7.2 m | 6.5 m | -0.7 m |
| Spanish GP | 4.7 m | 4.2 m | -0.5 m |

## Most Compact Oracle Polylines

| Event | Circuit km | Points | Chars | Chars / km |
|---|---:|---:|---:|---:|
| Azerbaijan GP | 6.003 | 79 | 254 | 42.3 |
| Las Vegas GP | 6.201 | 88 | 274 | 44.2 |
| Bahrain GP | 5.412 | 84 | 244 | 45.1 |
| Emilia Romagna GP | 4.909 | 75 | 228 | 46.4 |
| Italian GP | 5.793 | 90 | 277 | 47.8 |
