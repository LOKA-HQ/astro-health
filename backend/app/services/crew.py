"""Crew business logic: roster, summaries, lab queries, reports.

These functions operate on the loaded datasets and return plain dicts.
They contain no HTTP concerns; routes in api/routes/crew.py expose them.
"""

from ..config import ATTENTION_CLINICAL_OOR, REPORT_WINDOW_DAYS
from ..data import loader
from ..data.vitals import get_vitals

CLINICAL_OUT_OF_RANGE = ("high", "low")


def _clinical_oor(records):
    return sum(1 for r in records if r["status"] in CLINICAL_OUT_OF_RANGE)


def _avg(days, key):
    """Mean of one vitals field over a list of days, rounded to 1 dp."""
    return round(sum(d[key] for d in days) / len(days), 1)


def list_crew():
    """Crew roster with lab-record and flag counts per member."""
    out = []
    for c in loader.CREW:
        recs = loader.records_for_crew(c)
        out.append(
            {
                "crew_id": c,
                "lab_records": len(recs),
                "flagged": len(loader.flagged(recs)),
                "clinical_out_of_range": _clinical_oor(recs),
                "timepoints": loader.TIMEPOINTS,
            }
        )
    return {"crew": out}


def crew_summary(crew_id: str):
    """Per-crew summary: lab flag counts, top flagged indicators, and
    vitals aggregates (latest day, averages, alert days)."""
    recs = loader.records_for_crew(crew_id)
    flagged = loader.flagged(recs)
    vitals = get_vitals(crew_id)
    return {
        "crew_id": crew_id,
        "lab_records": len(recs),
        "flagged_total": len(flagged),
        "clinical_out_of_range": _clinical_oor(flagged),
        "top_flagged_indicators": loader.top_flagged(flagged),
        "vitals": {
            "source": "SYNTHETIC demo data",
            "days": len(vitals),
            "latest": vitals[-1],
            "alert_days": sum(1 for d in vitals if d["status"] != "nominal"),
            "avg_resting_hr": _avg(vitals, "resting_heart_rate_bpm"),
            "avg_sleep_hours": _avg(vitals, "sleep_hours"),
            "avg_body_temperature_c": _avg(vitals, "body_temperature_c"),
            "avg_mood_score": _avg(vitals, "mood_score"),
        },
    }


def crew_labs(
    crew_id: str,
    panel: str | None = None,
    timepoint: str | None = None,
    status: str | None = None,
    flagged_only: bool = False,
    limit: int = 100,
    offset: int = 0,
):
    """Lab records for one crew member, filtered and paginated."""
    recs = loader.records_for_crew(crew_id)
    if panel:
        recs = [r for r in recs if r["panel"] == panel]
    if timepoint:
        recs = [r for r in recs if r["timepoint"] == timepoint]
    if status:
        recs = [r for r in recs if r["status"] == status]
    if flagged_only:
        recs = loader.flagged(recs)
    return {
        "crew_id": crew_id,
        "total": len(recs),
        "limit": limit,
        "offset": offset,
        "records": recs[offset : offset + limit],
    }


def crew_vitals(crew_id: str, days: int = 30):
    """Vitals time series for one crew member (synthetic demo data).
    Returns the last `days` days (1-30)."""
    return {
        "crew_id": crew_id,
        "source": "SYNTHETIC demo data - no public astronaut wearable stream exists",
        "days": get_vitals(crew_id)[-days:],
    }


def crew_report(crew_id: str):
    """Weekly-style summary report for one crew member: 7-day vitals
    aggregates, lab flag totals, and an overall status."""
    summary = crew_summary(crew_id)
    vitals = get_vitals(crew_id)
    week = vitals[-REPORT_WINDOW_DAYS:]
    return {
        "crew_id": crew_id,
        "period": f"{week[0]['date']} to {week[-1]['date']}",
        "vitals_7d": {
            "avg_resting_hr": _avg(week, "resting_heart_rate_bpm"),
            "avg_sleep_hours": _avg(week, "sleep_hours"),
            "avg_stress": _avg(week, "stress_score"),
            "avg_body_temperature_c": _avg(week, "body_temperature_c"),
            "avg_mood_score": _avg(week, "mood_score"),
            "min_spo2": min(d["spo2_percent"] for d in week),
            "alert_days": sum(1 for d in week if d["status"] != "nominal"),
        },
        "labs": {
            "flagged_total": summary["flagged_total"],
            "clinical_out_of_range": summary["clinical_out_of_range"],
            "top_flagged_indicators": summary["top_flagged_indicators"],
        },
        "overall_status": (
            "attention"
            if summary["clinical_out_of_range"] > ATTENTION_CLINICAL_OOR
            or any(d["status"] != "nominal" for d in week)
            else "nominal"
        ),
    }
