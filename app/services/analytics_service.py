from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import case, extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import Budget
from app.models.category import Category
from app.models.transaction import Transaction, TransactionType
from app.schemas.analytics import (
    BalanceResponse,
    BudgetStatusItem,
    BudgetStatusResponse,
    CategoryBreakdown,
    MonthlySummaryItem,
    MonthlySummaryResponse,
    SpendingByCategoryResponse,
    TrendResponse,
)


async def get_balance(
    db: AsyncSession,
    start_date: date | None = None,
    end_date: date | None = None,
) -> BalanceResponse:
    """Net balance via CASE WHEN — income and expenses in a single query."""
    income_case = case(
        (Transaction.type == TransactionType.INCOME, Transaction.amount),
        else_=0,
    )
    expense_case = case(
        (Transaction.type == TransactionType.EXPENSE, Transaction.amount),
        else_=0,
    )

    query = select(
        func.coalesce(func.sum(income_case), 0).label("total_income"),
        func.coalesce(func.sum(expense_case), 0).label("total_expenses"),
    )

    if start_date:
        query = query.where(Transaction.date >= start_date)
    if end_date:
        query = query.where(Transaction.date <= end_date)

    row = (await db.execute(query)).one()
    total_income = Decimal(str(row.total_income))
    total_expenses = Decimal(str(row.total_expenses))

    return BalanceResponse(
        total_income=total_income,
        total_expenses=total_expenses,
        net_balance=total_income - total_expenses,
    )


async def get_spending_by_category(
    db: AsyncSession,
    start_date: date | None = None,
    end_date: date | None = None,
) -> SpendingByCategoryResponse:
    """Category breakdown with totals and percentage share."""
    query = (
        select(
            Category.id.label("category_id"),
            Category.name.label("category_name"),
            func.coalesce(func.sum(Transaction.amount), 0).label("total"),
        )
        .join(Transaction, Transaction.category_id == Category.id)
        .where(Transaction.type == TransactionType.EXPENSE)
        .group_by(Category.id, Category.name)
        .order_by(func.sum(Transaction.amount).desc())
    )

    if start_date:
        query = query.where(Transaction.date >= start_date)
    if end_date:
        query = query.where(Transaction.date <= end_date)

    rows = (await db.execute(query)).all()
    total_spending = sum(Decimal(str(r.total)) for r in rows)

    items = [
        CategoryBreakdown(
            category_id=r.category_id,
            category_name=r.category_name,
            total=Decimal(str(r.total)),
            percentage=round(float(Decimal(str(r.total)) / total_spending * 100), 2)
            if total_spending > 0
            else 0.0,
        )
        for r in rows
    ]

    return SpendingByCategoryResponse(items=items, total_spending=total_spending)


async def get_monthly_summary(
    db: AsyncSession,
    year: int,
) -> MonthlySummaryResponse:
    """Month-by-month income, expenses, and net using EXTRACT + GROUP BY."""
    month_col = extract("month", Transaction.date).label("month")

    income_case = case(
        (Transaction.type == TransactionType.INCOME, Transaction.amount),
        else_=0,
    )
    expense_case = case(
        (Transaction.type == TransactionType.EXPENSE, Transaction.amount),
        else_=0,
    )

    query = (
        select(
            month_col,
            func.coalesce(func.sum(income_case), 0).label("income"),
            func.coalesce(func.sum(expense_case), 0).label("expenses"),
        )
        .where(extract("year", Transaction.date) == year)
        .group_by(month_col)
        .order_by(month_col)
    )

    rows = (await db.execute(query)).all()
    items = [
        MonthlySummaryItem(
            month=int(r.month),
            year=year,
            income=Decimal(str(r.income)),
            expenses=Decimal(str(r.expenses)),
            net=Decimal(str(r.income)) - Decimal(str(r.expenses)),
        )
        for r in rows
    ]

    return MonthlySummaryResponse(items=items, year=year)


async def get_budget_status(db: AsyncSession) -> BudgetStatusResponse:
    """Active budgets with spent, remaining, and percentage used."""
    today = date.today()
    budgets_query = (
        select(Budget)
        .where(Budget.start_date <= today, Budget.end_date >= today)
        .order_by(Budget.start_date)
    )
    budgets = (await db.execute(budgets_query)).scalars().all()

    items = []
    for budget in budgets:
        # Compute spent for each budget's scope
        spent_query = select(
            func.coalesce(func.sum(Transaction.amount), 0)
        ).where(
            Transaction.type == TransactionType.EXPENSE,
            Transaction.date >= budget.start_date,
            Transaction.date <= budget.end_date,
        )
        if budget.category_id is not None:
            spent_query = spent_query.where(Transaction.category_id == budget.category_id)

        spent = Decimal(str((await db.execute(spent_query)).scalar_one()))
        remaining = budget.amount - spent
        pct = round(float(spent / budget.amount * 100), 2) if budget.amount > 0 else 0.0

        # Fetch category name if scoped
        cat_name = None
        if budget.category_id is not None:
            cat_row = await db.execute(
                select(Category.name).where(Category.id == budget.category_id)
            )
            cat_name = cat_row.scalar_one_or_none()

        items.append(
            BudgetStatusItem(
                budget_id=budget.id,
                budget_name=budget.name,
                budget_amount=budget.amount,
                category_name=cat_name,
                spent=spent,
                remaining=remaining,
                percentage_used=pct,
            )
        )

    return BudgetStatusResponse(items=items)


async def get_trends(
    db: AsyncSession,
    period: str = "monthly",
) -> TrendResponse:
    """Current vs previous period spending comparison."""
    today = date.today()

    if period == "weekly":
        current_start = today - timedelta(days=today.weekday())
        previous_start = current_start - timedelta(weeks=1)
        previous_end = current_start - timedelta(days=1)
    else:  # monthly
        current_start = today.replace(day=1)
        if current_start.month == 1:
            previous_start = current_start.replace(year=current_start.year - 1, month=12)
        else:
            previous_start = current_start.replace(month=current_start.month - 1)
        previous_end = current_start - timedelta(days=1)

    current_end = today

    async def _sum_expenses(start: date, end: date) -> Decimal:
        result = await db.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.type == TransactionType.EXPENSE,
                Transaction.date >= start,
                Transaction.date <= end,
            )
        )
        return Decimal(str(result.scalar_one()))

    current = await _sum_expenses(current_start, current_end)
    previous = await _sum_expenses(previous_start, previous_end)
    change = current - previous
    change_pct = round(float(change / previous * 100), 2) if previous > 0 else None

    return TrendResponse(
        current_period_spending=current,
        previous_period_spending=previous,
        change_amount=change,
        change_percentage=change_pct,
    )
