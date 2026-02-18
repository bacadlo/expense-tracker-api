from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.analytics import (
    BalanceResponse,
    BudgetStatusResponse,
    MonthlySummaryResponse,
    SpendingByCategoryResponse,
    TrendResponse,
)
from app.services import analytics_service

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    start_date: date | None = None,
    end_date: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await analytics_service.get_balance(db, start_date=start_date, end_date=end_date)


@router.get("/spending-by-category", response_model=SpendingByCategoryResponse)
async def get_spending_by_category(
    start_date: date | None = None,
    end_date: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await analytics_service.get_spending_by_category(
        db, start_date=start_date, end_date=end_date
    )


@router.get("/monthly-summary", response_model=MonthlySummaryResponse)
async def get_monthly_summary(
    year: int = Query(default_factory=lambda: date.today().year),
    db: AsyncSession = Depends(get_db),
):
    return await analytics_service.get_monthly_summary(db, year=year)


@router.get("/budget-status", response_model=BudgetStatusResponse)
async def get_budget_status(db: AsyncSession = Depends(get_db)):
    return await analytics_service.get_budget_status(db)


@router.get("/trends", response_model=TrendResponse)
async def get_trends(
    period: str = Query(default="monthly", pattern="^(monthly|weekly)$"),
    db: AsyncSession = Depends(get_db),
):
    return await analytics_service.get_trends(db, period=period)
