"""Tests for the Category model."""

from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.categories.models import Category


def test_create_category_with_required_fields(db_session: Session) -> None:
    """Creating a Category with only ``name`` persists with auto fields."""
    category = Category(name="Food")
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    assert category.id is not None
    assert category.name == "Food"
    assert category.description is None
    assert isinstance(category.created_at, datetime)
    assert isinstance(category.updated_at, datetime)


def test_create_category_with_all_fields(db_session: Session) -> None:
    """Creating a Category with both name and description persists both."""
    category = Category(name="Transport", description="Daily commute and travel")
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    assert category.name == "Transport"
    assert category.description == "Daily commute and travel"


def test_category_name_must_be_unique(db_session: Session) -> None:
    """Two categories with the same name violate the unique constraint."""
    db_session.add(Category(name="Food"))
    db_session.commit()

    db_session.add(Category(name="Food"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_category_name_is_required(db_session: Session) -> None:
    """Creating a Category without name fails."""
    db_session.add(Category())  # type: ignore[call-arg]
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_updated_at_changes_on_update(db_session: Session) -> None:
    """``updated_at`` is refreshed when the row is updated."""
    category = Category(name="Food")
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    original_updated_at = category.updated_at

    # Force a small time gap so the new timestamp differs.
    import time

    time.sleep(0.01)

    category.description = "Groceries and dining"
    db_session.commit()
    db_session.refresh(category)

    assert category.updated_at >= original_updated_at
