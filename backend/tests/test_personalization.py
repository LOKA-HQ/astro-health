"""Tests for personal and environment-aware thresholds (no HTTP)."""

import pytest

from app.data.loader import THRESHOLDS
from app.schemas.responses import (
    AlertsResponse,
    CrewAssessment,
    CrewForecast,
    CrewThresholds,
)
from app.services import alerts, environments, forecast, personalization

HR = "resting_heart_rate_bpm"


def _day(i, **overrides):
    day = {
        "date": f"2026-12-{i + 1:02d}",
        "mission_day": i + 1,
        HR: 70,
        "sleep_hours": 7.5,
        "sleep_quality": 80,
        "spo2_percent": 98.0,
        "stress_score": 30,
        "blood_pressure_systolic_mmhg": 118,
        "blood_pressure_diastolic_mmhg": 76,
        "body_temperature_c": 36.8,
        "mood_score": 8,
    }
    day.update(overrides)
    return day


def _history(n, **per_field):
    """n days; per_field maps field -> callable(day_index)."""
    return [_day(i, **{f: fn(i) for f, fn in per_field.items()}) for i in range(n)]


def _status(day, effective, field=HR):
    assessed = personalization.assess_day(day, effective)
    return next(i for i in assessed["indicators"] if i["indicator"] == field)


def _hypertensive_history(n=30):
    # Resting heart rate bouncing between 100 and 120 every day.
    return _history(n, **{HR: lambda i: 100 + (i * 7) % 21})


# ---- baseline ---------------------------------------------------------


def test_baseline_is_robust_to_outliers():
    values = [70] * 12 + [140, 40]
    center, sigma = personalization.compute_baseline(values)
    assert center == 70
    assert sigma == 0


def test_baseline_holds_out_recent_days():
    days = _history(30)
    assert len(personalization.baseline_history(days)) == 23
    # Too short to hold anything out: use everything.
    assert len(personalization.baseline_history(_history(10))) == 10


# ---- the "hypertensive crew member" case -----------------------------


def test_same_reading_is_critical_generic_but_normal_personal():
    days = _hypertensive_history()
    today = _day(30, **{HR: 108})

    generic = personalization.effective_thresholds(days, THRESHOLDS, "generic")
    assert _status(today, generic)["status"] == "critical"

    personal = personalization.effective_thresholds(days, THRESHOLDS, "personal")
    assert _status(today, personal)["status"] == "nominal"


def test_personal_baseline_outside_normal_is_reported_for_review():
    personal = personalization.effective_thresholds(
        _hypertensive_history(), THRESHOLDS, "personal"
    )
    rec = personal["indicators"][HR]
    assert rec["baseline_outside_generic_normal"] is True
    assert "clinical review" in rec["baseline_note"]
    assert rec["source"] == "personal"


def test_absolute_limit_cannot_be_relaxed_by_baseline():
    personal = personalization.effective_thresholds(
        _hypertensive_history(), THRESHOLDS, "personal"
    )
    assert _status(_day(30, **{HR: 160}), personal)["status"] == "critical"
    limit = personal["indicators"][HR]["thresholds"]["critical_high"]
    assert limit <= personalization.ABSOLUTE_LIMITS[HR]["high"]


def test_personal_may_tighten_a_steady_person():
    # Very steady resting heart rate of 62: 82 is a big jump for them but
    # still under the generic warning limit of 90.
    days = _history(30, **{HR: lambda i: 62 + (i % 2)})
    today = _day(30, **{HR: 82})
    assert _status(today, personalization.effective_thresholds(
        days, THRESHOLDS, "generic"))["status"] == "nominal"
    assert _status(today, personalization.effective_thresholds(
        days, THRESHOLDS, "personal"))["status"] != "nominal"


def test_personal_never_relaxes_generic_when_baseline_is_normal():
    # Sleep swinging between 6.2 and 7.8 h (baseline 7.0, inside the generic
    # normal range) gives a wide personal band; it must not be allowed to
    # drop below the generic warning limit of 6 h.
    days = _history(30, sleep_hours=lambda i: 6.2 if i % 2 else 7.8)
    personal = personalization.effective_thresholds(days, THRESHOLDS, "personal")
    th = personal["indicators"]["sleep_hours"]["thresholds"]
    assert th["warning_low"] >= THRESHOLDS["sleep_hours"]["warning_low"]
    assert th["critical_low"] >= THRESHOLDS["sleep_hours"]["critical_low"]
    assert personal["indicators"]["sleep_hours"]["baseline_outside_generic_normal"] is False


