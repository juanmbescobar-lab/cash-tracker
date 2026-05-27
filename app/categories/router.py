"""HTTP API for the categories domain."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.categories import service
from app.categories.schemas import (
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    PaginatedCategoryRead,
)
from app.core.database import get_db
from app.core.dependencies import PaginationParams, pagination_params

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category",
)
def create_category(data: CategoryCreate, db: Session = Depends(get_db)) -> CategoryRead:
    return CategoryRead.model_validate(service.create_category(db, data))


@router.get(
    "",
    response_model=PaginatedCategoryRead,
    summary="List categories with pagination",
)
def list_categories(
    pagination: PaginationParams = Depends(pagination_params),
    db: Session = Depends(get_db),
) -> PaginatedCategoryRead:
    items, total = service.list_categories(db, skip=pagination.skip, limit=pagination.limit)
    return PaginatedCategoryRead(
        items=[CategoryRead.model_validate(c) for c in items],
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Get a category by id",
)
def get_category(category_id: int, db: Session = Depends(get_db)) -> CategoryRead:
    return CategoryRead.model_validate(service.get_category(db, category_id))


@router.patch(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Partially update a category",
)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
) -> CategoryRead:
    return CategoryRead.model_validate(service.update_category(db, category_id, data))


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a category",
)
def delete_category(category_id: int, db: Session = Depends(get_db)) -> None:
    service.delete_category(db, category_id)
