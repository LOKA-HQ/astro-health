"""Safety invariants of personal / environment-aware thresholds and the forecast.

The scenario tests in test_personalization.py and test_forecast.py check
individual behaviours. These tests check properties that must hold for every
combination the API accepts, on the real crew data, so a future change to a
shift, a constant or a clamp cannot quietly break a safety guarantee.
"""

import math

import pytest

from app.data.loader import THRESHOLDS
from app.data.vitals import get_vitals
from app.services import environments, forecast, personalization

CREW = ["C001", "C002", "C003", "C004"]
DAYS_IN_ENV = [None, 0, 40, 90]
TOL = 0.011  # thresholds are rounded to 2 decimals


def _all_combinations():
    for crew in CREW:
        for profile in personalization.PROFILES:
            for env in environments.ENVIRONMENTS:
                for base_env in {environments.DEFAULT_ENVIRONMENT, env}:
                    for dive in DAYS_IN_ENV:
                        yield crew, profile, env, base_env, dive


def _effective(crew, profile, env, base_env, dive):
    return personalization.effective_thresholds(
        get_vitals(crew), THRESHOLDS, profile, env, base_env, dive
    )


def test_sweep_covers_every_crew_environment_and_profile():
    combos = list(_all_combinations())
    assert {c[0] for c in combos} == set(CREW)
    assert {c[2] for c in combos} == set(environments.ENVIRONMENTS)
    assert {c[1] for c in combos} == set(personalization.PROFILES)
    assert len(combos) > 300  # guards against the sweep silently shrinking


def test_every_combination_yields_finite_ordered_thresholds():
    for combo in _all_combinations():
        eff = _effective(*combo)
        assert set(eff["indicators"]) == set(personalization.INDICATOR_KEYS), combo
        for field, rec in eff["indicators"].items():
            th = rec["thresholds"]
            where = (combo, field)
            assert th, where
            assert all(math.isfinite(v) for v in th.values()), where
            # warning must trigger before critical, on each side
            if {"warning_high", "critical_high"} <= th.keys():
                assert th["warning_high"] <= th["critical_high"], where
            if {"warning_low", "critical_low"} <= th.keys():
                assert th["warning_low"] >= th["critical_low"], where
            # the low side must stay below the high side
            if {"warning_low", "warning_high"} <= th.keys():
                assert th["warning_low"] < th["warning_high"], where


def test_absolute_safety_limits_hold_in_every_combination():
    for combo in _all_combinations():
        env = environments.get_environment(combo[2])
        eff = _effective(*combo)
        for field, rec in eff["indicators"].items():
            limits = dict(personalization.ABSOLUTE_LIMITS.get(field, {}))
            limits.update(env["absolute_overrides"].get(field, {}))
            th = rec["thresholds"]
            if "high" in limits and "critical_high" in th:
                assert th["critical_high"] <= limits["high"] + TOL, (combo, field)
            if "low" in limits and "critical_low" in th:
                assert th["critical_low"] >= limits["low"] - TOL, (combo, field)


def test_tighten_only_indicators_are_never_looser_than_generic():
    """Sleep, sleep quality, stress and mood: a chronic deficiency is flagged,
    never learned as normal. Compared with the generic limits as they apply in
    the same environment."""
    for combo in _all_combinations():
        crew, profile, env_key, _, dive = combo
        env = environments.get_environment(env_key)
        eff = _effective(*combo)
        for field in personalization.TIGHTEN_ONLY:
            rec = eff["indicators"][field]
            shift = environments.shift_for(env, field, dive)
            for name, generic_value in rec["generic"].items():
                limit = generic_value + shift
                value = rec["thresholds"][name]
                if name.endswith("high"):
                    assert value <= limit + TOL, (combo, field, name)
                else:
                    assert value >= limit - TOL, (combo, field, name)


def test_generic_profile_ignores_the_crew_members_own_data():
    for env in environments.ENVIRONMENTS:
        thresholds = [
            personalization.flat_thresholds(
                _effective(crew, "generic", env, environments.DEFAULT_ENVIRONMENT, 40)
            )
            for crew in CREW
        ]
        assert all(t == thresholds[0] for t in thresholds), env


def test_personal_with_short_history_equals_generic_limits():
    days = get_vitals("C001")[
        : personalization.MIN_BASELINE_DAYS - 1
    ]  # one day short of a baseline
    personal = personalization.effective_thresholds(days, THRESHOLDS, "personal", "iss")
    generic = personalization.effective_thresholds(days, THRESHOLDS, "generic", "iss")
    assert personalization.flat_thresholds(personal) == personalization.flat_thresholds(
        generic
    )
    assert {r["source"] for r in personal["indicators"].values()} == {
        "generic_fallback"
    }


def _deviation(assessed, field):
    return next(i for i in assessed["indicators"] if i["indicator"] == field)[
        "deviation_sigma"
    ]


