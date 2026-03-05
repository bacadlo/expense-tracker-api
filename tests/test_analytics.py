from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction, TransactionType
from app.services import analytics_service


class TestAnalyticsService:
    """Test analytics service functions."""

    @pytest.mark.asyncio
    async def test_get_balance_no_transactions(self, async_db: AsyncSession):
        """Test getting balance with no transactions."""
        balance = await analytics_service.get_balance(async_db)

        assert balance.total_income == Decimal("0")
        assert balance.total_expenses == Decimal("0")
        assert balance.net_balance == Decimal("0")

    @pytest.mark.asyncio
    async def test_get_balance_with_transactions(
        self, async_db: AsyncSession, sample_category
    ):
        """Test getting balance with transactions."""
        # Add income transaction
        income = Transaction(
            amount=Decimal("1000.00"),
            type=TransactionType.INCOME,
            date=date(2024, 1, 1),
            category_id=sample_category.id,
        )
        async_db.add(income)

        # Add expense transaction
        expense = Transaction(
            amount=Decimal("300.00"),
            type=TransactionType.EXPENSE,
            date=date(2024, 1, 5),
            category_id=sample_category.id,
        )
        async_db.add(expense)
        await async_db.flush()

        balance = await analytics_service.get_balance(async_db)

        assert balance.total_income == Decimal("1000.00")
        assert balance.total_expenses == Decimal("300.00")
        assert balance.net_balance == Decimal("700.00")

    @pytest.mark.asyncio
    async def test_get_balance_with_date_range(
        self, async_db: AsyncSession, sample_category
    ):
        """Test getting balance within a date range."""
        # Add transactions on different dates
        txn1 = Transaction(
            amount=Decimal("100.00"),
            type=TransactionType.EXPENSE,
            date=date(2024, 1, 15),
            category_id=sample_category.id,
        )
        txn2 = Transaction(
            amount=Decimal("200.00"),
            type=TransactionType.EXPENSE,
            date=date(2024, 2, 15),
            category_id=sample_category.id,
        )
        async_db.add(txn1)
        async_db.add(txn2)
        await async_db.flush()

        # Get balance for January only
        balance = await analytics_service.get_balance(
            async_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

        assert balance.total_expenses == Decimal("100.00")

    @pytest.mark.asyncio
    async def test_get_spending_by_category(self, async_db: AsyncSession):
        """Test getting spending breakdown by category."""
        from app.models.category import Category

        # Create two categories
        cat1 = Category(name="Food", description="Food expenses")
        cat2 = Category(name="Transport", description="Transport expenses")
        async_db.add(cat1)
        async_db.add(cat2)
        await async_db.flush()

        # Add transactions
        txn1 = Transaction(
            amount=Decimal("50.00"),
            type=TransactionType.EXPENSE,
            date=date(2024, 1, 1),
            category_id=cat1.id,
        )
        txn2 = Transaction(
            amount=Decimal("30.00"),
            type=TransactionType.EXPENSE,
            date=date(2024, 1, 2),
            category_id=cat2.id,
        )
        async_db.add(txn1)
        async_db.add(txn2)
        await async_db.flush()

        response = await analytics_service.get_spending_by_category(async_db)

        assert response.total_spending == Decimal("80.00")
        assert len(response.items) == 2
        # Verify percentages add up
        total_pct = sum(item.percentage for item in response.items)
        assert abs(total_pct - 100.0) < 0.01  # Account for rounding

    @pytest.mark.asyncio
    async def test_get_spending_by_category_empty(self, async_db: AsyncSession):
        """Test spending by category with no expenses."""
        response = await analytics_service.get_spending_by_category(async_db)

        assert response.total_spending == Decimal("0")
        assert len(response.items) == 0

    @pytest.mark.asyncio
    async def test_get_monthly_summary(self, async_db: AsyncSession, sample_category):
        """Test getting monthly summary."""
        # Add transactions for different months
        txn1 = Transaction(
            amount=Decimal("100.00"),
            type=TransactionType.INCOME,
            date=date(2024, 1, 15),
            category_id=sample_category.id,
        )
        txn2 = Transaction(
            amount=Decimal("30.00"),
            type=TransactionType.EXPENSE,
            date=date(2024, 1, 20),
            category_id=sample_category.id,
        )
        txn3 = Transaction(
            amount=Decimal("200.00"),
            type=TransactionType.INCOME,
            date=date(2024, 2, 10),
            category_id=sample_category.id,
        )
        async_db.add(txn1)
        async_db.add(txn2)
        async_db.add(txn3)
        await async_db.flush()

        response = await analytics_service.get_monthly_summary(async_db, year=2024)

        # January should have income and expenses
        jan = next((item for item in response.items if item.month == 1), None)
        assert jan is not None
        assert jan.income == Decimal("100.00")
        assert jan.expenses == Decimal("30.00")
        assert jan.net == Decimal("70.00")

        # February should have income only
        feb = next((item for item in response.items if item.month == 2), None)
        assert feb is not None
        assert feb.income == Decimal("200.00")
        assert feb.expenses == Decimal("0")

    @pytest.mark.asyncio
    async def test_get_budget_status(self, async_db: AsyncSession):
        """Test getting budget status for active budgets."""
        from app.models.budget import Budget
        from app.models.category import Category

        cat = Category(name="TestBudgetStatus", description="Test category")
        async_db.add(cat)
        await async_db.flush()

        # Create active budget (with dates that include today)
        today = date.today()
        budget = Budget(
            name="Active Budget",
            amount=Decimal("500.00"),
            start_date=today.replace(day=1),
            end_date=today.replace(day=28) if today.month != 2 else today.replace(day=29),
            category_id=cat.id,
        )
        async_db.add(budget)
        await async_db.flush()

        # Add expense transaction (within budget period)
        txn = Transaction(
            amount=Decimal("150.00"),
            type=TransactionType.EXPENSE,
            date=today,
            category_id=cat.id,
        )
        async_db.add(txn)
        await async_db.flush()

        response = await analytics_service.get_budget_status(async_db)

        assert len(response.items) == 1
        item = response.items[0]
        assert item.budget_id == budget.id
        assert item.spent == Decimal("150.00")
        assert item.remaining == Decimal("350.00")
        assert item.percentage_used == 30.0

    @pytest.mark.asyncio
    async def test_get_trends(self, async_db: AsyncSession, sample_category):
        """Test getting spending trends."""
        from datetime import datetime

        # Add current month expense
        today = date.today()
        current_month_start = today.replace(day=1)
        current_txn = Transaction(
            amount=Decimal("100.00"),
            type=TransactionType.EXPENSE,
            date=current_month_start,
            category_id=sample_category.id,
        )
        async_db.add(current_txn)
        await async_db.flush()

        response = await analytics_service.get_trends(async_db, period="monthly")

        assert response.current_period_spending == Decimal("100.00")
        # previous_period_spending could be 0 if no transactions in previous month


class TestAnalyticsEndpoints:
    """Test analytics API endpoints."""

    @pytest.mark.asyncio
    async def test_get_balance_endpoint(self, client, sample_transaction):
        """Test GET /api/analytics/balance"""
        response = await client.get("/api/analytics/balance")

        assert response.status_code == 200
        data = response.json()
        assert "total_income" in data
        assert "total_expenses" in data
        assert "net_balance" in data

    @pytest.mark.asyncio
    async def test_get_balance_with_date_range_endpoint(self, client):
        """Test GET /api/analytics/balance with date range."""
        response = await client.get(
            "/api/analytics/balance",
            params={
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_income" in data

    @pytest.mark.asyncio
    async def test_get_spending_by_category_endpoint(self, client):
        """Test GET /api/analytics/spending-by-category"""
        response = await client.get("/api/analytics/spending-by-category")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total_spending" in data

    @pytest.mark.asyncio
    async def test_get_monthly_summary_endpoint(self, client):
        """Test GET /api/analytics/monthly-summary"""
        response = await client.get("/api/analytics/monthly-summary?year=2024")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "year" in data
        assert data["year"] == 2024

    @pytest.mark.asyncio
    async def test_get_budget_status_endpoint(self, client):
        """Test GET /api/analytics/budget-status"""
        response = await client.get("/api/analytics/budget-status")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_get_trends_monthly_endpoint(self, client):
        """Test GET /api/analytics/trends with monthly period."""
        response = await client.get("/api/analytics/trends?period=monthly")

        assert response.status_code == 200
        data = response.json()
        assert "current_period_spending" in data
        assert "previous_period_spending" in data
        assert "change_amount" in data

    @pytest.mark.asyncio
    async def test_get_trends_weekly_endpoint(self, client):
        """Test GET /api/analytics/trends with weekly period."""
        response = await client.get("/api/analytics/trends?period=weekly")

        assert response.status_code == 200
        data = response.json()
        assert "current_period_spending" in data

    @pytest.mark.asyncio
    async def test_get_trends_invalid_period_endpoint(self, client):
        """Test GET /api/analytics/trends with invalid period."""
        response = await client.get("/api/analytics/trends?period=invalid")

        assert response.status_code == 422  # Validation error