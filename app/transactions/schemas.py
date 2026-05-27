"""Pydantic schemas for the transactions domain.

Includes cross-field validation: expense transactions require a
``category_id`` (income transactions may omit it). The nested
``CategoryRead`` in ``TransactionRead`` allows clients to receive
the full category in a single request.
"""

from __future__ import annotations

from datetime import date as date_type
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.categories.schemas import CategoryRead
from app.transactions.enums import TransactionType


class TransactionBase(BaseModel):
    """Fields shared across Create, Update, and Read schemas."""

    type: TransactionType
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    description: str = Field(min_length=1, max_length=500)
    date: date_type
    category_id: int | None = None


class TransactionCreate(TransactionBase):
    """Schema for creating a new transaction (POST body)."""

    @model_validator(mode="after")
    def expense_requires_category(self) -> TransactionCreate:
        if self.type == TransactionType.EXPENSE and self.category_id is None:
            raise ValueError("Expense transactions require a category")
        return self


class TransactionUpdate(BaseModel):
    """Schema for partial update (PATCH body). All fields optional."""

    type: TransactionType | None = None
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    description: str | None = Field(default=None, min_length=1, max_length=500)
    date: date_type | None = None
    category_id: int | None = None


class TransactionRead(BaseModel):
    """Schema returned in responses, with category eagerly loaded."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    type: TransactionType
    amount: Decimal
    description: str
    date: date_type
    category: CategoryRead | None
    created_at: datetime
    updated_at: datetime


class PaginatedTransactionRead(BaseModel):
    """Paginated response for GET /transactions."""

    items: list[TransactionRead]
    total: int
    skip: int
    limit: int
