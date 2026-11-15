"""Shared route dependencies."""

from fastapi import HTTPException

from ..data.loader import CREW


def require_crew(crew_id: str) -> str:
    """Validate a crew id from the path, or raise 404."""
    if crew_id not in CREW:
        raise HTTPException(404, f"unknown crew id {crew_id}")
    return crew_id
