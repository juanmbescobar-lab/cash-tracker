"""Reusable FastAPI dependencies."""

from __future__ import annotations

from fastapi import Query
from pydantic import BaseModel


class PaginationParams(BaseModel):
    """Standard pagination query parameters.

    Used as a FastAPI dependency. Parses and validates ``skip`` and
    ``limit`` from the query string.

    Example: ``GET /transactions?skip=0&limit=50``
    """

    skip: int = 0
    limit: int = 50


def pagination_params(
    skip: int = Query(default=0, ge=0, description="Number of items to skip"),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Maximum items to return (1-200)",
    ),
) -> PaginationParams:
    """Return validated pagination parameters."""
    return PaginationParams(skip=skip, limit=limit)
