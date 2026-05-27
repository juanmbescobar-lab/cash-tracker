"""Pydantic schemas for the categories domain.

Schemas are separated by purpose:
- ``CategoryBase``: shared fields. Internal, not used at endpoints directly.
- ``CategoryCreate``: request body for POST /categories.
- ``CategoryUpdate``: request body for PATCH /categories/{id}. All fields optional.
- ``CategoryRead``: response shape returned by all GET endpoints.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    """Fields shared between Create, Update, and Read schemas."""

    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class CategoryCreate(CategoryBase):
    """Schema for creating a new category (POST body)."""


class CategoryUpdate(BaseModel):
    """Schema for partial update (PATCH body). All fields optional."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class CategoryRead(CategoryBase):
    """Schema returned in responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class PaginatedCategoryRead(BaseModel):
    """Paginated response for GET /categories."""

    items: list[CategoryRead]
    total: int
    skip: int
    limit: int
