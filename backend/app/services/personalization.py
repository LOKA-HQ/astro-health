"""Personalised, environment-aware vitals thresholds.

Fixed thresholds treat everybody the same: a resting heart rate of 100 bpm
is a warning for most people but ordinary for someone whose baseline is
110. This module learns each crew member's own normal and builds
thresholds around it, then adjusts them for where the crew member is
(see services/environments.py).

How a threshold is built, per indicator:

1. Baseline. The median of the crew member's own history, and a robust
   spread: 1.4826 x the median absolute deviation (MAD). The constant is
   1 / 0.6745, the scaling of the modified Z-score of Iglewicz and Hoaglin
   (NIST/SEMATECH e-Handbook of Statistical Methods, section 1.3.5.17), so
   the spread behaves like a standard deviation but is not thrown off by the
   odd bad day. The most recent days are held out of the baseline so a
   developing problem is not absorbed into "normal".
2. Personal limits. warning = baseline +/- K_WARNING x spread, critical =
   baseline +/- K_CRITICAL x spread, on the same sides the generic
   thresholds use. K_WARNING = 2.5 is the cut-off Leys et al. (2013)
   recommend for MAD-based outlier detection, and K_CRITICAL = 3.5 is the
   cut-off Iglewicz and Hoaglin recommend for flagging potential outliers.
   The spread never goes below a per-indicator floor, so a very steady
   person does not get a hair-trigger. Personal limits may only tighten the
   generic ones, unless the baseline itself lies outside the generic normal
   range (then they may relax them).
3. Environment. The expected value moves by the environment's shift (see
   services/environments.py for the evidence) and the spread is scaled by
   its spread factor, relative to the environment the baseline was learned
   in.
4. Absolute safety limits. Whatever the baseline says, values beyond these
   limits are always critical, so personalisation can never "normalise" a
   dangerous reading. A baseline that itself sits outside the generic
   normal range is reported so a clinician can review it.

The statistical constants and the absolute limits are sourced (docs/SOURCES.md).
Per-indicator spread floors are engineering choices. Nothing here has been
clinically validated.
"""

from statistics import median

from ..data import loader
from ..data.vitals import get_vitals
from . import environments

DEFAULT_PROFILE = "generic"
PROFILES = ("generic", "personal")

K_WARNING = 2.5  # Leys et al. 2013, MAD-based outlier cut-off
K_CRITICAL = 3.5  # Iglewicz & Hoaglin; NIST e-Handbook 1.3.5.17
MAD_TO_SIGMA = 1.4826  # 1 / 0.6745, NIST e-Handbook 1.3.5.17

# Most recent days kept out of the baseline, and the minimum history needed
# before a personal baseline is trusted (otherwise fall back to generic).
EVAL_WINDOW_DAYS = 7
MIN_BASELINE_DAYS = 7

SIDES = ("warning_high", "critical_high", "warning_low", "critical_low")

STATUS_RANK = {"nominal": 0, "warning": 1, "critical": 2}

# vitals field -> key in data/health_thresholds.json
INDICATOR_KEYS = {
    "resting_heart_rate_bpm": "resting_heart_rate_bpm",
    "sleep_hours": "sleep_hours",
    "sleep_quality": "sleep_quality_percent",
    "spo2_percent": "spo2_percent",
    "stress_score": "stress_score",
    "blood_pressure_systolic_mmhg": "blood_pressure_systolic_mmhg",
    "blood_pressure_diastolic_mmhg": "blood_pressure_diastolic_mmhg",
    "body_temperature_c": "body_temperature_c",
    "mood_score": "mood_score_1_10",
}

# Indicators whose personal limits may never be looser than the generic ones,
# even when the person's own baseline is outside the normal range. A chronic
# 6 h sleeper, or a crew member whose mood is always low, has a deficiency to
# be flagged, not a personal normal to be learned (ISS crews average about
# 6 h of sleep against 8.5 h scheduled, Barger 2014). Heart rate, blood
# pressure, temperature and SpO2 can legitimately differ between people, so
# those may relax when the baseline is outside the normal range.
TIGHTEN_ONLY = frozenset({"sleep_hours", "sleep_quality", "stress_score", "mood_score"})

# Smallest spread allowed per indicator (same units as the indicator).
# Engineering choices (not from a source): roughly the day-to-day noise
# below which a limit would trigger on ordinary variation.
MIN_SIGMA = {
    "resting_heart_rate_bpm": 3.0,
    "sleep_hours": 0.5,
    "sleep_quality": 5.0,
    "spo2_percent": 0.5,
    "stress_score": 5.0,
    "blood_pressure_systolic_mmhg": 5.0,
    "blood_pressure_diastolic_mmhg": 3.0,
    "body_temperature_c": 0.3,
    "mood_score": 0.75,
}