def test_personal_deviation_is_signed_and_generic_has_none():
    days = get_vitals("C002")
    day = dict(days[-1])
    personal = personalization.effective_thresholds(days, THRESHOLDS, "personal")
    for field, rec in personal["indicators"].items():
        center = rec["expected_value"]
        sigma = rec["sigma"]
        above = personalization.assess_day({**day, field: center + 2 * sigma}, personal)
        below = personalization.assess_day({**day, field: center - 2 * sigma}, personal)
        assert _deviation(above, field) == pytest.approx(2.0, abs=0.02), field
        assert _deviation(below, field) == pytest.approx(-2.0, abs=0.02), field

    generic = personalization.effective_thresholds(days, THRESHOLDS, "generic")
    assessed = personalization.assess_day(day, generic)
    assert all(i["deviation_sigma"] is None for i in assessed["indicators"])


def test_assessment_status_is_the_worst_indicator_in_every_environment():
    day = dict(get_vitals("C003")[-1])
    for env in environments.ENVIRONMENTS:
        eff = personalization.effective_thresholds(
            get_vitals("C003"), THRESHOLDS, "personal", env, days_in_environment=40
        )
        assessed = personalization.assess_day(day, eff)
        worst = max(
            (i["status"] for i in assessed["indicators"]),
            key=personalization.STATUS_RANK.__getitem__,
        )
        assert assessed["status"] == worst, env


@pytest.mark.parametrize("value", [150.1, 160, 220])
def test_heart_rate_above_the_absolute_limit_is_critical_for_everyone(value):
    """Even a person whose baseline is 120 bpm is critical above 150 bpm."""
    days = [
        {**d, "resting_heart_rate_bpm": 118 + (i * 5) % 9}
        for i, d in enumerate(get_vitals("C001"))
    ]
    for env in environments.ENVIRONMENTS:
        if env == "launch":
            continue  # launch overrides the absolute limit on purpose
        eff = personalization.effective_thresholds(
            days, THRESHOLDS, "personal", env, env
        )
        assessed = personalization.assess_day(
            {**days[-1], "resting_heart_rate_bpm": value}, eff
        )
        hr = next(
            i
            for i in assessed["indicators"]
            if i["indicator"] == "resting_heart_rate_bpm"
        )
        assert hr["status"] == "critical", env


# ---- forecast ---------------------------------------------------------


@pytest.mark.parametrize("horizon", [1, 3, 7, 14])
@pytest.mark.parametrize("slope", [-3, -0.5, 0, 0.2, 1, 5])
@pytest.mark.parametrize("direction", ["high", "low"])
def test_days_to_breach_is_within_the_horizon_and_matches_the_risk(
    slope, direction, horizon
):
    values = [50 + slope * i for i in range(14)]
    result = forecast.forecast_indicator(values, 60, direction, horizon)
    d = result["days_to_breach"]
    assert d is None or 0 <= d <= horizon
    if d is None:
        assert result["risk"] == "low"
    elif d <= forecast.HIGH_RISK_WITHIN_DAYS:
        assert result["risk"] == "high"
    else:
        assert result["risk"] == "moderate"
    # a breach is reported exactly when the fitted line crosses the limit
    # somewhere between now and the horizon
    crossed = any(
        (result["current_fit"] + result["slope_per_day"] * s > 60)
        if direction == "high"
        else (result["current_fit"] + result["slope_per_day"] * s < 60)
        for s in range(horizon + 1)
    )
    assert (d is not None) == crossed or abs(slope) < 0.01


def test_forecast_for_every_crew_is_labelled_and_bounded():
    for crew in CREW:
        for profile in personalization.PROFILES:
            for env in ("earth_ground", "iss", "launch", "mars_transit"):
                result = forecast.crew_forecast(
                    crew, 7, profile, env, "earth_ground", 40
                )
                assert result["data_source"] == "synthetic", (crew, profile, env)
                assert (
                    "not a diagnosis" in result["disclaimer"].lower()
                    or result["disclaimer"]
                )
                assert result["window_days"] <= forecast.DEFAULT_WINDOW_DAYS
                assert result["horizon_days"] == 7
                assert len(result["indicators"]) == len(forecast.INDICATORS)
                for item in result["indicators"]:
                    assert all(
                        math.isfinite(item[k])
                        for k in ("current_fit", "projected", "slope_per_day")
                    )
                    assert (
                        item["days_to_breach"] is None
                        or 0 <= item["days_to_breach"] <= 7
                    )
                # most risky first
                ranks = [forecast.RISK_RANK[i["risk"]] for i in result["indicators"]]
                assert ranks == sorted(ranks)


# ---- guarantees that only bite on unusual data -------------------------
# The real crew data never gets close to the absolute limits, so these use
# crafted histories that would break the limits if the safeguards were lost.


def _crafted(**per_field):
    """30 real vitals days with some fields replaced by cyclic values."""
    days = []
    for i, day in enumerate(get_vitals("C001")[:30]):
        day = dict(day)
        for field, cycle in per_field.items():
            day[field] = cycle[i % len(cycle)]
        days.append(day)
    return days


