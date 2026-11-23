"""Alert aggregation.

Combines three alert sources into one list, sorted most severe first:
- Clinical lab values out of reference range (high/low).
- Vitals alert days (elevated HR, short sleep, high stress).
- Current radiation environment (NOAA GOES proton flux, informational).
"""

from ..data import loader
from ..data.vitals import get_vitals
from . import environments, personalization

# Severity order for sorting: most severe first. Stable sort keeps the
# original within-group order.
SEVERITY_RANK = {"critical": 0, "warning": 1, "info": 2}

# Provenance labels carried on every alert (see schemas.responses.Alert).
DATA_SOURCE_REAL = "real"  # NASA OSDR Inspiration4 lab data
DATA_SOURCE_REAL_LIVE = "real_live"  # live NOAA / NASA feeds
DATA_SOURCE_SYNTHETIC = "synthetic"  # generated demo vitals


def _vitals_alerts_adaptive(
    crew_id, days, profile, environment, baseline_env, days_in_environment
):
    """Vitals alerts judged by personal and/or environment-adjusted
    thresholds instead of the fixed generic ones."""
    eff = personalization.effective_thresholds(
        days, loader.THRESHOLDS, profile, environment, baseline_env, days_in_environment
    )
    out = []
    for d in days:
        assessed = personalization.assess_day(d, eff)
        if assessed["status"] == "nominal":
            continue
        flagged = [i for i in assessed["indicators"] if i["status"] != "nominal"]
        out.append(
            {
                "level": assessed["status"],
                "type": "vitals",
                "data_source": DATA_SOURCE_SYNTHETIC,
                "crew_id": crew_id,
                "date": d["date"],
                "mission_day": d["mission_day"],
                "alerts": [
                    {
                        "indicator": i["indicator"],
                        "level": i["status"],
                        "message": i["message"],
                    }
                    for i in flagged
                ],
                "message": f"Mission day {d['mission_day']}: "
                + "; ".join(i["message"] for i in flagged),
            }
        )
    return out


def build_alerts(
    profile=personalization.DEFAULT_PROFILE,
    environment=environments.DEFAULT_ENVIRONMENT,
    baseline_environment=environments.DEFAULT_ENVIRONMENT,
    days_in_environment=None,
):
    """All alerts, most severe first.

    With the defaults (generic thresholds, Earth) vitals alerts use the
    original fixed rules. Any other profile or environment judges vitals by
    personal and/or environment-adjusted thresholds (see
    services/personalization.py). Lab and radiation alerts are unchanged.
    """
    adaptive = (
        profile != personalization.DEFAULT_PROFILE
        or environment != environments.DEFAULT_ENVIRONMENT
    )
    out = []
    # Clinical high/low labs.
    for r in loader.RECORDS:
        if r["status"] in ("high", "low"):
            out.append(
                {
                    "level": "critical" if r["status"] == "high" else "warning",
                    "type": "lab",
                    "data_source": DATA_SOURCE_REAL,
                    "crew_id": r["crew"],
                    "timepoint": r["timepoint"],
                    "indicator": r["indicator"],
                    "value": r["value"],
                    "unit": r["unit"],
                    "ref_range": [r["ref_min"], r["ref_max"]],
                    "message": f"{r['indicator']} {r['status']} ({r['value']} {r['unit']}) "
                    f"- ref {r['ref_min']}-{r['ref_max']}",
                }
            )
    # Vitals alert days.
    for c in loader.CREW:
        if adaptive:
            out.extend(
                _vitals_alerts_adaptive(
                    c,
                    get_vitals(c),
                    profile,
                    environment,
                    baseline_environment,
                    days_in_environment,
                )
            )
            continue
        for d in get_vitals(c):
            if d["status"] != "nominal":
                out.append(
                    {
                        "level": "warning",
                        "type": "vitals",
                        "data_source": DATA_SOURCE_SYNTHETIC,
                        "crew_id": c,
                        "date": d["date"],
                        "mission_day": d["mission_day"],
                        "alerts": d["alerts"],
                        "message": f"Mission day {d['mission_day']}: "
                        f"HR {d['resting_heart_rate_bpm']} bpm, "
                        f"sleep {d['sleep_hours']}h, "
                        f"stress {d['stress_score']}",
                    }
                )
    # Radiation environment (live snapshot).
    rad = loader.RADIATION
    out.append(
        {
            "level": "info",
            "type": "radiation",
            "data_source": DATA_SOURCE_REAL_LIVE,
            "source": "NOAA GOES-18 >=10 MeV proton flux",
            "latest_flux_pfu": rad["latest_flux_pfu"],
            "status": rad["latest_status"],
            "message": f"Radiation environment {rad['latest_status']} "
            f"({rad['latest_flux_pfu']} pfu)",
        }
    )
    out.sort(key=lambda a: SEVERITY_RANK[a["level"]])
    return {
        "alerts": out,
        "count": len(out),
        "profile": profile,
        "environment": environment,
    }


def alerts_for_crew(
    crew_id: str,
    profile=personalization.DEFAULT_PROFILE,
    environment=environments.DEFAULT_ENVIRONMENT,
    baseline_environment=environments.DEFAULT_ENVIRONMENT,
    days_in_environment=None,
):
    """Alerts for one crew member (lab + vitals). The radiation alert is
    global and is not included here; see build_alerts()."""
    built = build_alerts(
        profile, environment, baseline_environment, days_in_environment
    )
    crew_alerts = [a for a in built["alerts"] if a.get("crew_id") == crew_id]
    return {
        "alerts": crew_alerts,
        "count": len(crew_alerts),
        "profile": profile,
        "environment": environment,
    }
