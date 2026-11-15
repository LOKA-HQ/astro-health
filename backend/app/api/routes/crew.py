"""Crew routes: roster, summaries, labs, vitals, reports, alerts."""

from fastapi import APIRouter, Depends, Query

from ...schemas.responses import (
    AlertsResponse,
    CrewListResponse,
    CrewReport,
    CrewSummary,
    LabsResponse,
    VitalsResponse,
)
from ...services import alerts as alerts_service
from ...services import crew as crew_service
from ..deps import require_crew

router = APIRouter(prefix="/crew", tags=["crew"])


@router.get("", response_model=CrewListResponse)
def list_crew():
    """Crew roster with lab-record and flag counts per member."""
    return crew_service.list_crew()


@router.get("/{crew_id}/summary", response_model=CrewSummary)
def get_crew_summary(crew_id: str = Depends(require_crew)):
    """Per-crew summary: lab flag counts, top flagged indicators, and
    vitals aggregates."""
    return crew_service.crew_summary(crew_id)


@router.get("/{crew_id}/labs", response_model=LabsResponse)
def get_crew_labs(
    crew_id: str = Depends(require_crew),
    panel: str | None = None,
    timepoint: str | None = None,
    status: str | None = None,
    flagged_only: bool = False,
    limit: int = Query(100, ge=0, le=1000),
    offset: int = Query(0, ge=0),
):
    """Lab records for one crew member. Filter by panel, timepoint, or
    status; flagged_only restricts to out-of-range / baseline deviations.
    Results are paginated with limit/offset (max limit 1000)."""
    return crew_service.crew_labs(
        crew_id,
        panel=panel,
        timepoint=timepoint,
        status=status,
        flagged_only=flagged_only,
        limit=limit,
        offset=offset,
    )


@router.get("/{crew_id}/vitals", response_model=VitalsResponse)
def get_crew_vitals(
    crew_id: str = Depends(require_crew),
    days: int = Query(30, ge=1, le=30),
):
    """Vitals time series for one crew member (synthetic demo data).
    Returns the last `days` days (1-30, default 30)."""
    return crew_service.crew_vitals(crew_id, days=days)


@router.get("/{crew_id}/alerts", response_model=AlertsResponse)
def get_crew_alerts(crew_id: str = Depends(require_crew)):
    """Alerts for one crew member (lab + vitals, most severe first).
    The radiation alert is global; see GET /api/v1/alerts."""
    return alerts_service.alerts_for_crew(crew_id)


@router.get("/{crew_id}/report", response_model=CrewReport)
def get_crew_report(crew_id: str = Depends(require_crew)):
    """Weekly-style summary report for one crew member."""
    return crew_service.crew_report(crew_id)
