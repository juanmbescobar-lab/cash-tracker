"""HTTP API for the transactions domain."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import PaginationParams, pagination_params
from app.transactions import service
from app.transactions.schemas import (
    PaginatedTransactionRead,
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post(
    "",
    response_model=TransactionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new transaction",
)
def create_transaction(data: TransactionCreate, db: Session = Depends(get_db)) -> TransactionRead:
    return TransactionRead.model_validate(service.create_transaction(db, data))


@router.get(
    "",
    response_model=PaginatedTransactionRead,
    summary="List transactions with pagination",
)
def list_transactions(
    pagination: PaginationParams = Depends(pagination_params),
    db: Session = Depends(get_db),
) -> PaginatedTransactionRead:
    items, total = service.list_transactions(db, skip=pagination.skip, limit=pagination.limit)
    return PaginatedTransactionRead(
        items=[TransactionRead.model_validate(t) for t in items],
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionRead,
    summary="Get a transaction by id",
)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)) -> TransactionRead:
    return TransactionRead.model_validate(service.get_transaction(db, transaction_id))


@router.patch(
    "/{transaction_id}",
    response_model=TransactionRead,
    summary="Partially update a transaction",
)
def update_transaction(
    transaction_id: int,
    data: TransactionUpdate,
    db: Session = Depends(get_db),
) -> TransactionRead:
    return TransactionRead.model_validate(service.update_transaction(db, transaction_id, data))


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a transaction",
)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)) -> None:
    service.delete_transaction(db, transaction_id)
