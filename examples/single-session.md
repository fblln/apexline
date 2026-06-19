# Single-Session Example

This is the fastest path for validating FastF1 laps against an oracle circuit
GPS LineString with Apexline.

## Install

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
```

## Validate One Session

```bash
.venv/bin/apexline validate \
  --year 2025 \
  --event Canada \
  --session R
```

Outputs:

```text
data/2025/canadian-grand-prix/r/circuit-analysis.json
data/2025/canadian-grand-prix/r/circuit-analysis.csv
data/2025/canadian-grand-prix/r/lap-diagnostics.json
data/2025/canadian-grand-prix/r/artifact-manifest.json
```

`lap-diagnostics.json` records raw lap length, overlap-normalized length when
cleanup was possible, and the final shape fit against the oracle circuit line.

## Check And Summarize

```bash
.venv/bin/apexline schema-check \
  data/2025/canadian-grand-prix/r/circuit-analysis.json \
  data/2025/canadian-grand-prix/r/lap-diagnostics.json \
  data/2025/canadian-grand-prix/r/artifact-manifest.json

.venv/bin/apexline-summarize \
  --manifest data/2025/canadian-grand-prix/r/artifact-manifest.json
```

## Render A Static Evidence Card

```bash
.venv/bin/apexline-render-evidence \
  --year 2025 \
  --event "Canadian Grand Prix" \
  --session R \
  --diagnostics-json data/2025/canadian-grand-prix/r/lap-diagnostics.json
```

## Try A Different Session

```bash
.venv/bin/apexline validate --year 2025 --event Canada --session Q
```

If FastF1 cannot load the requested session, Apexline names the missing
year/event/session in the error.
