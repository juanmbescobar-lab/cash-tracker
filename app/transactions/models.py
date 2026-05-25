"""SQLAlchemy ORM model for the Transaction entity.

A Transaction represents a single cash income or expense event. The
``type`` column distinguishes income from expense. Amounts are stored
as ``Decimal(12, 2)`` and constrained to be strictly positive — the
sign of a transaction is implied by ``type``, not by the amount value.

Transactions optionally reference a Category. For expenses, a category
is required at the application layer (Phase 1.C). For incomes, the
category is genuinely optional.
"""

from __future__ import annotations

from datetime import date as date_type
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.transactions.enums import TransactionType

if TYPE_CHECKING:
    from app.categories.models import Category


class Transaction(Base):
    """A single cash transaction (income or expense)."""

    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
        Index("ix_transactions_date_category_id", "date", "category_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, name="transaction_type", validate_strings=True),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)

    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    category: Mapped[Category | None] = relationship(
        back_populates="transactions",
        lazy="raise",
    )

    def __repr__(self) -> str:
        return (
            f"Transaction(id={self.id!r}, type={self.type!r}, "
            f"amount={self.amount!r}, date={self.date!r})"
        )
