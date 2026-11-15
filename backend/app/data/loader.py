"""Dataset loading and in-memory store.

All prepared JSON files are loaded once at startup and kept in memory.
The lab file is the largest (~4 MB, 13,193 records); the API only filters
it, so no database is needed for the demo.

Live-refreshable datasets (space weather, radiation) can be replaced at
runtime through set_space_weather / set_radiation, which also persist the
new snapshot to disk.
"""

import json
from pathlib import Path

from ..config import DATA_DIR

# Lab statuses that count as flagged. "high"/"low" are out of the OSDR
# reference range (clinical panels). "elevated/reduced_vs_baseline" are
# immune-panel deviations from the crew member's own pre-flight median.
FLAGGED = {"high", "low", "elevated_vs_baseline", "reduced_vs_baseline"}


def _load_json(path: Path):
    with open(path) as f:
        return json.load(f)


def _save_json(path: Path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=1)


# Static datasets (prepared during data analysis, not refreshed at runtime).
LABS = _load_json(DATA_DIR / "astronaut_health_indicators.json")
VITALS_DEMO = _load_json(DATA_DIR / "vitals_timeseries_demo.json")
THRESHOLDS = _load_json(DATA_DIR / "health_thresholds.json")
OMICS = _load_json(DATA_DIR / "omics_summary.json")

# Refreshable datasets (live snapshots; see services/environment.py).
SPACE_WEATHER = _load_json(DATA_DIR / "space_weather.json")
RADIATION = _load_json(DATA_DIR / "radiation_environment.json")

CREW = LABS["crew"]  # ["C001", "C002", "C003", "C004"]
TIMEPOINTS = LABS["timepoints"]  # L-92 .. R+194 (L- pre-flight, R+ post-flight)
RECORDS = LABS["records"]


def records_for_crew(crew_id: str):
    """All lab records for one crew member."""
    return [r for r in RECORDS if r["crew"] == crew_id]


def flagged(records):
    """Only the records whose status counts as flagged."""
    return [r for r in records if r["status"] in FLAGGED]


def top_flagged(flagged_records, n=5):
    """Most frequently flagged indicators, as [{indicator, count}]."""
    counts = {}
    for r in flagged_records:
        counts[r["indicator"]] = counts.get(r["indicator"], 0) + 1
    return [
        {"indicator": k, "count": v}
        for k, v in sorted(counts.items(), key=lambda kv: -kv[1])[:n]
    ]


def set_space_weather(data):
    """Replace the in-memory space-weather snapshot and persist it."""
    global SPACE_WEATHER
    SPACE_WEATHER = data
    _save_json(DATA_DIR / "space_weather.json", data)


def set_radiation(data):
    """Replace the in-memory radiation snapshot and persist it."""
    global RADIATION
    RADIATION = data
    _save_json(DATA_DIR / "radiation_environment.json", data)
