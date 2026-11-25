# Astro Health — Astronaut Health Monitoring

[![CI](https://github.com/LOKA-HQ/astro-health/actions/workflows/ci.yml/badge.svg)](https://github.com/LOKA-HQ/astro-health/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**English** · [العربية](README.ar.md)

Health-monitoring software for astronauts on long-duration space missions,
built by team **NASA 6 of October** for the **NASA Space Apps Challenge
2026**, Challenge 05: *Create Health Monitoring Software for Astronauts on
Space Missions*.

It tracks crew health across vitals, blood lab results and the radiation
environment, raises prioritised alerts, and judges every reading against
limits that fit **the person** and **the place** instead of one fixed range
for everybody everywhere.

> Prototype for a hackathon demo. Not a medical device.

## Highlights

- **Personal thresholds.** Limits are learned from each crew member's own
  history. A resting heart rate of 108 bpm is a critical alert for most
  people and perfectly normal for someone whose usual range is 100–120.
- **Location awareness.** The same reading means different things on Earth,
  in an aircraft cabin, during launch, on the space station, in transit to
  Mars and on the Martian surface. Limits adapt to the environment, which
  can be given or inferred from telemetry. Every adjustment is backed by a
  published source (see [docs/SOURCES.md](docs/SOURCES.md)).
- **Safety rails.** Personalisation can tighten limits freely but can only
  relax them when the person's own baseline is outside the normal range, and
  absolute limits (for example SpO2 below 90%) are always critical.
- **Real data where it exists.** 13,193 clinical and immune measurements
  from the Inspiration4 mission (NASA OSDR), live NASA DONKI space-weather
  events and NOAA GOES proton flux. Vitals are synthetic and labelled as
  such in every response.
- **Trend forecast.** A 7-day look-ahead flags indicators heading towards a
  warning limit.

## Dashboard

- **Overview** — critical alerts, latest vitals, 14-day trends, radiation
  snapshot, priority alerts, crew readiness.
- **Body** — interactive 3D crew model (Three.js) with a heart pulse synced
  to resting heart rate, 8 vital indicators and 30-day trend charts.
- **Thresholds** — choose generic or personal limits and the environment (or
  detect it from telemetry), how many days the crew member has been there and
  where the personal baseline was recorded; see the limits in force beside the
  generic ones, each person's baseline, the latest status, a chart against the
  limits and the sources behind the environment's adjustments. English and
  Arabic, dark and light.
- **Labs** — Inspiration4 clinical and immune results flagged against
  reference ranges and personal baselines, with filters, 50-row pages and a
  weekly report export.
- **Environment** — GOES-18 proton flux with the NOAA S-scale, NASA DONKI
  events and published reference dose rates, with on-demand refresh.
- **Alerts** — one prioritised feed combining lab, vitals and radiation
  alerts (48 with the default settings: 20 critical, 27 warning, 1 info).

The personal-threshold, environment and forecast options are available
through the API; the dashboard does not expose them yet.

## Quick start

With Docker:

```bash
docker compose up --build
```

- Dashboard: http://localhost:8080
- API: http://localhost:8000 (interactive docs at `/docs`)

Without Docker:

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
npm run dev          # http://localhost:5173
```

Configuration (all optional):

| Setting | Where | Purpose |
|---|---|---|
| `NASA_API_KEY` | `backend/.env` | Free key from https://api.nasa.gov; lifts DONKI demo rate limits |
| `ASTRO_CORS_ORIGINS` | back-end environment | Front-end origins allowed by CORS (localhost defaults included) |
| `VITE_API_BASE` | `frontend/.env` or build arg | API address baked into the front-end (default `http://localhost:8000/api/v1`) |

Tests and lint:

```bash
cd backend
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest -q
.venv/bin/ruff check .
```

The same checks, plus a production front-end build, run in GitHub Actions on
every push and pull request.

## Personalised and location-aware thresholds

`/alerts`, `/crew/{id}/alerts`, `/crew/{id}/thresholds`,
`/crew/{id}/assessment` and `/crew/{id}/forecast` accept the same query
parameters. With none of them, behaviour is the original fixed thresholds.

| Parameter | Values | Meaning |
|---|---|---|
| `profile` | `generic` (default), `personal` | Fixed limits for everybody, or limits learned from the crew member's own history |
| `environment` | `earth_ground` (default), `atmosphere`, `launch`, `iss`, `mars_transit`, `mars_surface` | Where the crew member is now |
| `baseline_environment` | same values, default `earth_ground` | Where the baseline history was recorded. Use the same value as `environment` once the baseline has been re-learned in place |
| `days_in_environment` | integer, optional | Days spent in `environment`; lets gradual adaptations (core temperature in microgravity) ramp in. Omitted: they are not applied |

### How a personal limit is built

1. **Baseline:** the median of the crew member's own history and a robust
   spread (1.4826 × the median absolute deviation, the scaling of the
   Iglewicz–Hoaglin modified Z-score). The last 7 days are held out so a
   developing problem is not learned as normal.
2. **Limits:** warning at baseline ± 2.5 spreads (the MAD cut-off of Leys et
   al. 2013), critical at ± 3.5 (the Iglewicz–Hoaglin cut-off), with a floor
   on the spread so a steady person does not get a hair-trigger.
3. **Environment:** the expected value moves by the environment's shift.
4. **Safety rails:** personal limits may only tighten the generic ones,
   unless the baseline itself lies outside the generic normal range (the
   response then says so and recommends clinical review). Sleep, sleep
   quality, stress and mood are never relaxed: a chronic 6-hour sleeper has
   a deficiency to flag, not a personal normal. Absolute limits
   are always critical, and with fewer than 7 days of history the generic
   thresholds are used.

### What each environment changes

Only changes that published measurements support are applied; where the
evidence is missing or mixed the shift is zero.

| Environment | Change | Basis |
|---|---|---|
| `atmosphere` | SpO2 limits −3 points | Arterial O2 saturation 96% at sea level vs 93% at 7,500 ft; cabin limit 8,000 ft (National Research Council 2002) |
| `launch` | Heart-rate limits +30 bpm, ceiling 160 bpm | Apollo Commanders peaked near 120 bpm at touchdown; Shuttle crews reached 160 bpm after landing (NASA LSAH; EDOMP) |
| `iss`, `mars_transit` | Core temperature +1.0 °C ramped over 75 days; systolic pressure −7 mmHg | 11 ISS astronauts +1.01 °C, plateau around day 75 (Stahn 2017); blood pressure about 7–10 mmHg lower (Norsk 2015; Hughson 2017) |
| `iss`, `mars_transit` | Heart rate and sleep not moved | Heart rate unchanged; ISS crews sleep about 6 h against 8.5 h scheduled, a deficiency that should stay visible (Barger 2014) |
| `mars_surface` | No change | The effects of 0.38 g on human vital signs are unknown (Clément 2017; Jones 2021) |

`GET /api/v1/environments` returns every adjustment with its evidence, and
`GET /api/v1/environments/detect?body=earth&altitude_km=408&accel_g=1`
infers the environment from telemetry. Full derivations, the statistical
constants, the absolute limits and the known gaps are in
[docs/SOURCES.md](docs/SOURCES.md).

```text
# The same SpO2 of 94%, judged where the crew member actually is
GET /api/v1/crew/C001/assessment?environment=atmosphere

# Personal limits from a pre-flight baseline, 40 days into a station stay
GET /api/v1/crew/C001/thresholds?profile=personal&environment=iss&days_in_environment=40
```

## API reference

Base URL http://localhost:8000. Crew IDs `C001`–`C004`.

| Method | Path | Description |
|---|---|---|
| GET | `/` | Service health and crew list |
| GET | `/health` | Dataset status and snapshot freshness |
| GET | `/api/v1/crew` | Crew roster with lab and flag counts |
| GET | `/api/v1/crew/{id}/summary` | Per-crew summary (labs + vitals) |
| GET | `/api/v1/crew/{id}/labs` | Lab records, filterable and paginated |
| GET | `/api/v1/crew/{id}/vitals` | 30-day vitals time series |
| GET | `/api/v1/crew/{id}/thresholds` | Limits in force: generic vs personal, adjusted for the environment |
| GET | `/api/v1/crew/{id}/assessment` | Day-by-day nominal / warning / critical status (`days` 1–30, default 7) |
| GET | `/api/v1/crew/{id}/forecast` | Vitals trend forecast (`horizon` 1–14 days, default 7) |
| GET | `/api/v1/crew/{id}/report` | Weekly-style report for one crew member |
| GET | `/api/v1/crew/{id}/alerts` | Alerts for one crew member |
| GET | `/api/v1/alerts` | All alerts (labs + vitals + radiation) |
| GET | `/api/v1/environments` | Environments, their shifts and the evidence behind them |
| GET | `/api/v1/environments/detect` | Infer the environment from `body`, `altitude_km`, `accel_g` |
| GET | `/api/v1/space-weather` | DONKI events and radiation alert mapping |
| GET | `/api/v1/radiation` | GOES proton flux, S-scale, dose references |
| GET | `/api/v1/thresholds` | Generic alert thresholds |
| GET | `/api/v1/omics` | Proteomics / metabolomics summary |
| POST | `/api/v1/environment/refresh` | Re-fetch live DONKI and GOES snapshots |

Every alert and forecast carries a `data_source` label: `real` (OSDR labs),
`real_live` (NOAA / NASA feeds) or `synthetic` (generated vitals).

## Data

| Data | Records | Source | Real / synthetic |
|---|---|---|---|
| Clinical labs (blood count, metabolic, cardiovascular) | 1,280 | NASA OSDR OSD-569, OSD-575 (Inspiration4) | Real |
| Immune measurements (serum + urine) | 11,913 | NASA OSDR OSD-575, OSD-656 (Inspiration4) | Real |
| Proteomics / metabolomics changes | 300+ significant | NASA OSDR OSD-571 (Inspiration4) | Real |
| Space-weather events (SEP, CME, GST) | Last 30 days | NASA DONKI API | Real, live |
| Proton flux (GOES-18, ≥10 MeV) | 7 days, hourly | NOAA SWPC | Real, live |
| Vitals (heart rate, sleep, SpO2, stress, blood pressure, temperature, mood) | 30 days × 4 crew | Generated | Synthetic |

- No public astronaut wearable or actigraphy series exists, so vitals are
  generated demo data modelled on published healthy ranges.
- Lab values are flagged against OSDR reference ranges (clinical panels) or
  each crew member's own pre-flight median (immune panels).
- Reference dose rates (ISS ~0.5–1, Mars transit ~1.8, Mars surface ~0.64
  mSv/day) come from published MSL RAD measurements (Zeitlin et al. 2013,
  Hassler et al. 2014).

## Project structure

```text
.
  README.md, README.ar.md   # documentation (English, Arabic)
  CHANGELOG.md              # what changed in each revision
  LICENSE                   # MIT
  docs/SOURCES.md           # where every threshold and shift comes from
  docker-compose.yml        # back-end + front-end services
  .github/workflows/ci.yml  # lint, tests, front-end build
  data/                     # prepared datasets (JSON, CSV, raw downloads)
  backend/                  # FastAPI service (see backend/README.md)
  frontend/                 # React / Vite dashboard (see frontend/README.md)
```

**Back-end:** Python 3.12+ (3.14 in Docker), FastAPI, Pydantic, httpx,
Uvicorn. **Front-end:** React 19, Vite 6, Recharts, Three.js, lucide-react.
**Tests:** pytest, ruff, GitHub Actions. **Deployment:** Docker (front-end
built in a multi-stage image and served by nginx).

## Limitations

- **Lab data is not a Mars-mission dataset.** Inspiration4 was a three-day
  civilian flight in low Earth orbit with four crew. It is the best public
  human omics and clinical data available but does not represent a
  multi-month deep-space trip.
- **Vitals are synthetic**, so vitals alerts and the forecast demonstrate the
  pipeline, not real physiology. Alerts mix real and synthetic sources; use
  `data_source` to separate them.
- **Environment shifts come from small studies** (8–11 astronauts, five
  Apollo Commanders) and have not been clinically validated. No source was
  found for vitals at 0.38 g or for an Earth-launch heart-rate series, so
  those are documented gaps. Values need review by a flight surgeon before
  any real use.
- **The environment is a parameter** (or inferred from simple telemetry),
  not yet tied to a real mission timeline. The dashboard exposes both options
  (header selectors and the Thresholds page).
- **The forecast is a heuristic:** a robust linear trend over 14 days with no
  seasonality, no per-person model and no clinical validation.
- **No authentication.** Real health data would need access control, audit
  logging and privacy review before any deployment.

## Team — NASA 6 of October

| Member | Role |
|---|---|
| Ibrahim | Team lead |
| Nonaa (also called Nour) | Front-end, dashboard design |
| Yousef (Joe) | Design, data |
| Hala | Design |
| Malek | Back-end, data, code review |

## License

Code is released under the [MIT License](LICENSE). Data sources keep their
own terms (NASA OSDR, NASA DONKI, NOAA SWPC — all public).

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
