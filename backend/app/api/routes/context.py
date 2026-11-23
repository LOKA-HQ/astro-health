"""Environment (location) context routes."""

from fastapi import APIRouter, HTTPException, Query

from ...services import environments as environments_service

router = APIRouter(tags=["context"])


@router.get("/environments")
def list_environments():
    """The environments the thresholds adapt to (Earth, atmosphere, launch,
    space station, Mars transit, Mars surface) and how each one shifts the
    expected vital signs. Illustrative demo values, not clinical guidance."""
    return environments_service.list_environments()


@router.get("/environments/detect")
def detect_environment(
    body: str = "earth",
    altitude_km: float = Query(0.0, ge=0),
    accel_g: float = Query(1.0, ge=0),
):
    """Infer the environment from telemetry: the planet (`body`: earth or
    mars), altitude above its surface in km, and sustained acceleration in g.
    Pass the returned `environment` as the `environment` parameter of the
    crew endpoints."""
    try:
        return environments_service.detect_environment(body, altitude_km, accel_g)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
