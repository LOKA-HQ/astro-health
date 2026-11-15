# Test results — Nov 14, 2026, ~12:55 PM (Africa/Cairo)

Full suite: **23 passed, 0 failed** (`pytest -v`, 1.30s).
Lint: `ruff check` — all checks passed. Format: `ruff format --check` —
22 files already formatted. Dependency audit: `pip-audit` — no known
vulnerabilities. Docker image (Python 3.14.10) verified live: all
endpoints tested in the container.

Regenerate with: `cd backend && .venv/bin/pytest -v`

## API tests (17) — tests/test_api.py

| Test | Result | Checks |
|---|---|---|
| test_root | PASSED | `/` returns the 4-crew roster |
| test_health | PASSED | `/health` ok, 4 crew, 13,193 lab records |
| test_crew_list | PASSED | Roster counts; C001=2, C003=20 clinical out-of-range |
| test_crew_summary | PASSED | C003 summary: 456 flagged, 30 vitals days, 2 alert days |
| test_crew_labs_filters_and_pagination | PASSED | panel/status filters + limit/offset pagination |
| test_crew_vitals_deterministic | PASSED | Generated vitals identical across calls |
| test_crew_report | PASSED | Weekly report structure + overall status |
| test_alerts | PASSED | 48 alerts (38 clinical + 9 vitals + 1 radiation) |
| test_environment_endpoints | PASSED | space-weather, radiation, thresholds, omics all 200 |
| test_unknown_crew_404 | PASSED | Unknown crew id returns 404 |
| test_labs_invalid_pagination_422 | PASSED | Negative / over-max limit/offset rejected (422) |
| test_labs_offset_beyond_total | PASSED | Offset past the end returns empty page, total 3047 |
| test_crew_vitals_days_param | PASSED | `?days=7` returns last 7 days; 0/31/-3 rejected (422) |
| test_crew_alerts | PASSED | C003 alerts = 22, all C003, no radiation alert |
| test_alerts_sorted_by_severity | PASSED | critical, then warning, then info; radiation last |
| test_vitals_alerts_use_thresholds | PASSED | Vitals alert messages use served threshold values |
| test_vitals_new_indicators | PASSED | BP, temperature, mood present for all crew; in range on normal days, flagged on alert days; summary/report averages |

## Security tests (6) — tests/test_security.py

| Test | Result | Checks |
|---|---|---|
| test_traversal_crew_ids_404 | PASSED | `..`, encoded `../` paths return 404, no file content |
| test_injection_strings_are_harmless | PASSED | SQL/NoSQL/XSS-style filter values return 0 rows, no crash |
| test_error_responses_hide_internals | PASSED | 404/422 bodies contain no tracebacks or file paths |
| test_very_long_crew_id_404 | PASSED | 1000-char crew id returns 404 |
| test_refresh_requires_post | PASSED | GET on the refresh endpoint returns 405 |
| test_api_responses_are_json | PASSED | API responses served as application/json |
