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
    schemas/
      responses.py          # Pydantic response models (OpenAPI docs)
    api/
      deps.py               # shared dependencies (crew validation)
      routes/
        crew.py             # /api/v1/crew/*
        alerts.py           # /api/v1/alerts
        environment.py      # /api/v1/space-weather, /radiation, ...
  tests/
    test_api.py             # API smoke tests (pytest)
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

23 tests, all passing: 17 API tests (every endpoint, filters,
pagination, 404/422 handling, vitals determinism, alert sorting,
per-crew alerts, vitals `days` param, new vitals indicators) + 6 light security tests
(traversal, injection-style input, error-response hygiene, method
checks). The live refresh endpoint is not covered by pytest because it
calls external APIs; it was verified live instead. Dependencies are
audited with `pip-audit` (no known vulnerabilities as of Nov 14, 2026).

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
| GET | `/api/v1/crew/{id}/report` | Weekly-style report for one crew member |
| GET | `/api/v1/crew/{id}/alerts` | Alerts for one crew member (lab + vitals, most severe first) |
| GET | `/api/v1/alerts` | All alerts (labs + vitals + radiation) |
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
- CORS is open for the hackathon demo. Restrict it before any real use.

## Browser CORS configuration

CORS is restricted to explicit frontend origins. The local defaults are
`http://localhost:5173` and `http://127.0.0.1:5173`. Set
`ASTRO_CORS_ORIGINS` to a comma-separated list of deployed frontend origins
before production deployment. Do not use `*` for a deployed dashboard.
