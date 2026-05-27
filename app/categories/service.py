"""Service layer for category CRUD operations.

Service functions encapsulate business logic and database access.
They raise domain exceptions (``NotFoundError``, ``ConflictError``)
which are translated to HTTP responses at the API layer.

All functions take ``db: Session`` as the first argument for explicit
dependency injection and ease of testing.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.categories.models import Category
from app.categories.schemas import CategoryCreate, CategoryUpdate
from app.core.exceptions import ConflictError, NotFoundError


def create_category(db: Session, data: CategoryCreate) -> Category:
    """Create a new category. Raises ConflictError if name already exists."""
    category = Category(name=data.name, description=data.description)
    db.add(category)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(f"A category with name '{data.name}' already exists") from exc
    db.refresh(category)
    return category


def get_category(db: Session, category_id: int) -> Category:
    """Return a category by id or raise NotFoundError."""
    category = db.get(Category, category_id)
    if category is None:
        raise NotFoundError("Category", category_id)
    return category


def list_categories(db: Session, skip: int = 0, limit: int = 50) -> tuple[list[Category], int]:
    """Return (categories, total_count) for paginated listing."""
    total = db.execute(select(func.count(Category.id))).scalar_one()
    items = list(
        db.execute(select(Category).order_by(Category.name).offset(skip).limit(limit)).scalars()
    )
    return items, total


def update_category(db: Session, category_id: int, data: CategoryUpdate) -> Category:
    """Update fields provided in ``data``. Other fields remain unchanged."""
    category = get_category(db, category_id)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(category, key, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            f"A category with name '{update_data.get('name')}' already exists"
        ) from exc
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int) -> None:
    """Delete a category. Raises ConflictError if transactions reference it."""
    category = get_category(db, category_id)
    db.delete(category)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            f"Cannot delete category {category_id}: transactions still reference it"
        ) from exc