def test_chronic_short_sleep_is_never_learned_as_normal():
    # A crew member who always sleeps 5.5-6.5 h has a baseline outside the
    # normal range, but that is a deficiency to flag, not a personal normal.
    days = _history(30, sleep_hours=lambda i: 5.5 + (i % 3) * 0.5)
    personal = personalization.effective_thresholds(days, THRESHOLDS, "personal")
    rec = personal["indicators"]["sleep_hours"]
    assert rec["baseline_outside_generic_normal"] is True
    assert "never relaxed" in rec["baseline_note"]
    assert rec["thresholds"]["warning_low"] >= THRESHOLDS["sleep_hours"]["warning_low"]
    assert rec["thresholds"]["critical_low"] >= THRESHOLDS["sleep_hours"]["critical_low"]
    today = _day(30, sleep_hours=5.5)
    assert _status(today, personal, "sleep_hours")["status"] != "nominal"


def test_only_performance_indicators_are_tighten_only():
    assert {
        "sleep_hours", "sleep_quality", "stress_score", "mood_score"
    } == personalization.TIGHTEN_ONLY
    # Heart rate can still relax for a baseline outside the normal range.
    assert HR not in personalization.TIGHTEN_ONLY


def test_too_little_history_falls_back_to_generic():
    personal = personalization.effective_thresholds(
        _history(5), THRESHOLDS, "personal"
    )
    assert personal["baseline_days"] == 0
    assert all(r["source"] == "generic_fallback" for r in personal["indicators"].values())
    generic = personalization.effective_thresholds(_history(5), THRESHOLDS, "generic")
    assert personal["indicators"][HR]["thresholds"] == generic["indicators"][HR]["thresholds"]


def test_unknown_profile_or_environment_is_rejected():
    with pytest.raises(ValueError):
        personalization.effective_thresholds(_history(30), THRESHOLDS, "average")
    with pytest.raises(KeyError):
        personalization.effective_thresholds(
            _history(30), THRESHOLDS, "generic", "venus"
        )


# ---- environments -----------------------------------------------------


def test_generic_default_environment_matches_the_fixed_thresholds():
    eff = personalization.effective_thresholds(_history(30), THRESHOLDS, "generic")
    flat = personalization.flat_thresholds(eff)
    for key, rec in flat.items():
        for name, value in rec.items():
            assert value == THRESHOLDS[key][name], (key, name)


def test_same_spo2_reading_depends_on_where_you_are():
    days = _history(30)
    today = _day(30, spo2_percent=94.0)
    ground = personalization.effective_thresholds(days, THRESHOLDS, "generic")
    cabin = personalization.effective_thresholds(
        days, THRESHOLDS, "generic", "atmosphere"
    )
    assert _status(today, ground, "spo2_percent")["status"] != "nominal"
    assert _status(today, cabin, "spo2_percent")["status"] == "nominal"


def test_launch_expects_a_high_heart_rate():
    days = _history(30)
    today = _day(30, **{HR: 120})
    ground = personalization.effective_thresholds(days, THRESHOLDS, "generic")
    launch = personalization.effective_thresholds(
        days, THRESHOLDS, "generic", "launch"
    )
    assert _status(today, ground)["status"] == "critical"
    assert _status(today, launch)["status"] == "nominal"
    # But it still has a ceiling.
    assert _status(_day(30, **{HR: 185}), launch)["status"] == "critical"


SBP = "blood_pressure_systolic_mmhg"
TEMP = "body_temperature_c"


def test_personal_expected_value_moves_with_the_environment():
    days = _history(30)  # baseline recorded on Earth: 118 mmHg systolic
    iss = personalization.effective_thresholds(days, THRESHOLDS, "personal", "iss")
    rec = iss["indicators"][SBP]
    assert rec["baseline_median"] == 118
    assert rec["environment_shift"] == -7
    assert rec["expected_value"] == 118 - 7
    # Heart rate is not moved in microgravity (Norsk 2015, Hughson 2017).
    assert iss["indicators"][HR]["environment_shift"] == 0


