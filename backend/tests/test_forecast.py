"""Tests for the vitals trend forecast (pure functions, no HTTP)."""

import pytest

from app.services import forecast

THRESHOLDS = {
    "resting_heart_rate_bpm": {"warning_high": 90},
    "sleep_hours": {"warning_low": 6},
    "spo2_percent": {"warning_low": 96},
    "stress_score": {"warning_high": 65},
    "blood_pressure_systolic_mmhg": {"warning_high": 140},
    "blood_pressure_diastolic_mmhg": {"warning_high": 90},
    "body_temperature_c": {"warning_high": 38.0},
    "mood_score_1_10": {"warning_low": 4},
}


def _days(n, **overrides):
    """n flat vitals days; overrides map field -> callable(day_index)."""
    base = {
        "resting_heart_rate_bpm": 68,
        "sleep_hours": 7.2,
        "spo2_percent": 98.0,
        "stress_score": 30,
        "blood_pressure_systolic_mmhg": 118,
        "blood_pressure_diastolic_mmhg": 76,
        "body_temperature_c": 36.8,
        "mood_score": 8,
    }
    days = []
    for i in range(n):
        day = dict(base)
        for field, fn in overrides.items():
            day[field] = fn(i)
        days.append(day)
    return days


def _find(result, indicator):
    return next(i for i in result["indicators"] if i["indicator"] == indicator)


def test_theil_sen_recovers_exact_line():
    slope, intercept = forecast.theil_sen([3 + 2 * x for x in range(10)])
    assert slope == pytest.approx(2.0)
    assert intercept == pytest.approx(3.0)


def test_theil_sen_ignores_single_outlier():
    ys = [10.0] * 14
    ys[6] = 100.0  # one alert-day style spike
    slope, intercept = forecast.theil_sen(ys)
    assert slope == pytest.approx(0.0)
    assert intercept == pytest.approx(10.0)


def test_theil_sen_needs_two_points():
    with pytest.raises(ValueError):
        forecast.theil_sen([1.0])


def test_flat_vitals_are_low_risk():
    result = forecast.forecast_from_days(_days(30), THRESHOLDS)
    assert result["overall_risk"] == "low"
    assert all(i["days_to_breach"] is None for i in result["indicators"])
    assert result["data_source"] == "synthetic"


def test_rising_heart_rate_flags_breach_within_horizon():
    days = _days(30, resting_heart_rate_bpm=lambda i: 70 + i * 0.5)
    # Last 14 days: 78..84.5, slope 0.5/day. The line crosses 90 about 11
    # days after the last point: outside a 7 day horizon, inside 14.
    result = forecast.forecast_from_days(days, THRESHOLDS, horizon=7)
    hr = _find(result, "resting_heart_rate_bpm")
    assert hr["risk"] == "low"

    result = forecast.forecast_from_days(days, THRESHOLDS, horizon=14)
    hr = _find(result, "resting_heart_rate_bpm")
    assert hr["risk"] == "moderate"
    assert 10 <= hr["days_to_breach"] <= 12
    assert result["overall_risk"] == "moderate"


def test_fast_rise_is_high_risk():
    days = _days(30, resting_heart_rate_bpm=lambda i: 60 + i * 1.0)
    # Last 14 days: 76..89, slope 1/day, crosses 90 on the next day.
    result = forecast.forecast_from_days(days, THRESHOLDS, horizon=7)
    hr = result["indicators"][0]  # sorted most risky first
    assert hr["indicator"] == "resting_heart_rate_bpm"
    assert hr["risk"] == "high"
    assert hr["days_to_breach"] <= forecast.HIGH_RISK_WITHIN_DAYS
    assert result["overall_risk"] == "high"


def test_falling_sleep_uses_low_direction():
    days = _days(30, sleep_hours=lambda i: 8.0 - i * 0.1)
    # Last 14 days: 5.1 .. 6.4 falling 0.1/day -> already near threshold 6.
    result = forecast.forecast_from_days(days, THRESHOLDS, horizon=7)
    sleep = _find(result, "sleep_hours")
    assert sleep["direction"] == "low"
    assert sleep["risk"] in ("moderate", "high")


def test_already_beyond_threshold_is_breached_now():
    days = _days(30, stress_score=lambda i: 80)
    result = forecast.forecast_from_days(days, THRESHOLDS)
    stress = _find(result, "stress_score")
    assert stress["days_to_breach"] == 0
    assert stress["risk"] == "high"


def test_too_few_days_returns_low_with_no_indicators():
    result = forecast.forecast_from_days(_days(2), THRESHOLDS)
    assert result["indicators"] == []
    assert result["overall_risk"] == "low"


def test_indicators_sorted_most_risky_first():
    days = _days(30, stress_score=lambda i: 80)
    result = forecast.forecast_from_days(days, THRESHOLDS)
    ranks = [forecast.RISK_RANK[i["risk"]] for i in result["indicators"]]
    assert ranks == sorted(ranks)