# Beyond these a reading is always critical, whatever the personal baseline
# (a value is critical when it is above "high" or below "low").
#
# Sourced:
# - heart rate high 150: the AHA ACLS tachyarrhythmia algorithm describes
#   the rate as typically 150/min or more.
# - SpO2 low 90: healthy adults at the 8,000 ft cabin limit stay at or above
#   90% (PaO2 above 60 mmHg), so below 90% is hypoxaemia (National Research
#   Council, Airliner Cabin Environment, 2002).
# - blood pressure high 180 / 120: the AHA hypertensive-crisis threshold
#   (above 180 systolic and/or above 120 diastolic).
# - temperature high 40.0: Mayo Clinic heat-stroke core temperature, 40 C
#   or higher; low 35.0: Mayo Clinic hypothermia, below 35 C.
# Engineering choices (no guideline cited): heart rate low 40 (chosen below
# the generic critical of 50 so trained crew with a slow resting rate are
# not alarmed), blood pressure low 80 / 50.
ABSOLUTE_LIMITS = {
    "resting_heart_rate_bpm": {"high": 150, "low": 40},
    "spo2_percent": {"low": 90},
    "blood_pressure_systolic_mmhg": {"high": 180, "low": 80},
    "blood_pressure_diastolic_mmhg": {"high": 120, "low": 50},
    "body_temperature_c": {"high": 40.0, "low": 35.0},
}


def compute_baseline(values):
    """(median, robust spread) of a list of numbers."""
    center = median(values)
    mad = median(abs(v - center) for v in values)
    return center, MAD_TO_SIGMA * mad


def baseline_history(days, eval_window=EVAL_WINDOW_DAYS):
    """Days used to learn the baseline: everything before the evaluation
    window when that leaves enough history, otherwise all days."""
    if len(days) - eval_window >= MIN_BASELINE_DAYS:
        return days[:-eval_window]
    return days


def _absolute_limits(field, env):
    limits = dict(ABSOLUTE_LIMITS.get(field, {}))
    limits.update(env["absolute_overrides"].get(field, {}))
    return limits


def _clamp(thresholds, limits):
    """Apply the absolute safety limits and keep warning inside critical."""
    out = dict(thresholds)
    if "critical_high" in out and "high" in limits:
        out["critical_high"] = min(out["critical_high"], limits["high"])
    if "critical_low" in out and "low" in limits:
        out["critical_low"] = max(out["critical_low"], limits["low"])
    if "warning_high" in out and "critical_high" in out:
        out["warning_high"] = min(out["warning_high"], out["critical_high"])
    if "warning_low" in out and "critical_low" in out:
        out["warning_low"] = max(out["warning_low"], out["critical_low"])
    return out


def effective_thresholds(
    days,
    generic,
    profile=DEFAULT_PROFILE,
    environment=environments.DEFAULT_ENVIRONMENT,
    baseline_environment=environments.DEFAULT_ENVIRONMENT,
    days_in_environment=None,
):
    """Thresholds to judge `days` by, for one crew member.

    days                   vitals day dicts, oldest first (the baseline source)
    generic                generic thresholds (data/health_thresholds.json)
    profile                "generic" (same for everyone) or "personal"
    environment            where the crew member is now
    baseline_environment   where the baseline history was recorded (default:
                           Earth, i.e. a pre-flight baseline). Pass the same
                           value as `environment` once the baseline has been
                           re-learned in place and no shift is needed.
    days_in_environment    days spent in `environment` so far. Shifts that
                           develop gradually (core temperature in
                           microgravity) are scaled by it; when it is None
                           they are not applied at all.
    """
    if profile not in PROFILES:
        raise ValueError(f"unknown profile {profile!r}")
    env = environments.get_environment(environment)
    base_env = environments.get_environment(baseline_environment)
    history = baseline_history(days)
    use_personal = profile == "personal" and len(history) >= MIN_BASELINE_DAYS

    indicators = {}
    for field, key in INDICATOR_KEYS.items():
        generic_th = {n: v for n, v in generic[key].items() if n in SIDES}
        record = {"threshold_key": key, "generic": generic_th}

        if use_personal:
            base_shift = environments.full_shift_for(base_env, field)
            if baseline_environment == environment:
                shift = 0.0  # baseline learned in place: already adapted
            else:
                shift = (
                    environments.shift_for(env, field, days_in_environment) - base_shift
                )
            values = [d[field] for d in history]
            center, sigma_raw = compute_baseline(values)
            sigma = max(sigma_raw, MIN_SIGMA[field])
            sigma *= env["spread_factor"] / base_env["spread_factor"]
            expected = center + shift
            th = {}
            for name in generic_th:
                k = K_CRITICAL if name.startswith("critical") else K_WARNING
                sign = 1 if name.endswith("high") else -1
                th[name] = expected + sign * k * sigma
            record.update(
                source="personal",
                baseline_median=round(center, 2),
                baseline_days=len(values),
                expected_value=round(expected, 2),
                sigma=round(sigma, 3),
            )
            # The generic normal range as it applies where the baseline was
            # recorded. A baseline inside it may only tighten the generic
            # limits; one outside it (a hypertensive crew member, say) may
            # also relax them.
            normal = generic[key].get("normal")
            outside = bool(normal) and not (
                normal[0] + base_shift <= center <= normal[1] + base_shift
            )
            record["baseline_outside_generic_normal"] = outside
            may_relax = outside and field not in TIGHTEN_ONLY
            if outside:
                record["baseline_note"] = (
                    f"Personal baseline {round(center, 1)} is outside the "
                    f"generic normal range {normal[0] + base_shift:g}-"
                    f"{normal[1] + base_shift:g}; clinical review recommended."
                )
                if not may_relax:
                    record["baseline_note"] += (
                        " Limits for this indicator are never relaxed "
                        "below the generic ones."
                    )
            if not may_relax:
                generic_shift = environments.shift_for(env, field, days_in_environment)
                generic_here = {n: v + generic_shift for n, v in generic_th.items()}
                for name, limit in generic_here.items():
                    if name.endswith("high"):
                        th[name] = min(th[name], limit)
                    else:
                        th[name] = max(th[name], limit)
        else:
            shift = environments.shift_for(env, field, days_in_environment)
            th = {n: v + shift for n, v in generic_th.items()}
            record["source"] = "generic" if profile == "generic" else "generic_fallback"

        record["environment_shift"] = round(shift, 2)
        th = _clamp(th, _absolute_limits(field, env))
        record["thresholds"] = {n: round(v, 2) for n, v in th.items()}
        indicators[field] = record

    return {
        "profile": profile,
        "environment": environment,
        "baseline_environment": baseline_environment,
        "days_in_environment": days_in_environment,
        "baseline_days": len(history) if use_personal else 0,
        "indicators": indicators,
    }


