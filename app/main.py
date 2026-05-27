"""FastAPI application entry point.

Wires the FastAPI app, mounts feature routers, and registers global
exception handlers that translate domain errors into HTTP responses.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.categories.router import router as categories_router
from app.core.config import get_settings
from app.core.exceptions import (
    BusinessRuleError,
    ConflictError,
    NotFoundError,
)
from app.transactions.router import router as transactions_router

settings = get_settings()

app = FastAPI(
    title="Cash Tracker",
    description=("Mobile-first PWA for tracking cash transactions. API backend (Phase 1)."),
    version="0.1.0",
    debug=settings.debug,
)


# Exception handlers translate domain exceptions to HTTP responses.
# See ADR-0004 for rationale.


@app.exception_handler(NotFoundError)
async def _handle_not_found(_: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


@app.exception_handler(ConflictError)
async def _handle_conflict(_: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


@app.exception_handler(BusinessRuleError)
async def _handle_business_rule(_: Request, exc: BusinessRuleError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)},
    )


# Mount feature routers.
app.include_router(categories_router)
app.include_router(transactions_router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    """Return a 200 OK with basic service information."""
    return {"status": "ok", "env": settings.app_env}