def test_baseline_learned_in_place_needs_no_shift():
    days = _history(30)
    in_place = personalization.effective_thresholds(
        days, THRESHOLDS, "personal", "iss", baseline_environment="iss"
    )
    for field in (SBP, TEMP):
        rec = in_place["indicators"][field]
        assert rec["environment_shift"] == 0
        assert rec["expected_value"] == rec["baseline_median"]


# ---- shifts come from the published evidence ----------------------------


def test_cabin_altitude_lowers_spo2_limits_by_three_points():
    # Arterial saturation 96% at sea level vs 93% at 7,500 ft (NRC 2002).
    ground = personalization.effective_thresholds(_history(30), THRESHOLDS, "generic")
    cabin = personalization.effective_thresholds(
        _history(30), THRESHOLDS, "generic", "atmosphere"
    )
    g = ground["indicators"]["spo2_percent"]["thresholds"]
    c = cabin["indicators"]["spo2_percent"]["thresholds"]
    assert c["warning_low"] == pytest.approx(g["warning_low"] - 3)
    # The 90% absolute floor is kept.
    assert c["critical_low"] >= 90
    assert cabin["indicators"][HR]["environment_shift"] == 0


def test_launch_shift_covers_the_apollo_descent_peak():
    # Apollo Commanders peaked near 120 bpm; generic warning is 90 -> +30.
    launch = personalization.effective_thresholds(
        _history(30), THRESHOLDS, "generic", "launch"
    )
    th = launch["indicators"][HR]["thresholds"]
    assert th["warning_high"] == THRESHOLDS[HR]["warning_high"] + 30
    assert th["warning_high"] >= 120
    assert environments.ENVIRONMENTS["launch"]["absolute_overrides"][HR]["high"] == 160


def test_microgravity_does_not_move_heart_rate_or_sleep():
    for key in ("iss", "mars_transit"):
        shifts = environments.ENVIRONMENTS[key]["shifts"]
        assert HR not in shifts
        assert "sleep_hours" not in shifts


def test_mars_surface_has_no_shift_because_there_is_no_human_data():
    env = environments.ENVIRONMENTS["mars_surface"]
    assert env["shifts"] == {}
    assert env["sources"]


def test_core_temperature_shift_ramps_over_75_days():
    env = environments.ENVIRONMENTS["iss"]
    assert environments.shift_for(env, TEMP) == 0  # time in orbit unknown
    assert environments.shift_for(env, TEMP, 0) == 0
    assert environments.shift_for(env, TEMP, 75) == pytest.approx(1.0)
    assert environments.shift_for(env, TEMP, 150) == pytest.approx(1.0)  # capped
    assert environments.shift_for(env, TEMP, 30) == pytest.approx(0.4)
    assert environments.full_shift_for(env, TEMP) == 1.0


def test_fever_is_not_hidden_early_in_flight():
    days = _history(30)
    fever = _day(30, **{TEMP: 38.4})
    unknown = personalization.effective_thresholds(days, THRESHOLDS, "generic", "iss")
    adapted = personalization.effective_thresholds(
        days, THRESHOLDS, "generic", "iss", days_in_environment=90
    )
    # Without days_in_environment the temperature limits are not relaxed.
    assert unknown["indicators"][TEMP]["environment_shift"] == 0
    assert _status(fever, unknown, TEMP)["status"] == "warning"
    # Once adapted (+1.0 C) the same reading falls inside the shifted limits.
    assert adapted["indicators"][TEMP]["environment_shift"] == 1.0
    assert _status(fever, adapted, TEMP)["status"] == "nominal"


def test_every_environment_cites_known_references():
    for key, env in environments.ENVIRONMENTS.items():
        assert env["basis"], key
        assert set(env["sources"]) <= set(environments.REFERENCES), key
        if env["shifts"]:
            assert env["sources"], f"{key} has shifts but no sources"
    for ref in environments.REFERENCES.values():
        assert ref["citation"] and ref["url"].startswith("https://") and ref["finding"]


def test_statistical_constants_follow_the_cited_sources():
    assert personalization.K_WARNING == 2.5  # Leys et al. 2013
    assert personalization.K_CRITICAL == 3.5  # Iglewicz & Hoaglin / NIST
    assert pytest.approx(1 / 0.6745, abs=1e-3) == personalization.MAD_TO_SIGMA