def flat_thresholds(effective):
    """Effective thresholds in the same shape as health_thresholds.json
    (threshold key -> {warning_high, ...}), for code that expects that."""
    return {
        r["threshold_key"]: r["thresholds"] for r in effective["indicators"].values()
    }


def assess_day(day, effective):
    """Judge one vitals day against effective thresholds.

    Returns {"date", "mission_day", "status", "indicators": [...]} where
    status is the worst of the indicator statuses.
    """
    records = []
    worst = "nominal"
    for field, rec in effective["indicators"].items():
        value = day[field]
        th = rec["thresholds"]
        status, side, limit = "nominal", None, None
        for level in ("critical", "warning"):
            high, low = th.get(f"{level}_high"), th.get(f"{level}_low")
            if high is not None and value > high:
                status, side, limit = level, "high", high
                break
            if low is not None and value < low:
                status, side, limit = level, "low", low
                break

        sigma = rec.get("sigma")
        deviation = None
        if rec["source"] == "personal" and sigma:
            deviation = round((value - rec["expected_value"]) / sigma, 2)

        label = field.replace("_", " ")
        if status == "nominal":
            message = f"{label} {value} within limits"
        else:
            where = "above" if side == "high" else "below"
            message = f"{label} {value} {where} {rec['source']} {status} limit {limit}"

        records.append(
            {
                "indicator": field,
                "value": value,
                "status": status,
                "side": side,
                "limit": limit,
                "deviation_sigma": deviation,
                "message": message,
            }
        )
        if STATUS_RANK[status] > STATUS_RANK[worst]:
            worst = status

    return {
        "date": day["date"],
        "mission_day": day["mission_day"],
        "status": worst,
        "indicators": records,
    }


def crew_thresholds(
    crew_id,
    profile=DEFAULT_PROFILE,
    environment=environments.DEFAULT_ENVIRONMENT,
    baseline_environment=environments.DEFAULT_ENVIRONMENT,
    days_in_environment=None,
):
    """Effective thresholds for one crew member."""
    eff = effective_thresholds(
        get_vitals(crew_id),
        loader.THRESHOLDS,
        profile,
        environment,
        baseline_environment,
        days_in_environment,
    )
    return {"crew_id": crew_id, **eff}


def crew_assessment(
    crew_id,
    profile=DEFAULT_PROFILE,
    environment=environments.DEFAULT_ENVIRONMENT,
    baseline_environment=environments.DEFAULT_ENVIRONMENT,
    days_in_environment=None,
    days=7,
):
    """Status of the last `days` vitals days for one crew member, judged
    by the effective thresholds."""
    all_days = get_vitals(crew_id)
    eff = effective_thresholds(
        all_days,
        loader.THRESHOLDS,
        profile,
        environment,
        baseline_environment,
        days_in_environment,
    )
    assessed = [assess_day(d, eff) for d in all_days[-days:]]
    return {
        "crew_id": crew_id,
        "profile": profile,
        "environment": environment,
        "baseline_environment": baseline_environment,
        "days_in_environment": days_in_environment,
        "data_source": "synthetic",
        "latest_status": assessed[-1]["status"],
        "days": assessed,
    }
