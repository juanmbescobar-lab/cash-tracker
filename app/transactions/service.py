"""Service layer for transaction CRUD operations.

Eagerly loads the related Category in all read paths via
``selectinload``, which aligns with ``lazy="raise"`` on the
``Transaction.category`` relationship.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.categories.models import Category
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.transactions.enums import TransactionType
from app.transactions.models import Transaction
from app.transactions.schemas import TransactionCreate, TransactionUpdate


def _ensure_category_exists(db: Session, category_id: int) -> None:
    """Raise BusinessRuleError if the given category_id does not exist."""
    if db.get(Category, category_id) is None:
        raise BusinessRuleError(f"Category with id {category_id} does not exist")


def create_transaction(db: Session, data: TransactionCreate) -> Transaction:
    """Create a new transaction.

    Validates that the referenced category (if any) exists. The
    Pydantic schema already enforces that expense transactions
    have a category_id; this function additionally validates that
    the referenced category exists in the database.
    """
    if data.category_id is not None:
        _ensure_category_exists(db, data.category_id)

    transaction = Transaction(
        type=data.type,
        amount=data.amount,
        description=data.description,
        date=data.date,
        category_id=data.category_id,
    )
    db.add(transaction)
    db.commit()
    return _get_with_category(db, transaction.id)


def get_transaction(db: Session, transaction_id: int) -> Transaction:
    """Return a transaction with its category eagerly loaded."""
    return _get_with_category(db, transaction_id)


def list_transactions(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    from_date: date | None = None,
    to_date: date | None = None,
    category_id: int | None = None,
    txn_type: TransactionType | None = None,
) -> tuple[list[Transaction], int]:
    """Return (transactions, total_count) with optional filters.

    Filters (all optional, combinable):
    - from_date / to_date: inclusive date range
    - category_id: restrict to a single category
    - txn_type: restrict to income or expense

    Transactions are ordered by date descending, then id descending.
    """
    filters = []
    if from_date is not None:
        filters.append(Transaction.date >= from_date)
    if to_date is not None:
        filters.append(Transaction.date <= to_date)
    if category_id is not None:
        filters.append(Transaction.category_id == category_id)
    if txn_type is not None:
        filters.append(Transaction.type == txn_type)

    total = db.execute(select(func.count(Transaction.id)).where(*filters)).scalar_one()
    items = list(
        db.execute(
            select(Transaction)
            .options(selectinload(Transaction.category))
            .where(*filters)
            .order_by(Transaction.date.desc(), Transaction.id.desc())
            .offset(skip)
            .limit(limit)
        ).scalars()
    )
    return items, total


def update_transaction(db: Session, transaction_id: int, data: TransactionUpdate) -> Transaction:
    """Update fields provided in ``data``. Enforces expense-requires-category.

    Because update is partial, we must validate the combined post-update
    state, not just the incoming fields.
    """
    transaction = _get_with_category(db, transaction_id)
    update_data = data.model_dump(exclude_unset=True)

    # Validate referenced category exists if changing it.
    if "category_id" in update_data and update_data["category_id"] is not None:
        _ensure_category_exists(db, update_data["category_id"])

    # Apply updates to a copy first for validation purposes.
    new_type = update_data.get("type", transaction.type)
    new_category_id = update_data.get("category_id", transaction.category_id)
    if new_type == TransactionType.EXPENSE and new_category_id is None:
        raise BusinessRuleError("Expense transactions require a category")

    for key, value in update_data.items():
        setattr(transaction, key, value)
    db.commit()
    return _get_with_category(db, transaction.id)


def delete_transaction(db: Session, transaction_id: int) -> None:
    """Delete a transaction by id."""
    transaction = get_transaction(db, transaction_id)
    db.delete(transaction)
    db.commit()


def _get_with_category(db: Session, transaction_id: int) -> Transaction:
    """Load a transaction with category eagerly. Raises NotFoundError."""
    transaction = db.execute(
        select(Transaction)
        .options(selectinload(Transaction.category))
        .where(Transaction.id == transaction_id)
    ).scalar_one_or_none()
    if transaction is None:
        raise NotFoundError("Transaction", transaction_id)
    return transaction
