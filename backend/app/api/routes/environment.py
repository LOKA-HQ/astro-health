"""Environment routes: space weather, radiation, thresholds, omics.

Space weather and radiation are live snapshots, refreshed from NASA DONKI
and NOAA SWPC on demand via POST /environment/refresh.
"""

from fastapi import APIRouter

from ...data import loader
from ...services import environment as env_service

router = APIRouter(tags=["environment"])


@router.get("/space-weather")
def get_space_weather():
    """DONKI space-weather events (last 30 days) and the radiation alert
    mapping used by the app."""
    return loader.SPACE_WEATHER


@router.get("/radiation")
def get_radiation():
    """Radiation environment: hourly GOES proton flux, NOAA S-scale
    thresholds, and published reference dose rates."""
    return loader.RADIATION


@router.get("/thresholds")
def get_thresholds():
    """Alert thresholds for vitals and lab panels."""
    return loader.THRESHOLDS


@router.get("/omics")
def get_omics():
    """OSD-571 proteomics/metabolomics summary: significant post-flight
    changes (R+1 vs pre-flight baseline)."""
    return loader.OMICS


@router.post("/environment/refresh")
def refresh_environment():
    """Re-fetch live space weather (DONKI) and radiation (GOES) data and
    update the stored snapshots. Each source is attempted independently;
    a failure in one does not block the other."""
    return env_service.refresh_all()
