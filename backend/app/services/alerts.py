"""Alert aggregation.

Combines three alert sources into one list, sorted most severe first:
- Clinical lab values out of reference range (high/low).
- Vitals alert days (elevated HR, short sleep, high stress).
- Current radiation environment (NOAA GOES proton flux, informational).
"""

from ..data import loader
from ..data.vitals import get_vitals

# Severity order for sorting: most severe first. Stable sort keeps the
# original within-group order.
SEVERITY_RANK = {"critical": 0, "warning": 1, "info": 2}


def build_alerts():
    out = []
    # Clinical high/low labs.
    for r in loader.RECORDS:
        if r["status"] in ("high", "low"):
            out.append(
                {
                    "level": "critical" if r["status"] == "high" else "warning",
                    "type": "lab",
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
        for d in get_vitals(c):
            if d["status"] != "nominal":
                out.append(
                    {
                        "level": "warning",
                        "type": "vitals",
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
            "source": "NOAA GOES-18 >=10 MeV proton flux",
            "latest_flux_pfu": rad["latest_flux_pfu"],
            "status": rad["latest_status"],
            "message": f"Radiation environment {rad['latest_status']} "
            f"({rad['latest_flux_pfu']} pfu)",
        }
    )
    out.sort(key=lambda a: SEVERITY_RANK[a["level"]])
    return {"alerts": out, "count": len(out)}


def alerts_for_crew(crew_id: str):
    """Alerts for one crew member (lab + vitals). The radiation alert is
    global and is not included here; see build_alerts()."""
    all_alerts = build_alerts()["alerts"]
    crew_alerts = [a for a in all_alerts if a.get("crew_id") == crew_id]
    return {"alerts": crew_alerts, "count": len(crew_alerts)}
