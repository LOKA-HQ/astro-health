"""Synthetic vitals time series (demo data).

No public astronaut wearable stream exists, so vitals are generated and
clearly labeled as synthetic in every API response.

C001 vitals come from data/vitals_timeseries_demo.json. Other crew members
get vitals from the same generator with a per-crew seed, so the dashboard
works for all four crew. The seed is derived from a SHA-256 hash of the
crew id, which is stable across processes (unlike Python's hash()).
"""

import hashlib
import random
from datetime import date, timedelta

from ..config import VITALS_DAYS, VITALS_START_DATE
from .loader import THRESHOLDS, VITALS_DEMO


def _warning_thresholds():
    """Warning thresholds from data/health_thresholds.json, so the
    generator and the served thresholds can never drift apart."""
    return {
        "hr_high": THRESHOLDS["resting_heart_rate_bpm"]["warning_high"],
        "sleep_low": THRESHOLDS["sleep_hours"]["warning_low"],
        "spo2_low": THRESHOLDS["spo2_percent"]["warning_low"],
        "stress_high": THRESHOLDS["stress_score"]["warning_high"],
        "bp_sys_high": THRESHOLDS["blood_pressure_systolic_mmhg"]["warning_high"],
        "bp_dia_high": THRESHOLDS["blood_pressure_diastolic_mmhg"]["warning_high"],
        "temp_high": THRESHOLDS["body_temperature_c"]["warning_high"],
        "temp_low": THRESHOLDS["body_temperature_c"]["warning_low"],
        "mood_low": THRESHOLDS["mood_score_1_10"]["warning_low"],
    }


def _day_alerts(hr, sleep, spo2, stress, bp_sys, bp_dia, temp, mood):
    """Structured alerts for one day, derived from the warning thresholds.
    Same format as the C001 demo file."""
    t = _warning_thresholds()
    alerts = []
    if hr > t["hr_high"]:
        alerts.append(
            {
                "indicator": "heart_rate",
                "level": "warning",
                "message": f"Resting heart rate above {t['hr_high']} BPM",
            }
        )
    if sleep < t["sleep_low"]:
        alerts.append(
            {
                "indicator": "sleep",
                "level": "warning",
                "message": f"Sleep under {t['sleep_low']} hours",
            }
        )
    if spo2 < t["spo2_low"]:
        alerts.append(
            {
                "indicator": "spo2",
                "level": "warning",
                "message": f"SpO2 below {t['spo2_low']}%",
            }
        )
    if stress > t["stress_high"]:
        alerts.append(
            {
                "indicator": "stress",
                "level": "warning",
                "message": "Stress score elevated",
            }
        )
    if bp_sys > t["bp_sys_high"] or bp_dia > t["bp_dia_high"]:
        alerts.append(
            {
                "indicator": "blood_pressure",
                "level": "warning",
                "message": f"Blood pressure above {t['bp_sys_high']}/"
                f"{t['bp_dia_high']} mmHg",
            }
        )
    if temp > t["temp_high"]:
        alerts.append(
            {
                "indicator": "body_temperature",
                "level": "warning",
                "message": f"Body temperature above {t['temp_high']} C",
            }
        )
    elif temp < t["temp_low"]:
        alerts.append(
            {
                "indicator": "body_temperature",
                "level": "warning",
                "message": f"Body temperature below {t['temp_low']} C",
            }
        )
    if mood < t["mood_low"]:
        alerts.append(
            {
                "indicator": "mood",
                "level": "warning",
                "message": "Mood score low",
            }
        )
    return alerts


def _synthetic_vitals(crew_id: str):
    seed = int(hashlib.sha256(crew_id.encode()).hexdigest(), 16)
    rng = random.Random(seed)
    base_hr = rng.randint(62, 74)
    base_sleep = rng.uniform(6.6, 7.6)
    start = date.fromisoformat(VITALS_START_DATE)
    # Two alert days per crew, placed at random within the window.
    alert_days = {rng.randint(4, 12), rng.randint(15, 25)}
    # Floor for normal-day sleep, so alert days come only from the
    # injected alert days, not from random noise.
    sleep_floor = _warning_thresholds()["sleep_low"] + 0.1
    days = []
    for i in range(VITALS_DAYS):
        d = start + timedelta(days=i)
        hr = base_hr + rng.randint(-5, 6)
        sleep = round(base_sleep + rng.uniform(-0.9, 0.9), 1)
        spo2 = round(rng.uniform(97.0, 99.2), 1)
        stress = rng.randint(12, 45)
        bp_sys = rng.randint(112, 126)
        bp_dia = rng.randint(70, 80)
        temp = round(rng.uniform(36.5, 37.2), 1)
        mood = rng.randint(6, 9)
        if i in alert_days:
            # Alert day: elevated resting HR, short sleep, high stress,
            # raised blood pressure and temperature, low mood.
            hr += 22
            sleep = round(sleep - 2.1, 1)
            stress = rng.randint(68, 82)
            spo2 = round(spo2 - 1.6, 1)
            bp_sys += rng.randint(20, 26)
            bp_dia += rng.randint(10, 14)
            temp = round(temp + rng.uniform(0.9, 1.2), 1)
            mood = rng.randint(2, 3)
        else:
            # Normal days stay inside the warning thresholds, so alert
            # days come only from the injected alert days, not from noise.
            sleep = max(sleep, sleep_floor)
        alerts = _day_alerts(hr, sleep, spo2, stress, bp_sys, bp_dia, temp, mood)
        status = "attention" if alerts else "nominal"
        days.append(
            {
                "date": d.isoformat(),
                "mission_day": i + 1,
                "resting_heart_rate_bpm": hr,
                "sleep_hours": sleep,
                "sleep_quality": rng.randint(68, 92)
                - (18 if status == "attention" else 0),
                "steps": rng.randint(5200, 9800),
                "spo2_percent": spo2,
                "stress_score": stress,
                "blood_pressure_systolic_mmhg": bp_sys,
                "blood_pressure_diastolic_mmhg": bp_dia,
                "body_temperature_c": temp,
                "mood_score": mood,
                "status": status,
                "alerts": alerts,
            }
        )
    return days


def get_vitals(crew_id: str):
    """30-day vitals for one crew member."""
    if crew_id == "C001":
        return VITALS_DEMO["days"]
    return _synthetic_vitals(crew_id)
