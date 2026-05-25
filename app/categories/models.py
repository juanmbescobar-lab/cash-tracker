"""SQLAlchemy ORM model for the Category entity.

A Category groups expenses (and optionally incomes) for reporting
purposes. Names are unique. Categories cannot be deleted while any
transaction references them (enforced via ``ondelete=RESTRICT`` on the
foreign key in Transaction).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.transactions.models import Transaction


class Category(Base):
    """User-defined category for organizing transactions."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

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

    transactions: Mapped[list[Transaction]] = relationship(
        back_populates="category",
        lazy="raise",
    )

    def __repr__(self) -> str:
        return f"Category(id={self.id!r}, name={self.name!r})"
