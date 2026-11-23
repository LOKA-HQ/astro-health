# Astronaut Health Monitoring - Back-end API

NASA Space Apps Challenge 2026, Challenge 5. NASA 6 of October team.

FastAPI service over the prepared data in `../data/` (real Inspiration4 lab
data from NASA OSDR, synthetic 30-day vitals demo, live DONKI space weather
and NOAA GOES radiation environment).

## Project structure

```text
backend/
  run.py                    # dev entrypoint (python run.py)
  requirements.txt          # runtime dependencies (pinned, verified)
  requirements-dev.txt      # runtime + test/lint dependencies (pinned)
  pyproject.toml            # ruff + pytest configuration
  Dockerfile                # container build (from project root)
  .env.example              # optional NASA_API_KEY
  app/
    main.py                 # app factory, routers, root + health endpoints
    config.py               # paths, API URLs, constants, env vars
    data/
      loader.py             # JSON loading, in-memory store, flag helpers
      vitals.py             # synthetic vitals generator (demo data)
    services/
      crew.py               # crew summaries, lab queries, reports
      alerts.py             # alert aggregation (labs + vitals + radiation)
      environment.py        # live DONKI / GOES refresh
      personalization.py    # personal baselines, effective thresholds, assessment
      environments.py       # location awareness: shifts, evidence, detection
      forecast.py           # 7-day vitals trend forecast
    schemas/
      responses.py          # Pydantic response models (OpenAPI docs)
    api/
      deps.py               # shared dependencies (crew id, threshold query params)
      routes/
        crew.py             # /api/v1/crew/*
        alerts.py           # /api/v1/alerts
        context.py          # /api/v1/environments, /environments/detect
        environment.py      # /api/v1/space-weather, /radiation, ...
  tests/
    test_api.py             # API tests (pytest)
    test_personalization.py # personal / environment-aware thresholds
    test_forecast.py        # trend forecast
    test_security.py        # light security tests (pytest)
```

Rules of the layout:

- `routes/` only handle HTTP (paths, query params, status codes). All logic
  lives in `services/`.
- `services/` work on plain dicts and never import FastAPI.
- `data/` owns loading, storage, and the synthetic vitals generator.
- `schemas/` define response shapes; nothing else validates output.

## Setup

Requirements: Python 3.12+ locally; the Docker image uses Python 3.14.

```bash
cd backend
python -m venv .venv
.venv/bin/pip install -r requirements-dev.txt   # runtime + tests + lint
```

Optional: copy `.env.example` to `.env` and set `NASA_API_KEY` (free key
from https://api.nasa.gov). The file is loaded automatically
(python-dotenv). Without it, the live refresh uses `DEMO_KEY`, which is
enough for the demo.

## Run

```bash
# from backend/
.venv/bin/python run.py
# or
.venv/bin/uvicorn app.main:app --reload --port 8000
```

- API base: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Test

```bash
# from backend/
.venv/bin/pytest -q
.venv/bin/ruff check app tests run.py
.venv/bin/ruff format --check app tests run.py
```

The suite covers every endpoint (filters, pagination, 404/422 handling,
vitals determinism, alert sorting, per-crew alerts, the `profile` /
`environment` / `baseline_environment` / `days_in_environment` options),
unit tests for the personal-baseline, environment and forecast logic
(including checks that every shift cites a source and that the statistical
constants and absolute limits match `docs/SOURCES.md`), and light security
tests (traversal, injection-style input, error-response hygiene, method
checks). The live refresh endpoint is not covered by pytest because it
calls external APIs. GitHub Actions runs pytest and ruff on every push.
`TEST_RESULTS.md` is a dated record of an earlier run.

## Docker

```bash
# from the project root (nasa-space-apps-2026/)
docker build -f backend/Dockerfile -t astro-health .
docker run -p 8000:8000 astro-health
```

## Endpoints

| Method | Path | Returns |
|---|---|---|
| GET | `/` | Service health and crew list |
| GET | `/health` | Dataset status and snapshot freshness |
| GET | `/api/v1/crew` | Crew roster with lab/flag counts |
| GET | `/api/v1/crew/{id}/summary` | Per-crew summary (labs + vitals) |
| GET | `/api/v1/crew/{id}/labs?panel=&timepoint=&status=&flagged_only=&limit=&offset=` | Lab records, filterable and paginated |
| GET | `/api/v1/crew/{id}/vitals?days=` | Vitals time series, last N days (1-30, default 30; synthetic, labeled) |
| GET | `/api/v1/crew/{id}/thresholds?profile=&environment=&baseline_environment=&days_in_environment=` | Limits in force: generic vs personal, adjusted for the environment |
| GET | `/api/v1/crew/{id}/assessment?days=&profile=&environment=...` | Day-by-day nominal / warning / critical status |
| GET | `/api/v1/crew/{id}/forecast?horizon=&profile=&environment=...` | Vitals trend forecast (horizon 1-14 days, default 7) |
| GET | `/api/v1/crew/{id}/report` | Weekly-style report for one crew member |
| GET | `/api/v1/crew/{id}/alerts?profile=&environment=...` | Alerts for one crew member (lab + vitals, most severe first) |
| GET | `/api/v1/alerts?profile=&environment=...` | All alerts (labs + vitals + radiation) |
| GET | `/api/v1/environments` | Environments, their shifts and the evidence behind them |
| GET | `/api/v1/environments/detect?body=&altitude_km=&accel_g=` | Infer the environment from telemetry |
| GET | `/api/v1/space-weather` | DONKI events and radiation alert mapping |
| GET | `/api/v1/radiation` | GOES proton flux, S-scale, dose references |
| GET | `/api/v1/thresholds` | Alert thresholds |
| GET | `/api/v1/omics` | OSD-571 proteomics/metabolomics summary |
| POST | `/api/v1/environment/refresh` | Re-fetch live DONKI + GOES snapshots |

Crew IDs: `C001`-`C004`. Timepoints: `L-92, L-44, L-3, R+1, R+45, R+82, R+194`
(pre-flight `L-`, post-flight `R+`).

## Notes

- Lab `status` values: `normal`, `high`, `low` (vs OSDR reference ranges),
  `elevated_vs_baseline`, `reduced_vs_baseline` (immune panels vs the crew
  member's own pre-flight median).
- Vitals are synthetic demo data (no public astronaut wearable stream
  exists). C001 comes from `data/vitals_timeseries_demo.json`; C002-C004
  are generated deterministically in `app/data/vitals.py`. Each day
  carries resting HR, sleep, steps, SpO2, stress, blood pressure,
  body temperature, and mood.
- The `profile`, `environment`, `baseline_environment` and
  `days_in_environment` query parameters are shared by the alerts,
  thresholds, assessment and forecast endpoints (see `api/deps.py`). With none
  of them the original fixed thresholds apply. How the limits are built, and
  the evidence behind every shift, is in `../docs/SOURCES.md`.

## Browser CORS configuration

CORS is restricted to explicit frontend origins. The local defaults are
`http://localhost:5173` and `http://127.0.0.1:5173`. Set
`ASTRO_CORS_ORIGINS` to a comma-separated list of deployed frontend origins
before production deployment. Do not use `*` for a deployed dashboard.
