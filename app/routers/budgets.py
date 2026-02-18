from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.budget import BudgetCreate, BudgetDetailResponse, BudgetResponse, BudgetUpdate
from app.services import budget_service

router = APIRouter(prefix="/api/budgets", tags=["budgets"])


@router.post("/", response_model=BudgetResponse, status_code=201)
async def create_budget(data: BudgetCreate, db: AsyncSession = Depends(get_db)):
    return await budget_service.create_budget(db, data)


@router.get("/", response_model=list[BudgetResponse])
async def list_budgets(db: AsyncSession = Depends(get_db)):
    return await budget_service.list_budgets(db)


@router.get("/{budget_id}", response_model=BudgetDetailResponse)
async def get_budget(budget_id: int, db: AsyncSession = Depends(get_db)):
    return await budget_service.get_budget_detail(db, budget_id)


@router.put("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: int, data: BudgetUpdate, db: AsyncSession = Depends(get_db)
):
    return await budget_service.update_budget(db, budget_id, data)


@router.delete("/{budget_id}", status_code=204)
async def delete_budget(budget_id: int, db: AsyncSession = Depends(get_db)):
    await budget_service.delete_budget(db, budget_id)
