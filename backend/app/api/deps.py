"""Shared route dependencies."""

from typing import Annotated

from fastapi import Depends, HTTPException, Query

from ..data.loader import CREW
from ..services.environments import DEFAULT_ENVIRONMENT, ENVIRONMENTS
from ..services.personalization import DEFAULT_PROFILE, PROFILES


def require_crew(crew_id: str) -> str:
    """Validate a crew id from the path, or raise 404."""
    if crew_id not in CREW:
        raise HTTPException(404, f"unknown crew id {crew_id}")
    return crew_id


def threshold_context(
    profile: str = DEFAULT_PROFILE,
    environment: str = DEFAULT_ENVIRONMENT,
    baseline_environment: str = DEFAULT_ENVIRONMENT,
    days_in_environment: Annotated[int | None, Query(ge=0, le=3650)] = None,
) -> dict:
    """Validate the ?profile=, ?environment=, ?baseline_environment= and
    ?days_in_environment= query parameters shared by every threshold-aware
    endpoint, or raise 422.

    profile              generic (fixed thresholds) or personal (learned
                         from the crew member's own history)
    environment          where the crew member is now
    baseline_environment where the personal baseline was recorded
                         (default: Earth, a pre-flight baseline)
    days_in_environment  days spent in `environment` so far; shifts that
                         develop gradually (core temperature in
                         microgravity) grow with it and are not applied
                         when it is omitted
    """
    if profile not in PROFILES:
        raise HTTPException(
            422, f"unknown profile {profile!r}; choose one of: {', '.join(PROFILES)}"
        )
    for name, value in (
        ("environment", environment),
        ("baseline_environment", baseline_environment),
    ):
        if value not in ENVIRONMENTS:
            raise HTTPException(
                422,
                f"unknown {name} {value!r}; choose one of: {', '.join(ENVIRONMENTS)}",
            )
    return {
        "profile": profile,
        "environment": environment,
        "baseline_environment": baseline_environment,
        "days_in_environment": days_in_environment,
    }


ThresholdContext = Annotated[dict, Depends(threshold_context)]
