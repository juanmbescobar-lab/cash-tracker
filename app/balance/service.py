"""Service layer for balance computations.

All figures are computed from the transactions table using SQL
aggregate queries (see ADR-0005). Monetary sums use Decimal to avoid
floating-point error.
"""

from __future__ import annotations

import calendar
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.balance.schemas import (
    BalanceHistory,
    CategoryBreakdown,
    MonthBalance,
    MonthRef,
    MonthSummary,
)
from app.categories.models import Category
from app.categories.schemas import CategoryRead
from app.core.exceptions import BusinessRuleError
from app.transactions.enums import TransactionType
from app.transactions.models import Transaction

_ZERO = Decimal("0.00")
_MAX_HISTORY_MONTHS = 120


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    """Return (first_day, last_day) for the given year and month."""
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    return first_day, last_day


def _sum_by_type(db: Session, txn_type: TransactionType, start: date, end: date) -> Decimal:
    """Return the total amount of a transaction type within [start, end]."""
    result = db.execute(
        select(func.coalesce(func.sum(Transaction.amount), _ZERO)).where(
            Transaction.type == txn_type,
            Transaction.date >= start,
            Transaction.date <= end,
        )
    ).scalar_one()
    return Decimal(result).quantize(Decimal("0.01"))


def compute_running_balance_until(db: Session, year: int, month: int) -> Decimal:
    """Return the running balance at the end of the given month.

    Running balance = sum(income) - sum(expense) for all transactions
    dated on or before the last day of the given month.
    """
    _, last_day = _month_bounds(year, month)
    income = db.execute(
        select(func.coalesce(func.sum(Transaction.amount), _ZERO)).where(
            Transaction.type == TransactionType.INCOME,
            Transaction.date <= last_day,
        )
    ).scalar_one()
    expense = db.execute(
        select(func.coalesce(func.sum(Transaction.amount), _ZERO)).where(
            Transaction.type == TransactionType.EXPENSE,
            Transaction.date <= last_day,
        )
    ).scalar_one()
    return (Decimal(income) - Decimal(expense)).quantize(Decimal("0.01"))


def compute_by_category(db: Session, year: int, month: int) -> list[CategoryBreakdown]:
    """Return expense totals grouped by category for the given month."""
    start, end = _month_bounds(year, month)
    rows = db.execute(
        select(
            Transaction.category_id,
            func.coalesce(func.sum(Transaction.amount), _ZERO).label("total"),
        )
        .where(
            Transaction.type == TransactionType.EXPENSE,
            Transaction.date >= start,
            Transaction.date <= end,
        )
        .group_by(Transaction.category_id)
        .order_by(func.sum(Transaction.amount).desc())
    ).all()

    # Resolve category objects in a single query.
    category_ids = [r.category_id for r in rows if r.category_id is not None]
    categories: dict[int, Category] = {}
    if category_ids:
        found = db.execute(select(Category).where(Category.id.in_(category_ids))).scalars()
        categories = {c.id: c for c in found}

    breakdown: list[CategoryBreakdown] = []
    for row in rows:
        category_read = (
            CategoryRead.model_validate(categories[row.category_id])
            if row.category_id is not None and row.category_id in categories
            else None
        )
        breakdown.append(
            CategoryBreakdown(
                category=category_read,
                total=Decimal(row.total).quantize(Decimal("0.01")),
            )
        )
    return breakdown


def compute_month_balance(db: Session, year: int, month: int) -> MonthBalance:
    """Compute the full balance detail for a single month."""
    start, end = _month_bounds(year, month)
    income_total = _sum_by_type(db, TransactionType.INCOME, start, end)
    expense_total = _sum_by_type(db, TransactionType.EXPENSE, start, end)
    net = (income_total - expense_total).quantize(Decimal("0.01"))

    running_until_this_month = compute_running_balance_until(db, year, month)
    previous_balance = (running_until_this_month - net).quantize(Decimal("0.01"))

    return MonthBalance(
        year=year,
        month=month,
        income_total=income_total,
        expense_total=expense_total,
        net=net,
        previous_balance=previous_balance,
        running_balance=running_until_this_month,
        by_category=compute_by_category(db, year, month),
    )


def _iter_months(
    from_year: int, from_month: int, to_year: int, to_month: int
) -> list[tuple[int, int]]:
    """Return a list of (year, month) tuples from start to end inclusive."""
    months: list[tuple[int, int]] = []
    year, month = from_year, from_month
    while (year, month) <= (to_year, to_month):
        months.append((year, month))
        if month == 12:
            year, month = year + 1, 1
        else:
            month += 1
    return months


def compute_history(
    db: Session,
    from_year: int,
    from_month: int,
    to_year: int,
    to_month: int,
) -> BalanceHistory:
    """Compute month-over-month balance summaries within a range.

    Raises BusinessRuleError if the range is inverted or too large.
    """
    if (from_year, from_month) > (to_year, to_month):
        raise BusinessRuleError("The 'from' month must not be after the 'to' month")

    months = _iter_months(from_year, from_month, to_year, to_month)
    if len(months) > _MAX_HISTORY_MONTHS:
        raise BusinessRuleError(
            f"Requested range exceeds the maximum of {_MAX_HISTORY_MONTHS} months"
        )

    summaries: list[MonthSummary] = []
    for year, month in months:
        start, end = _month_bounds(year, month)
        income_total = _sum_by_type(db, TransactionType.INCOME, start, end)
        expense_total = _sum_by_type(db, TransactionType.EXPENSE, start, end)
        net = (income_total - expense_total).quantize(Decimal("0.01"))
        running_balance = compute_running_balance_until(db, year, month)
        summaries.append(
            MonthSummary(
                year=year,
                month=month,
                income_total=income_total,
                expense_total=expense_total,
                net=net,
                running_balance=running_balance,
            )
        )

    # Most recent first.
    summaries.reverse()

    return BalanceHistory(
        items=summaries,
        **{"from": MonthRef(year=from_year, month=from_month)},
        to=MonthRef(year=to_year, month=to_month),
    )
