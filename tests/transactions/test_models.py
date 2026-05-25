"""Tests for the Transaction model and its relationship to Category."""

from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.orm import Session, selectinload

from app.categories.models import Category
from app.transactions.enums import TransactionType
from app.transactions.models import Transaction


def test_create_income_without_category(db_session: Session) -> None:
    """An income transaction may be created without a category."""
    txn = Transaction(
        type=TransactionType.INCOME,
        amount=Decimal("500.00"),
        description="Salary",
        date=date(2026, 5, 23),
    )
    db_session.add(txn)
    db_session.commit()
    db_session.refresh(txn)

    assert txn.id is not None
    assert txn.type == TransactionType.INCOME
    assert txn.amount == Decimal("500.00")
    assert txn.category_id is None
    assert isinstance(txn.created_at, datetime)


def test_create_expense_with_category(db_session: Session) -> None:
    """An expense transaction may reference a Category via FK."""
    category = Category(name="Food")
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    txn = Transaction(
        type=TransactionType.EXPENSE,
        amount=Decimal("25.50"),
        description="Coffee",
        date=date(2026, 5, 23),
        category_id=category.id,
    )
    db_session.add(txn)
    db_session.commit()
    db_session.refresh(txn)

    assert txn.id is not None
    assert txn.type == TransactionType.EXPENSE
    assert txn.category_id == category.id


def test_transaction_amount_must_be_positive(db_session: Session) -> None:
    """The CHECK constraint rejects non-positive amounts."""
    txn = Transaction(
        type=TransactionType.EXPENSE,
        amount=Decimal("-10.00"),
        description="Invalid",
        date=date(2026, 5, 23),
    )
    db_session.add(txn)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    txn_zero = Transaction(
        type=TransactionType.EXPENSE,
        amount=Decimal("0.00"),
        description="Invalid",
        date=date(2026, 5, 23),
    )
    db_session.add(txn_zero)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_transaction_required_fields(db_session: Session) -> None:
    """All non-nullable fields must be provided."""
    # Missing type
    db_session.add(
        Transaction(  # type: ignore[call-arg]
            amount=Decimal("10.00"),
            description="x",
            date=date(2026, 5, 23),
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Missing amount
    db_session.add(
        Transaction(  # type: ignore[call-arg]
            type=TransactionType.EXPENSE,
            description="x",
            date=date(2026, 5, 23),
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Missing description
    db_session.add(
        Transaction(  # type: ignore[call-arg]
            type=TransactionType.EXPENSE,
            amount=Decimal("10.00"),
            date=date(2026, 5, 23),
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Missing date
    db_session.add(
        Transaction(  # type: ignore[call-arg]
            type=TransactionType.EXPENSE,
            amount=Decimal("10.00"),
            description="x",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_cannot_delete_category_with_transactions(db_session: Session) -> None:
    """RESTRICT prevents deleting a Category referenced by a Transaction."""
    category = Category(name="Food")
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    txn = Transaction(
        type=TransactionType.EXPENSE,
        amount=Decimal("10.00"),
        description="Snack",
        date=date(2026, 5, 23),
        category_id=category.id,
    )
    db_session.add(txn)
    db_session.commit()

    db_session.delete(category)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_delete_category_without_transactions(db_session: Session) -> None:
    """A Category with no transactions can be deleted."""
    category = Category(name="Unused")
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    category_id = category.id

    db_session.delete(category)
    db_session.commit()

    result = db_session.execute(
        select(Category).where(Category.id == category_id)
    ).scalar_one_or_none()
    assert result is None


def test_lazy_raise_prevents_implicit_load(db_session: Session) -> None:
    """Accessing ``transaction.category`` without eager loading raises."""
    category = Category(name="Food")
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    txn = Transaction(
        type=TransactionType.EXPENSE,
        amount=Decimal("10.00"),
        description="Snack",
        date=date(2026, 5, 23),
        category_id=category.id,
    )
    db_session.add(txn)
    db_session.commit()
    db_session.refresh(txn)
    db_session.expire(txn, ["category"])

    with pytest.raises(InvalidRequestError):
        _ = txn.category


def test_selectinload_loads_category(db_session: Session) -> None:
    """Explicit ``selectinload`` makes ``transaction.category`` accessible."""
    category = Category(name="Food")
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    db_session.add(
        Transaction(
            type=TransactionType.EXPENSE,
            amount=Decimal("10.00"),
            description="Snack",
            date=date(2026, 5, 23),
            category_id=category.id,
        )
    )
    db_session.commit()

    txn = db_session.execute(
        select(Transaction).options(selectinload(Transaction.category))
    ).scalar_one()

    assert txn.category is not None
    assert txn.category.name == "Food"


def test_category_back_populates_transactions(db_session: Session) -> None:
    """Loading a Category with ``selectinload`` exposes its transactions."""
    category = Category(name="Food")
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    db_session.add_all(
        [
            Transaction(
                type=TransactionType.EXPENSE,
                amount=Decimal("10.00"),
                description="Snack",
                date=date(2026, 5, 23),
                category_id=category.id,
            ),
            Transaction(
                type=TransactionType.EXPENSE,
                amount=Decimal("25.50"),
                description="Lunch",
                date=date(2026, 5, 23),
                category_id=category.id,
            ),
        ]
    )
    db_session.commit()

    loaded = db_session.execute(
        select(Category)
        .options(selectinload(Category.transactions))
        .where(Category.id == category.id)
    ).scalar_one()

    assert len(loaded.transactions) == 2
    descriptions = sorted(t.description for t in loaded.transactions)
    assert descriptions == ["Lunch", "Snack"]


def test_transaction_type_enum_values(db_session: Session) -> None:
    """Only INCOME and EXPENSE are valid; other values fail."""
    db_session.add(
        Transaction(
            type=TransactionType.INCOME,
            amount=Decimal("100.00"),
            description="Valid income",
            date=date(2026, 5, 23),
        )
    )
    db_session.add(
        Transaction(
            type=TransactionType.EXPENSE,
            amount=Decimal("50.00"),
            description="Valid expense",
            date=date(2026, 5, 23),
        )
    )
    db_session.commit()

    # Invalid string value (bypassing the enum)
    db_session.add(
        Transaction(
            type="transfer",  # type: ignore[arg-type]
            amount=Decimal("10.00"),
            description="Invalid",
            date=date(2026, 5, 23),
        )
    )
    with pytest.raises((IntegrityError, LookupError, ValueError, Exception)):
        db_session.commit()
    db_session.rollback()


def test_transaction_amount_precision(db_session: Session) -> None:
    """Amounts preserve two-decimal precision through DB round-trip."""
    txn = Transaction(
        type=TransactionType.EXPENSE,
        amount=Decimal("1234567.89"),
        description="Large expense",
        date=date(2026, 5, 23),
    )
    db_session.add(txn)
    db_session.commit()
    db_session.refresh(txn)

    assert txn.amount == Decimal("1234567.89")
