"""Pydantic schemas for balance computation and history.

Balance figures are derived from transactions and never persisted, so
there are no Create or Update schemas — only read-shaped responses.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from app.categories.schemas import CategoryRead


class CategoryBreakdown(BaseModel):
    """Total expense for a single category within a period.

    ``category`` is null for expenses with no category assigned (which
    should not occur under normal validation, but is handled defensively).
    """

    category: CategoryRead | None
    total: Decimal


class MonthBalance(BaseModel):
    """Full balance detail for a single month."""

    year: int
    month: int
    income_total: Decimal
    expense_total: Decimal
    net: Decimal
    previous_balance: Decimal
    running_balance: Decimal
    by_category: list[CategoryBreakdown]


class MonthSummary(BaseModel):
    """Lightweight monthly figures, used in history listings."""

    year: int
    month: int
    income_total: Decimal
    expense_total: Decimal
    net: Decimal
    running_balance: Decimal


class MonthRef(BaseModel):
    """A year/month reference, used to echo the requested range."""

    year: int
    month: int


class BalanceHistory(BaseModel):
    """Month-over-month balance history within a requested range."""

    items: list[MonthSummary]
    from_: MonthRef = Field(alias="from")
    to: MonthRef

    model_config = {"populate_by_name": True}
