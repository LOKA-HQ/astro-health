"""Application configuration.

Central place for paths, external API endpoints, and constants.
Environment variables override defaults where noted. A backend/.env file
is loaded if present (see .env.example).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Project layout: backend/app/config.py, so the project root is 3 levels up.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = Path(os.environ.get("ASTRO_DATA_DIR", PROJECT_ROOT / "data"))

API_VERSION = "0.1.0"
API_V1_PREFIX = "/api/v1"

# NASA DONKI (space weather). DEMO_KEY works for the demo; set NASA_API_KEY
# to a free key from https://api.nasa.gov to lift the rate limits.
NASA_API_KEY = os.environ.get("NASA_API_KEY", "DEMO_KEY")
DONKI_BASE_URL = "https://api.nasa.gov/DONKI"

# NOAA SWPC GOES proton flux. No key required.
GOES_PROTONS_URL = (
    "https://services.swpc.noaa.gov/json/goes/primary/integral-protons-7-day.json"
)

# Synthetic vitals demo window.
VITALS_START_DATE = "2026-11-14"
VITALS_DAYS = 30

# Report window in days (crew weekly report uses the last N vitals days).
REPORT_WINDOW_DAYS = 7

# A crew member is flagged "attention" in reports above this many clinical
# out-of-range lab values.
ATTENTION_CLINICAL_OOR = 10
