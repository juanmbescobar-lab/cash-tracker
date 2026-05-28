"""Unit tests for balance service computations."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.balance.service import (
    compute_history,
    compute_month_balance,
    compute_running_balance_until,
)
from app.categories.models import Category
from app.core.exceptions import BusinessRuleError
from app.transactions.enums import TransactionType
from app.transactions.models import Transaction


def _add_txn(
    db: Session,
    txn_type: TransactionType,
    amount: str,
    txn_date: date,
    category_id: int | None = None,
) -> None:
    db.add(
        Transaction(
            type=txn_type,
            amount=Decimal(amount),
            description="test",
            date=txn_date,
            category_id=category_id,
        )
    )
    db.commit()


def test_empty_month_returns_zero(db_session: Session) -> None:
    balance = compute_month_balance(db_session, 2026, 5)
    assert balance.income_total == Decimal("0.00")
    assert balance.expense_total == Decimal("0.00")
    assert balance.net == Decimal("0.00")
    assert balance.previous_balance == Decimal("0.00")
    assert balance.running_balance == Decimal("0.00")
    assert balance.by_category == []


def test_month_with_only_income(db_session: Session) -> None:
    _add_txn(db_session, TransactionType.INCOME, "1000.00", date(2026, 5, 10))
    _add_txn(db_session, TransactionType.INCOME, "500.00", date(2026, 5, 20))
    balance = compute_month_balance(db_session, 2026, 5)
    assert balance.income_total == Decimal("1500.00")
    assert balance.expense_total == Decimal("0.00")
    assert balance.net == Decimal("1500.00")
    assert balance.running_balance == Decimal("1500.00")


def test_month_with_only_expense(db_session: Session) -> None:
    cat = Category(name="Food")
    db_session.add(cat)
    db_session.commit()
    _add_txn(db_session, TransactionType.EXPENSE, "200.00", date(2026, 5, 10), cat.id)
    balance = compute_month_balance(db_session, 2026, 5)
    assert balance.expense_total == Decimal("200.00")
    assert balance.net == Decimal("-200.00")
    assert balance.running_balance == Decimal("-200.00")


def test_month_with_income_and_expense(db_session: Session) -> None:
    cat = Category(name="Food")
    db_session.add(cat)
    db_session.commit()
    _add_txn(db_session, TransactionType.INCOME, "1000.00", date(2026, 5, 5))
    _add_txn(db_session, TransactionType.EXPENSE, "300.00", date(2026, 5, 15), cat.id)
    balance = compute_month_balance(db_session, 2026, 5)
    assert balance.income_total == Decimal("1000.00")
    assert balance.expense_total == Decimal("300.00")
    assert balance.net == Decimal("700.00")


def test_previous_balance_carries_over(db_session: Session) -> None:
    # April: net +500
    _add_txn(db_session, TransactionType.INCOME, "500.00", date(2026, 4, 10))
    # May: net +200
    _add_txn(db_session, TransactionType.INCOME, "200.00", date(2026, 5, 10))

    may_balance = compute_month_balance(db_session, 2026, 5)
    assert may_balance.net == Decimal("200.00")
    assert may_balance.previous_balance == Decimal("500.00")
    assert may_balance.running_balance == Decimal("700.00")


def test_running_balance_until(db_session: Session) -> None:
    _add_txn(db_session, TransactionType.INCOME, "1000.00", date(2026, 3, 1))
    _add_txn(db_session, TransactionType.EXPENSE, "400.00", date(2026, 4, 1))
    _add_txn(db_session, TransactionType.INCOME, "200.00", date(2026, 5, 1))

    assert compute_running_balance_until(db_session, 2026, 3) == Decimal("1000.00")
    assert compute_running_balance_until(db_session, 2026, 4) == Decimal("600.00")
    assert compute_running_balance_until(db_session, 2026, 5) == Decimal("800.00")


def test_by_category_breakdown(db_session: Session) -> None:
    food = Category(name="Food")
    transport = Category(name="Transport")
    db_session.add_all([food, transport])
    db_session.commit()

    _add_txn(db_session, TransactionType.EXPENSE, "100.00", date(2026, 5, 1), food.id)
    _add_txn(db_session, TransactionType.EXPENSE, "50.00", date(2026, 5, 2), food.id)
    _add_txn(
        db_session,
        TransactionType.EXPENSE,
        "30.00",
        date(2026, 5, 3),
        transport.id,
    )

    balance = compute_month_balance(db_session, 2026, 5)
    breakdown = {(b.category.name if b.category else None): b.total for b in balance.by_category}
    assert breakdown["Food"] == Decimal("150.00")
    assert breakdown["Transport"] == Decimal("30.00")


def test_decimal_precision_preserved(db_session: Session) -> None:
    _add_txn(db_session, TransactionType.INCOME, "1234567.89", date(2026, 5, 1))
    balance = compute_month_balance(db_session, 2026, 5)
    assert balance.income_total == Decimal("1234567.89")


def test_history_inverted_range_raises(db_session: Session) -> None:
    with pytest.raises(BusinessRuleError, match="must not be after"):
        compute_history(db_session, 2026, 6, 2026, 5)


def test_history_excessive_range_raises(db_session: Session) -> None:
    with pytest.raises(BusinessRuleError, match="exceeds the maximum"):
        compute_history(db_session, 2000, 1, 2026, 5)


def test_history_orders_recent_first(db_session: Session) -> None:
    _add_txn(db_session, TransactionType.INCOME, "100.00", date(2026, 4, 1))
    _add_txn(db_session, TransactionType.INCOME, "200.00", date(2026, 5, 1))

    history = compute_history(db_session, 2026, 4, 2026, 5)
    assert len(history.items) == 2
    assert history.items[0].month == 5
    assert history.items[1].month == 4
    # Running balance accumulates
    assert history.items[0].running_balance == Decimal("300.00")
    assert history.items[1].running_balance == Decimal("100.00")
