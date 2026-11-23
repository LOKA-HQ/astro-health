# Astro Health — update notes

## Personalised and location-aware thresholds

- **Personal thresholds** (`profile=personal`): warning and critical limits
  learned from each crew member's own history (median and MAD-based spread,
  last 7 days held out), with safety rails: they may only tighten the
  generic limits unless the baseline itself is outside the normal range,
  absolute limits are always critical, sleep / sleep quality / stress / mood
  are never relaxed, and short histories fall back to the generic
  thresholds.
- **Location awareness** (`environment=`): earth_ground, atmosphere, launch,
  iss, mars_transit and mars_surface, selectable or inferred from telemetry
  (`/environments/detect`). Every shift is tied to a published source;
  where evidence is missing or mixed the shift is zero. Core temperature in
  microgravity ramps in over 75 days (`days_in_environment`).
- New endpoints: `/crew/{id}/thresholds`, `/crew/{id}/assessment`,
  `/crew/{id}/forecast`, `/environments`, `/environments/detect`. The alerts,
  per-crew alerts and forecast endpoints accept the same options; defaults
  keep the original behaviour.
- Alerts carry a `data_source` (`real`, `real_live`, `synthetic`).
- **7-day trend forecast** per crew member (robust Theil-Sen trend).
- `docs/SOURCES.md` documents where every number comes from. Unverifiable
  attributions in `data/health_thresholds.json` notes were replaced.
- MIT license, GitHub Actions CI (ruff, pytest, front-end build), English
  and Arabic README, `.gitignore` cleanup. `CHANGELOG_FIXES.md` became this
  file.

## Earlier revision

## Improvements in this revision

- Laboratory results are fetched across every API page instead of stopping at the first 1,000 records.
- Laboratory table uses 50-row client-side pages with Previous/Next controls and resets to page 1 when the filter changes.
- Refresh controls now call the backend's `POST /api/v1/environment/refresh` endpoint to attempt fresh NASA DONKI and NOAA SWPC snapshots.
- Partial external refresh failures are surfaced while retaining the last saved snapshots.
- Synthetic crew vitals are explicitly labelled as demo data; generic telemetry labels no longer imply live wearable measurements.
- Removed the hard-coded mission day/progress percentage display.
- CORS is restricted to configured frontend origins, with localhost Vite defaults and `ASTRO_CORS_ORIGINS` for deployment.
- Frontend package versions are pinned instead of using `latest`.

## Verification

- Backend test suite: 24 passed.
- Python compile check: passed.
- Frontend production build: not verified in this environment because frontend dependencies are not installed and package registry access is unavailable (`vite: not found`). Run `npm install` followed by `npm run build` in `frontend/` on a machine with registry access.
