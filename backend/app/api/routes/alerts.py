"""Alert routes."""

from fastapi import APIRouter

from ...schemas.responses import AlertsResponse
from ...services import alerts as alerts_service

router = APIRouter(tags=["alerts"])


@router.get("/alerts", response_model=AlertsResponse)
def get_alerts():
    """All active alerts, combined from three sources: clinical lab values
    out of reference range, vitals alert days, and the current radiation
    environment."""
    return alerts_service.build_alerts()
