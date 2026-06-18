# Contributing

## Setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

## Checks

```bash
.venv/bin/python -m pytest
.venv/bin/ruff check .
```

FastF1 integration tests are optional because they need cached or downloadable
session data:

```bash
APEXLINE_RUN_INTEGRATION=1 .venv/bin/python -m pytest tests/test_integration_fastf1.py
```

## Artifact Policy

Keep small, intentional examples in `data/` and `docs/assets/`. Do not commit
FastF1 cache contents, virtual environments, bytecode caches, or local scratch
outputs.
