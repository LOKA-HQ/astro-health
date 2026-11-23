"""Application entrypoint.

Builds the FastAPI app, registers routers, and exposes the root and
health endpoints.

Run:
    uvicorn app.main:app --reload --port 8000
    # or
    python run.py
"""

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import alerts, context, crew, environment
from .config import API_V1_PREFIX, API_VERSION
from .data import loader
from .schemas.responses import HealthResponse

logger = logging.getLogger(__name__)


def _configure_logging():
    """App loggers write INFO+ to stderr. Uvicorn's default logging setup
    leaves the root logger at WARNING, which would swallow app INFO
    messages (startup line, refresh results)."""
    app_logger = logging.getLogger("app")
    if not app_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        app_logger.addHandler(handler)
    app_logger.setLevel(logging.INFO)


def create_app() -> FastAPI:
    _configure_logging()
    app = FastAPI(
        title="Astronaut Health Monitoring API",
        version=API_VERSION,
        description=(
            "Health-monitoring back-end for the NASA 6 of October team "
            "(Space Apps 2026, CH-05)."
        ),
    )

    # Restrict browser access to explicitly configured frontend origins.
    # Local Vite defaults are included for development; production should set
    # ASTRO_CORS_ORIGINS to the deployed frontend origin(s).
    cors_origins = [
        origin.strip()
        for origin in os.environ.get(
            "ASTRO_CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    app.include_router(crew.router, prefix=API_V1_PREFIX)
    app.include_router(alerts.router, prefix=API_V1_PREFIX)
    app.include_router(environment.router, prefix=API_V1_PREFIX)
    app.include_router(context.router, prefix=API_V1_PREFIX)

    logger.info(
        "astronaut-health-api v%s ready: %d crew, %d lab records",
        API_VERSION,
        len(loader.CREW),
        len(loader.RECORDS),
    )

    @app.get("/", tags=["meta"])
    def root():
        """Service health check and crew list."""
        return {
            "service": "astronaut-health-api",
            "version": API_VERSION,
            "crew": loader.CREW,
        }

    @app.get("/health", tags=["meta"], response_model=HealthResponse)
    def health():
        """Service health with dataset status and snapshot freshness."""
        return {
            "status": "ok",
            "crew": len(loader.CREW),
            "lab_records": len(loader.RECORDS),
            "flagged_total": len(loader.flagged(loader.RECORDS)),
            "space_weather_fetched_at": loader.SPACE_WEATHER.get("fetched_at"),
            "radiation_fetched_at": loader.RADIATION.get("fetched_at"),
        }

    return app


app = create_app()