def test_absolute_limits_match_the_cited_guidelines():
    lim = personalization.ABSOLUTE_LIMITS
    assert lim["blood_pressure_systolic_mmhg"]["high"] == 180  # AHA crisis
    assert lim["blood_pressure_diastolic_mmhg"]["high"] == 120  # AHA crisis
    assert lim["spo2_percent"]["low"] == 90  # hypoxaemia
    assert lim[TEMP] == {"high": 40.0, "low": 35.0}  # heat stroke / hypothermia
    assert lim[HR]["high"] == 150  # AHA ACLS tachyarrhythmia


def test_environment_definitions_only_use_known_indicators():
    for key, env in environments.ENVIRONMENTS.items():
        assert set(env["shifts"]) <= set(personalization.INDICATOR_KEYS), key
        assert set(env["absolute_overrides"]) <= set(personalization.INDICATOR_KEYS), key
        assert env["spread_factor"] >= 1.0, key
    assert environments.DEFAULT_ENVIRONMENT in environments.ENVIRONMENTS


@pytest.mark.parametrize(
    "kwargs, expected",
    [
        ({}, "earth_ground"),
        ({"altitude_km": 10.0, "accel_g": 1.0}, "atmosphere"),
        ({"altitude_km": 20.0, "accel_g": 3.5}, "launch"),
        ({"altitude_km": 408.0}, "iss"),
        ({"altitude_km": 400_000.0}, "mars_transit"),
        ({"body": "mars", "altitude_km": 0.0, "accel_g": 0.38}, "mars_surface"),
        ({"body": "mars", "altitude_km": 3000.0, "accel_g": 0.0}, "mars_transit"),
    ],
)
def test_detect_environment(kwargs, expected):
    result = environments.detect_environment(**kwargs)
    assert result["environment"] == expected
    assert result["reason"]


def test_detect_environment_rejects_unknown_body():
    with pytest.raises(ValueError):
        environments.detect_environment(body="venus")


# ---- crew-level outputs match the API response models ------------------


@pytest.mark.parametrize("profile", ["generic", "personal"])
@pytest.mark.parametrize("environment", ["earth_ground", "iss", "launch"])
def test_crew_outputs_validate_against_schemas(profile, environment):
    CrewThresholds.model_validate(
        personalization.crew_thresholds("C001", profile, environment)
    )
    assessment = CrewAssessment.model_validate(
        personalization.crew_assessment("C001", profile, environment, days=5)
    )
    assert len(assessment.days) == 5
    assert all(len(d.indicators) == 9 for d in assessment.days)
    CrewForecast.model_validate(forecast.crew_forecast("C001", 7, profile, environment))
    AlertsResponse.model_validate(alerts.build_alerts(profile, environment))


# ---- alerts and forecast honour the profile ----------------------------


def test_default_alerts_are_unchanged():
    built = alerts.build_alerts()
    assert built["count"] == 48
    assert built["profile"] == "generic"
    assert built["environment"] == "earth_ground"


def test_personal_alerts_use_personal_levels_and_keep_provenance():
    built = alerts.build_alerts("personal", "iss")
    vitals = [a for a in built["alerts"] if a["type"] == "vitals"]
    assert vitals
    for a in vitals:
        assert a["level"] in ("warning", "critical")
        assert a["data_source"] == "synthetic"
        assert a["alerts"]
        assert all("personal" in x["message"] or "generic" in x["message"] for x in a["alerts"])
    # Lab and radiation alerts are untouched by the profile.
    default = alerts.build_alerts()
    for kind in ("lab", "radiation"):
        assert sum(1 for a in built["alerts"] if a["type"] == kind) == sum(
            1 for a in default["alerts"] if a["type"] == kind
        )


def test_alerts_for_crew_filters_to_that_crew():
    crew_alerts = alerts.alerts_for_crew("C002", "personal", "iss")
    assert crew_alerts["alerts"]
    assert {a["crew_id"] for a in crew_alerts["alerts"]} == {"C002"}


def test_forecast_uses_effective_thresholds():
    generic = forecast.crew_forecast("C001")
    personal = forecast.crew_forecast("C001", 7, "personal", "iss")
    assert generic["profile"] == "generic"
    assert personal["profile"] == "personal"
    assert personal["environment"] == "iss"
    thresholds = {i["indicator"]: i["threshold"] for i in generic["indicators"]}
    personal_thresholds = {i["indicator"]: i["threshold"] for i in personal["indicators"]}
    assert thresholds != personal_thresholds
