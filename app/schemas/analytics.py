from decimal import Decimal

from pydantic import BaseModel


class BalanceResponse(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    net_balance: Decimal


class CategoryBreakdown(BaseModel):
    category_id: int
    category_name: str
    total: Decimal
    percentage: float


class SpendingByCategoryResponse(BaseModel):
    items: list[CategoryBreakdown]
    total_spending: Decimal


class MonthlySummaryItem(BaseModel):
    month: int
    year: int
    income: Decimal
    expenses: Decimal
    net: Decimal


class MonthlySummaryResponse(BaseModel):
    items: list[MonthlySummaryItem]
    year: int


class BudgetStatusItem(BaseModel):
    budget_id: int
    budget_name: str
    budget_amount: Decimal
    category_name: str | None
    spent: Decimal
    remaining: Decimal
    percentage_used: float


class BudgetStatusResponse(BaseModel):
    items: list[BudgetStatusItem]


class TrendResponse(BaseModel):
    current_period_spending: Decimal
    previous_period_spending: Decimal
    change_amount: Decimal
    change_percentage: float | None
