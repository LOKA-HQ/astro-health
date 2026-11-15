# Astro Health — Astronaut Health Monitoring

Health-monitoring software for astronauts on long-duration space missions.
Built by team **NASA 6 of October** for the **NASA Space Apps Challenge 2026**,
Challenge 05: *Create Health Monitoring Software for Astronauts on Space
Missions*.

The app tracks crew health across vitals, blood lab results, and the
radiation environment; raises prioritized alerts; and produces daily and
weekly reports for a crew on a long Mars trip.

> Prototype for a hackathon demo. Not a medical device.

## Features

- **Overview** — crew status at a glance: critical alerts, latest vitals,
  14-day health trends, radiation snapshot, priority alerts, crew readiness.
- **Body** — interactive 3D crew model (Three.js) with a heart pulse synced
  to resting heart rate, 8 vital indicators, and 30-day trend charts.
- **Labs** — 13,193 real clinical and immune measurements from the
  Inspiration4 mission, flagged against reference ranges and personal
  baselines, with High/Low/Baseline filters, 50-row pages, and a weekly
  report export.
- **Environment** — live radiation data: GOES-18 proton flux with the NOAA
  S-scale, NASA DONKI space-weather events, and published reference dose
  rates.
- **Alerts** — one prioritized feed combining lab, vitals, and radiation
  alerts (48 total: 20 critical, 27 warning, 1 info).
- **Live refresh** — space weather and radiation snapshots can be re-fetched
  on demand from NASA DONKI and NOAA SWPC.

## Tech stack

- **Back-end:** Python 3.12+ (3.14 in Docker), FastAPI, Pydantic, httpx, Uvicorn
- **Front-end:** React 19, Vite 6, Recharts, Three.js, lucide-react
- **Tests:** pytest (24 tests)
- **Deployment:** Docker (multi-stage front-end build served by nginx)

## Project structure

```text
.
  README.md               # this file
  CHANGELOG_FIXES.md      # notes on this revision
  docker-compose.yml      # back-end + front-end services
  data/                   # prepared datasets (JSON + raw downloads)
  backend/                # FastAPI back-end (see backend/README.md)
  frontend/               # React/Vite dashboard (see frontend/README.md)
```

## Quick start

The fastest way to run the whole stack is Docker:

```bash
docker compose up --build
```

- Dashboard: http://localhost:8080
- API base: http://localhost:8000
- Interactive API docs: http://localhost:8000/docs

Run the services manually instead:

```bash
# Back-end (terminal 1)
cd backend
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python run.py

# Front-end (terminal 2)
cd frontend
npm install
cp .env.example .env
npm run dev
```

- Dashboard (dev): http://localhost:5173
- Production front-end build: `npm run build` in `frontend/`

Optional: copy `backend/.env.example` to `backend/.env` and set `NASA_API_KEY`
(a free key from https://api.nasa.gov) to lift the DONKI demo rate limits.
For a deployed front-end, set `ASTRO_CORS_ORIGINS` on the back-end to the
front-end origin(s); the front-end API address is set at build time with
`VITE_API_BASE` (default `http://localhost:8000/api/v1`).

Run the back-end tests:

```bash
cd backend
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest -q          # 24 tests, all passing
```

## API reference

Base URL: http://localhost:8000. Crew IDs: `C001`–`C004`.

| Method | Path | Description |
|---|---|---|
| GET | `/` | Service health and crew list |
| GET | `/health` | Dataset status and snapshot freshness |
| GET | `/api/v1/crew` | Crew roster with lab/flag counts |
| GET | `/api/v1/crew/{id}/summary` | Per-crew summary (labs + vitals) |
| GET | `/api/v1/crew/{id}/labs` | Lab records, filterable and paginated |
| GET | `/api/v1/crew/{id}/vitals` | 30-day vitals time series |
| GET | `/api/v1/crew/{id}/report` | Weekly-style report for one crew member |
| GET | `/api/v1/crew/{id}/alerts` | Alerts for one crew member |
| GET | `/api/v1/alerts` | All alerts (labs + vitals + radiation) |
| GET | `/api/v1/space-weather` | DONKI events and radiation alert mapping |
| GET | `/api/v1/radiation` | GOES proton flux, S-scale, dose references |
| GET | `/api/v1/thresholds` | Alert thresholds |
| GET | `/api/v1/omics` | Proteomics/metabolomics summary |
| POST | `/api/v1/environment/refresh` | Re-fetch live DONKI + GOES snapshots |

## Data

| Data | Records | Source | Real / synthetic |
|---|---|---|---|
| Clinical labs (blood count, metabolic, cardiovascular) | 1,280 | NASA OSDR OSD-569, OSD-575 (Inspiration4) | Real |
| Immune measurements (serum + urine) | 11,913 | NASA OSDR OSD-575, OSD-656 (Inspiration4) | Real |
| Proteomics / metabolomics changes | 300+ significant | NASA OSDR OSD-571 (Inspiration4) | Real |
| Space-weather events (SEP, CME, GST) | Last 30 days | NASA DONKI API | Real, live |
| Proton flux (GOES-18, >=10 MeV) | 7 days, hourly | NOAA SWPC | Real, live |
| Vitals time series (HR, sleep, SpO2, stress, blood pressure, body temperature, mood) | 30 days x 4 crew | Generated | Synthetic |

Notes on provenance:

- No public astronaut wearable or actigraphy time series exists, so the
  vitals are generated demo data, modeled on published healthy ranges and
  clearly labeled as synthetic in every API response and in the dashboard.
- Lab values are flagged against OSDR reference ranges (clinical panels)
  or each crew member's own pre-flight median (immune panels). Pre-flight
  baselines vary between crew members, so personal baselines matter.
- Reference dose rates (ISS ~0.5–1, Mars transit ~1.8, Mars surface ~0.64
  mSv/day) come from published MSL RAD measurements (Zeitlin et al. 2013,
  Hassler et al. 2014).

## Team — NASA 6 of October

| Member | Role |
|---|---|
| Ibrahim | Team lead |
| Nonaa (also called Nour) | Front-end, dashboard design |
| Yousef (Joe) | Design, data |
| Hala | Design |
| Malek | Back-end, data, code review |

## License

Built for the NASA Space Apps Challenge 2026. Data sources retain their own
terms (NASA OSDR, NASA DONKI, NOAA SWPC — all public).

## AI assistance disclosure

This project was built with AI assistance in all stages of the project.
The AI tools used were Muse and Claude Code, working as assistants from
the team's direction: data preparation, back-end code, front-end code,
and documentation. The challenge choice, the project idea, and all
decisions are the team's own. All NASA data used is real, sourced from
NASA OSDR, NASA DONKI, and NOAA SWPC, and verified against those sources.
The vitals time series is synthetic demo data and is labeled as such in
every API response and in the dashboard. No NASA branding or design
elements were generated or modified, and no AI-generated images, video, or
audio are used in this project.
