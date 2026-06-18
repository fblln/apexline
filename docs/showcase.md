# Apexline Showcase

Apexline validates a reference circuit line against real FastF1 position traces
for a requested year, event, and session. Canada 2025 is the checked-in proof
point, but the workflow is not tied to that season.

## Example 1: Single Race Session

```bash
apexline validate --year 2025 --event Canada --session R
```

This writes:

| Artifact | Purpose |
|---|---|
| `data/2025/canadian-grand-prix/r/circuit-analysis.json` | line fit, polyline, and summary metrics |
| `data/2025/canadian-grand-prix/r/lap-diagnostics.json` | per-lap compliance and rejection reasons |
| `data/2025/canadian-grand-prix/r/artifact-manifest.json` | command, thresholds, provenance, and paths |

The checked-in Canada result demonstrates the main capability:

- 1,349 laps inspected.
- 1,157 geometry-usable laps.
- 192 rejected laps with explicit reasons.
- 84-point compact polyline with less than 1 m simplification error.

![Canada 2025 lap diagnostic overlays](assets/canada-2025-lap-diagnostic-overlays.svg)

Belgium 2025 is the stronger rejected-lap shape showcase. Spa has many laps
that need visual inspection because the projected lap shape diverges from the
reference geometry:

![Belgian Grand Prix rejected-lap gallery](assets/rejected-laps-2025/13-belgian-grand-prix.svg)

## Example 2: Non-Race Session

The same command model works for any FastF1-supported session code:

```bash
apexline validate --year 2025 --event Canada --session Q
```

Qualifying and practice sessions may have fewer laps or different telemetry
quality. Apexline records the session in every artifact and in each `lap_key`,
so race and non-race laps cannot collide downstream.

## Example 3: Full-Year Batch

```bash
apexline batch --year 2025 --session R
apexline-summarize --manifest data/2025/all-events/r/artifact-manifest.json
```

Batch mode is useful for season-level summaries and galleries. It is not
required for normal use; single-session validation is the primary workflow.

![2025 lap compliance](assets/lap-compliance-2025.svg)

## No-Download Demo

```bash
apexline fixture-demo --output-dir data/fixture-demo
apexline schema-check data/fixture-demo/lap-diagnostics.json
apexline-summarize --manifest data/fixture-demo/artifact-manifest.json
```

The fixture proves the artifact and visualization path without requiring
FastF1 downloads.
