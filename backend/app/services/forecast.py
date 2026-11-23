"""Short-horizon vitals trend forecast.

For each vitals indicator we fit a robust straight line (Theil-Sen: the
median of all pairwise slopes) to the last N days and extrapolate it a few
days ahead. If the extrapolated line crosses a warning threshold inside the
horizon, the indicator is flagged. Theil-Sen is used instead of ordinary
least squares so that a single alert-day spike does not tilt the whole trend.

This is a transparent heuristic for the demo, not a clinical prediction
model. It runs on the synthetic vitals series, and every response says so.
"""

from statistics import median

from ..data import loader
from ..data.vitals import get_vitals
from . import environments, personalization

DEFAULT_WINDOW_DAYS = 14
DEFAULT_HORIZON_DAYS = 7
# A breach this many days out (or sooner) is rated "high" risk.
HIGH_RISK_WITHIN_DAYS = 3

# (vitals field, threshold key in health_thresholds.json, threshold name,
#  direction). direction "high" means values above the threshold are bad.
INDICATORS = [
    ("resting_heart_rate_bpm", "resting_heart_rate_bpm", "warning_high", "high"),
    ("sleep_hours", "sleep_hours", "warning_low", "low"),
    ("spo2_percent", "spo2_percent", "warning_low", "low"),
    ("stress_score", "stress_score", "warning_high", "high"),
    (
        "blood_pressure_systolic_mmhg",
        "blood_pressure_systolic_mmhg",
        "warning_high",
        "high",
    ),
    (
        "blood_pressure_diastolic_mmhg",
        "blood_pressure_diastolic_mmhg",
        "warning_high",
        "high",
    ),
    ("body_temperature_c", "body_temperature_c", "warning_high", "high"),
    ("mood_score", "mood_score_1_10", "warning_low", "low"),
]

RISK_RANK = {"high": 0, "moderate": 1, "low": 2}

DISCLAIMER = (
    "Heuristic trend extrapolation on synthetic demo vitals. Not a medical prediction."
)


def theil_sen(ys):
    """Robust line fit y = intercept + slope * x for x = 0..len(ys)-1.

    Returns (slope, intercept). Needs at least 2 points.
    """
    n = len(ys)
    if n < 2:
        raise ValueError("need at least 2 points")
    slopes = [(ys[j] - ys[i]) / (j - i) for i in range(n) for j in range(i + 1, n)]
    slope = median(slopes)
    intercept = median(y - slope * x for x, y in enumerate(ys))
    return slope, intercept


def _breached(value, threshold, direction):
    return value > threshold if direction == "high" else value < threshold


def _risk(days_to_breach):
    if days_to_breach is None:
        return "low"
    return "high" if days_to_breach <= HIGH_RISK_WITHIN_DAYS else "moderate"


def forecast_indicator(values, threshold, direction, horizon):
    """Forecast one indicator from its recent values (oldest first)."""
    slope, intercept = theil_sen(values)
    last_x = len(values) - 1
    current_fit = intercept + slope * last_x

    days_to_breach = None
    if _breached(current_fit, threshold, direction):
        days_to_breach = 0
    else:
        for step in range(1, horizon + 1):
            if _breached(intercept + slope * (last_x + step), threshold, direction):
                days_to_breach = step
                break

    return {
        "direction": direction,
        "threshold": threshold,
        "current_fit": round(current_fit, 2),
        "projected": round(intercept + slope * (last_x + horizon), 2),
        "slope_per_day": round(slope, 3),
        "days_to_breach": days_to_breach,
        "risk": _risk(days_to_breach),
    }


def forecast_from_days(
    days,
    thresholds,
    window=DEFAULT_WINDOW_DAYS,
    horizon=DEFAULT_HORIZON_DAYS,
):
    """Forecast every indicator from a list of vitals day dicts.

    Pure function: takes the data and thresholds as arguments, so it can be
    tested without loading the datasets.
    """
    recent = days[-window:]
    indicators = []
    if len(recent) >= 3:
        for field, key, threshold_name, direction in INDICATORS:
            threshold = thresholds[key][threshold_name]
            result = forecast_indicator(
                [d[field] for d in recent], threshold, direction, horizon
            )
            result["indicator"] = field
            indicators.append(result)
        indicators.sort(key=lambda i: RISK_RANK[i["risk"]])

    overall = min(
        (i["risk"] for i in indicators), key=lambda r: RISK_RANK[r], default="low"
    )
    return {
        "method": "Theil-Sen robust linear trend",
        "window_days": len(recent),
        "horizon_days": horizon,
        "data_source": "synthetic",
        "disclaimer": DISCLAIMER,
        "overall_risk": overall,
        "indicators": indicators,
    }


def crew_forecast(
    crew_id: str,
    horizon: int = DEFAULT_HORIZON_DAYS,
    profile: str = personalization.DEFAULT_PROFILE,
    environment: str = environments.DEFAULT_ENVIRONMENT,
    baseline_environment: str = environments.DEFAULT_ENVIRONMENT,
    days_in_environment: int | None = None,
):
    """Trend forecast for one crew member's vitals.

    The trend is compared with the effective thresholds: generic by
    default, or personal and/or environment-adjusted (see
    services/personalization.py).
    """
    days = get_vitals(crew_id)
    if profile == personalization.DEFAULT_PROFILE and (
        environment == environments.DEFAULT_ENVIRONMENT
    ):
        thresholds = loader.THRESHOLDS
    else:
        thresholds = personalization.flat_thresholds(
            personalization.effective_thresholds(
                days,
                loader.THRESHOLDS,
                profile,
                environment,
                baseline_environment,
                days_in_environment,
            )
        )
    result = forecast_from_days(days, thresholds, horizon=horizon)
    return {
        "crew_id": crew_id,
        "profile": profile,
        "environment": environment,
        **result,
    }
