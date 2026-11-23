"""Alert routes."""

from fastapi import APIRouter

from ...schemas.responses import AlertsResponse
from ...services import alerts as alerts_service
from ..deps import ThresholdContext

router = APIRouter(tags=["alerts"])


@router.get("/alerts", response_model=AlertsResponse)
def get_alerts(ctx: ThresholdContext):
    """All active alerts, combined from three sources: clinical lab values
    out of reference range, vitals alert days, and the current radiation
    environment.

    Vitals are judged by fixed thresholds unless `profile=personal` and/or
    an `environment` is given (earth_ground, atmosphere, launch, iss,
    mars_transit, mars_surface)."""
    return alerts_service.build_alerts(**ctx)
