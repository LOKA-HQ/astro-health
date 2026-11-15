# Astro Health — update notes

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
