from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundException
from app.models.budget import Budget
from app.models.transaction import Transaction, TransactionType
from app.schemas.budget import BudgetCreate, BudgetDetailResponse, BudgetUpdate


async def create_budget(db: AsyncSession, data: BudgetCreate) -> Budget:
    budget = Budget(**data.model_dump())
    db.add(budget)
    await db.flush()
    await db.refresh(budget)
    return budget


async def get_budget(db: AsyncSession, budget_id: int) -> Budget:
    budget = await db.get(Budget, budget_id)
    if not budget:
        raise NotFoundException("Budget", budget_id)
    return budget


async def get_budget_detail(db: AsyncSession, budget_id: int) -> BudgetDetailResponse:
    budget = await get_budget(db, budget_id)
    spent = await _compute_spent(db, budget)
    remaining = budget.amount - spent
    percentage_used = float(spent / budget.amount * 100) if budget.amount > 0 else 0.0

    return BudgetDetailResponse(
        **{c.name: getattr(budget, c.name) for c in budget.__table__.columns},
        spent=spent,
        remaining=remaining,
        percentage_used=round(percentage_used, 2),
    )


async def list_budgets(db: AsyncSession) -> list[Budget]:
    result = await db.execute(select(Budget).order_by(Budget.start_date.desc()))
    return list(result.scalars().all())


async def update_budget(db: AsyncSession, budget_id: int, data: BudgetUpdate) -> Budget:
    budget = await get_budget(db, budget_id)
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(budget, field, value)

    # Validate dates after update
    if budget.end_date <= budget.start_date:
        raise ValueError("end_date must be after start_date")

    await db.flush()
    await db.refresh(budget)
    return budget


async def delete_budget(db: AsyncSession, budget_id: int) -> None:
    budget = await get_budget(db, budget_id)
    await db.delete(budget)
    await db.flush()


async def _compute_spent(db: AsyncSession, budget: Budget) -> Decimal:
    query = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.type == TransactionType.EXPENSE,
        Transaction.date >= budget.start_date,
        Transaction.date <= budget.end_date,
    )
    if budget.category_id is not None:
        query = query.where(Transaction.category_id == budget.category_id)

    result = await db.execute(query)
    return result.scalar_one()