def test_very_variable_baseline_cannot_push_limits_past_the_absolute_ones():
    # Heart rate cycling 115..155 gives a wide spread: 3.5 sigma above the
    # ~135 median is ~187 bpm, far above the 150 bpm hard limit. Likewise SpO2
    # cycling 90..98 puts 3.5 sigma below its median at ~84 %.
    days = _crafted(
        resting_heart_rate_bpm=[115, 125, 135, 145, 155],
        spo2_percent=[90.0, 92.0, 94.0, 96.0, 98.0],
    )
    eff = personalization.effective_thresholds(days, THRESHOLDS, "personal")
    hr = eff["indicators"]["resting_heart_rate_bpm"]
    assert hr["source"] == "personal"
    assert hr["thresholds"]["critical_high"] == 150
    assert hr["thresholds"]["warning_high"] <= 150  # warning stays inside critical
    spo2 = eff["indicators"]["spo2_percent"]
    assert spo2["thresholds"]["critical_low"] == 90  # never below 90 % SpO2
    assert spo2["thresholds"]["warning_low"] >= 90


@pytest.mark.parametrize("field", sorted(personalization.MIN_SIGMA))
def test_a_perfectly_flat_baseline_still_has_a_minimum_spread(field):
    """Without the floor a constant history gives sigma 0 and every tiny
    fluctuation would be an alarm."""
    days = _crafted(**{field: [5]})
    eff = personalization.effective_thresholds(days, THRESHOLDS, "personal")
    assert eff["indicators"][field]["sigma"] == pytest.approx(
        personalization.MIN_SIGMA[field], abs=0.001
    )


@pytest.mark.parametrize(("horizon", "expected"), [(5, None), (6, 6), (7, 6), (14, 6)])
def test_breach_exactly_one_day_beyond_the_horizon_is_not_reported(horizon, expected):
    # Rising 1 per day to 55 against a limit of 60: first value above the
    # limit is 61, on day 6. A threshold equal to the value is not a breach.
    values = [42 + i for i in range(14)]
    result = forecast.forecast_indicator(values, 60, "high", horizon)
    assert result["days_to_breach"] == expected


def test_a_value_equal_to_the_limit_is_not_a_breach():
    values = [59, 59, 59, 59, 59]
    assert forecast.forecast_indicator(values, 59, "high", 7)["days_to_breach"] is None
    assert forecast.forecast_indicator(values, 59, "low", 7)["days_to_breach"] is None


# ---- launch raises the upper heart-rate limits only ---------------------
# Regression: the +30 bpm launch allowance used to move the lower limits too,
# so a calm resting heart rate of 73 bpm was "critical" during launch.

HR_FIELD = "resting_heart_rate_bpm"


@pytest.mark.parametrize("profile", sorted(personalization.PROFILES))
@pytest.mark.parametrize("crew", CREW)
def test_launch_only_raises_the_upper_heart_rate_limits(crew, profile):
    earth = _effective(crew, profile, "earth_ground", "earth_ground", None)
    launch = _effective(crew, profile, "launch", "earth_ground", None)
    e = earth["indicators"][HR_FIELD]
    la = launch["indicators"][HR_FIELD]
    for name, value in la["thresholds"].items():
        if name.endswith("low"):
            assert value == e["thresholds"][name], (crew, profile, name)  # unchanged
        else:
            assert value >= e["thresholds"][name], (
                crew,
                profile,
                name,
            )  # never tighter
    assert la["environment_shift"] == 0  # the expected value does not move
    assert la["environment_tolerance_high"] == 30
    assert la.get("expected_value") == e.get("expected_value")


def test_other_environments_have_no_tolerance_and_other_indicators_none():
    for key, env in environments.ENVIRONMENTS.items():
        for field in personalization.INDICATOR_KEYS:
            expected = 30 if (key, field) == ("launch", HR_FIELD) else 0
            assert environments.tolerance_for(env, field) == expected, (key, field)


@pytest.mark.parametrize("profile", sorted(personalization.PROFILES))
def test_a_calm_heart_rate_is_not_critical_during_launch(profile):
    day = {**get_vitals("C001")[-1], HR_FIELD: 73}
    eff = _effective("C001", profile, "launch", "earth_ground", None)
    hr = next(
        i
        for i in personalization.assess_day(day, eff)["indicators"]
        if i["indicator"] == HR_FIELD
    )
    assert hr["status"] == "nominal"
    assert hr["deviation_sigma"] is None or abs(hr["deviation_sigma"]) < 1


def test_launch_still_flags_a_dangerously_high_heart_rate():
    day = {**get_vitals("C001")[-1], HR_FIELD: 165}
    eff = _effective("C001", "personal", "launch", "earth_ground", None)
    hr = next(
        i
        for i in personalization.assess_day(day, eff)["indicators"]
        if i["indicator"] == HR_FIELD
    )
    assert hr["status"] == "critical"  # above the 160 bpm launch ceiling


def test_environments_with_tolerances_name_known_indicators_and_cite_sources():
    for key, env in environments.ENVIRONMENTS.items():
        tolerances = env.get("tolerances", {})
        assert set(tolerances) <= set(personalization.INDICATOR_KEYS), key
        for field, sides in tolerances.items():
            assert set(sides) <= {"high"}, (
                key,
                field,
            )  # only upper limits are supported
            assert sides["high"] > 0, (key, field)
        if tolerances:
            assert env["sources"], key  # an allowance needs evidence
