"""HTTP API for balance computations."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.balance import service
from app.balance.schemas import BalanceHistory, MonthBalance
from app.core.database import get_db

router = APIRouter(prefix="/balance", tags=["balance"])


@router.get(
    "/current",
    response_model=MonthBalance,
    summary="Balance for the current month",
)
def get_current_balance(db: Session = Depends(get_db)) -> MonthBalance:
    today = date.today()
    return service.compute_month_balance(db, today.year, today.month)


@router.get(
    "/history",
    response_model=BalanceHistory,
    response_model_by_alias=True,
    summary="Month-over-month balance history",
)
def get_balance_history(
    from_year: int | None = Query(default=None, ge=2000, le=2100),
    from_month: int | None = Query(default=None, ge=1, le=12),
    to_year: int | None = Query(default=None, ge=2000, le=2100),
    to_month: int | None = Query(default=None, ge=1, le=12),
    db: Session = Depends(get_db),
) -> BalanceHistory:
    today = date.today()

    # Default 'to' is the current month.
    resolved_to_year = to_year if to_year is not None else today.year
    resolved_to_month = to_month if to_month is not None else today.month

    # Default 'from' is 12 months before 'to' (11 months back, inclusive of 12).
    if from_year is not None and from_month is not None:
        resolved_from_year = from_year
        resolved_from_month = from_month
    else:
        # Compute 11 months before the 'to' month.
        total_index = resolved_to_year * 12 + (resolved_to_month - 1) - 11
        resolved_from_year = total_index // 12
        resolved_from_month = total_index % 12 + 1

    return service.compute_history(
        db,
        resolved_from_year,
        resolved_from_month,
        resolved_to_year,
        resolved_to_month,
    )


@router.get(
    "/month/{year}/{month}",
    response_model=MonthBalance,
    summary="Balance for a specific month",
)
def get_month_balance(
    year: int = Path(ge=2000, le=2100),
    month: int = Path(ge=1, le=12),
    db: Session = Depends(get_db),
) -> MonthBalance:
    return service.compute_month_balance(db, year, month)
