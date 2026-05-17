"""FastAPI application entry point.

Wires the application together: creates the FastAPI instance, mounts
routers (added in later phases), and exposes a health check used by
infrastructure and CI to verify the service is up.
"""

from fastapi import FastAPI

from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Cash Tracker",
    description=("Mobile-first PWA for tracking cash transactions. API backend (Phase 1)."),
    version="0.1.0",
    debug=settings.debug,
)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    """Return a 200 OK with basic service information.

    Used by load balancers, container orchestrators, and CI smoke
    tests to verify the service is alive.
    """
    return {"status": "ok", "env": settings.app_env}
