# Parameter Guide

Apexline has two jobs:

1. Validate FastF1 local telemetry laps against an oracle circuit shape.
2. Encode the oracle circuit shape compactly without losing important geometry.

The defaults are intentionally conservative.

## Recommended Defaults

```bash
--validation-samples 720
--validation-offset-step 4
--polyline-tolerance-m 1.0
--polyline-precision 5
--max-shape-candidates 12
--average-laps 5
--average-samples 720
--shape-rmse-threshold-m 32
--shape-p95-threshold-m 75
--shape-rmse-threshold-pct-of-length 0.016
--shape-p95-threshold-pct-of-length 0.025
```

## Validation Samples

`--validation-samples` controls how many equal-progress points are compared
between the oracle circuit line and FastF1 lap shape.

Recommended: `720`

Why:

- It is dense enough to catch chicanes and tight corner errors.
- It keeps the fit stable across circuits from Monaco to Spa.
- It is still cheap enough for a full-season run.

Lower values can hide localized errors. Higher values usually add runtime more
than insight.

## Validation Offset Step

`--validation-offset-step` controls the circular start-offset search.

Recommended: `4`

FastF1 lap samples and oracle circuit LineStrings rarely start at exactly the
same physical point. The script searches different phase offsets around the
closed loop. Step `4` at `720` samples means offsets are tested every 0.56% of a
lap.

Use a smaller value only when debugging a single circuit.

## Shape Thresholds

Shape compliance uses both a meter floor and a circuit-length proportion:

```text
effective RMSE limit = max(32 m, 1.6% of oracle length)
effective p95 limit  = max(75 m, 2.5% of oracle length)
```

The proportional limit matters on long circuits such as Spa, where the same
small relative disagreement produces a larger absolute residual. The meter
floor avoids over-penalizing short circuits. Both effective values are written
to each diagnostics artifact.

## Polyline Tolerance

`--polyline-tolerance-m` controls Ramer-Douglas-Peucker simplification in meters.

Recommended: `1.0`

Why not higher?

- F1 circuits have chicanes, hairpins, and tight street-circuit geometry.
- A 5-10 m tolerance can visibly cut corners.
- The encoded strings are already small enough at 1 m tolerance.

In the 2025 run, a 1 m tolerance produced:

- average of about 105 simplified points per circuit,
- average of about 309 encoded characters,
- max simplification error under 1 m for every circuit.

That is a good tradeoff for map overlays.

## Polyline Precision

`--polyline-precision` controls decimal precision for Google encoded polyline.

Recommended: `5`

Precision 5 is the common web-map default. It represents roughly meter-level
coordinate precision. Since the simplification tolerance is already 1 m, using a
higher encoding precision usually increases string size without materially
improving the visible line.

## Candidate Lap Selection

`--max-shape-candidates` controls how many FastF1 laps receive full shape
fitting after a cheap path-length filter.

Recommended: `12`

Why this exists:

FastF1's `IsAccurate` flag is useful, but not sufficient for circuit-shape
validation. Some early laps can include odd position slices while still being
marked accurate.

The script now:

1. collects clean non-pit laps,
2. trims repeated lap-boundary overlap when an over-long lap contains one clean loop,
3. rejects laps whose normalized FastF1 path length is still too far from the oracle length,
4. ranks remaining laps by path-length closeness,
5. runs expensive shape fitting on the top candidates,
6. picks the lowest RMSE fit.

The more important Canada lesson now is seam repair: some laps look too long
only because the timing-line segment repeats. When Apexline can trim that
overlap and recover one clean loop, the lap becomes usable evidence instead of
a false rejection.

## Averaging Laps

`--average-laps` controls how many fitted FastF1 laps are averaged into a
secondary diagnostic line.

Recommended: `5`

Important: averaging is not always better.

FastF1 traces are driven racing lines. The oracle circuit shape is usually a
centerline. Multiple good laps can use different corner entries, exits, and
curb usage. Averaging those racing lines can move the result away from the
centerline.

Use averaged output as a diagnostic:

- If averaging improves RMSE, the single best lap may still have local noise.
- If averaging worsens RMSE, the circuit likely has meaningful racing-line
  variation relative to the mapped centerline.

## Interpreting RMSE

These metrics do not mean "the car GPS was wrong by 7 meters." FastF1 has no
native GPS channel here.

They mean:

> After allowing scale, rotation, translation, direction, and start offset, how
> closely does the FastF1 local track shape match the oracle circuit shape?

Useful thresholds:

| RMSE | Interpretation |
|---:|---|
| 0-5 m | Excellent shape agreement. |
| 5-10 m | Good agreement for display and validation. |
| 10-20 m | Investigate localized differences, especially street circuits. |
| 20+ m | Likely wrong lap, wrong layout, or source geometry mismatch. |
