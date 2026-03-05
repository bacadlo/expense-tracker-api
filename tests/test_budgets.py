from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundException
from app.models.budget import Budget
from app.models.transaction import Transaction, TransactionType
from app.services import budget_service


class TestBudgetService:
    """Test budget service functions."""

    @pytest.mark.asyncio
    async def test_create_budget(self, async_db: AsyncSession, sample_category):
        """Test creating a budget."""
        from app.schemas.budget import BudgetCreate

        data = BudgetCreate(
            name="January Budget",
            amount=Decimal("1000.00"),
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            category_id=sample_category.id,
        )

        budget = await budget_service.create_budget(async_db, data)

        assert budget.id is not None
        assert budget.name == "January Budget"
        assert budget.amount == Decimal("1000.00")

    @pytest.mark.asyncio
    async def test_create_budget_invalid_dates(self, async_db: AsyncSession):
        """Test creating budget with invalid date range."""
        from app.schemas.budget import BudgetCreate

        with pytest.raises(ValueError, match="end_date must be after start_date"):
            data = BudgetCreate(
                name="Invalid Budget",
                amount=Decimal("500.00"),
                start_date=date(2024, 1, 31),
                end_date=date(2024, 1, 1),  # end before start
                category_id=None,
            )

    @pytest.mark.asyncio
    async def test_get_budget(self, async_db: AsyncSession, sample_budget):
        """Test getting a budget."""
        budget = await budget_service.get_budget(async_db, sample_budget.id)

        assert budget.id == sample_budget.id
        assert budget.name == sample_budget.name

    @pytest.mark.asyncio
    async def test_get_budget_not_found(self, async_db: AsyncSession):
        """Test getting non-existent budget."""
        with pytest.raises(NotFoundException):
            await budget_service.get_budget(async_db, 9999)

    @pytest.mark.asyncio
    async def test_get_budget_detail(
        self, async_db: AsyncSession, sample_budget, sample_category
    ):
        """Test getting budget detail with spent calculation."""
        # Add a transaction within budget scope
        txn = Transaction(
            amount=Decimal("100.00"),
            type=TransactionType.EXPENSE,
            date=date(2024, 1, 15),
            category_id=sample_category.id,
        )
        async_db.add(txn)
        await async_db.flush()

        detail = await budget_service.get_budget_detail(async_db, sample_budget.id)

        assert detail.id == sample_budget.id
        assert detail.spent == Decimal("100.00")
        assert detail.remaining == Decimal("400.00")
        assert detail.percentage_used == 20.0

    @pytest.mark.asyncio
    async def test_list_budgets(self, async_db: AsyncSession, sample_budget):
        """Test listing budgets."""
        budgets = await budget_service.list_budgets(async_db)

        assert len(budgets) > 0
        assert any(b.id == sample_budget.id for b in budgets)

    @pytest.mark.asyncio
    async def test_update_budget(self, async_db: AsyncSession, sample_budget):
        """Test updating a budget."""
        from app.schemas.budget import BudgetUpdate

        update_data = BudgetUpdate(
            name="Updated Budget",
            amount=Decimal("1500.00"),
        )

        updated = await budget_service.update_budget(
            async_db, sample_budget.id, update_data
        )

        assert updated.name == "Updated Budget"
        assert updated.amount == Decimal("1500.00")

    @pytest.mark.asyncio
    async def test_update_budget_invalid_dates(
        self, async_db: AsyncSession, sample_budget
    ):
        """Test updating budget with invalid dates."""
        from app.schemas.budget import BudgetUpdate

        update_data = BudgetUpdate(
            start_date=date(2024, 1, 31),
            end_date=date(2024, 1, 1),
        )

        with pytest.raises(ValueError, match="end_date must be after start_date"):
            await budget_service.update_budget(async_db, sample_budget.id, update_data)

    @pytest.mark.asyncio
    async def test_delete_budget(self, async_db: AsyncSession, sample_budget):
        """Test deleting a budget."""
        budget_id = sample_budget.id

        await budget_service.delete_budget(async_db, budget_id)

        with pytest.raises(NotFoundException):
            await budget_service.get_budget(async_db, budget_id)


class TestBudgetEndpoints:
    """Test budget API endpoints."""

    @pytest.mark.asyncio
    async def test_create_budget_endpoint(self, client, sample_category):
        """Test POST /api/budgets/"""
        response = await client.post(
            "/api/budgets/",
            json={
                "name": "February Budget",
                "amount": "800.00",
                "start_date": "2024-02-01",
                "end_date": "2024-02-29",
                "category_id": sample_category.id,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "February Budget"
        assert data["amount"] == "800.00"

    @pytest.mark.asyncio
    async def test_create_budget_invalid_dates_endpoint(self, client, sample_category):
        """Test creating budget with invalid date range."""
        response = await client.post(
            "/api/budgets/",
            json={
                "name": "Invalid Budget",
                "amount": "500.00",
                "start_date": "2024-01-31",
                "end_date": "2024-01-01",
                "category_id": sample_category.id,
            },
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_budget_no_category(self, client):
        """Test creating budget without category."""
        response = await client.post(
            "/api/budgets/",
            json={
                "name": "Overall Budget",
                "amount": "2000.00",
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["category_id"] is None

    @pytest.mark.asyncio
    async def test_list_budgets_endpoint(self, client, sample_budget):
        """Test GET /api/budgets/"""
        response = await client.get("/api/budgets/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_get_budget_endpoint(self, client, sample_budget):
        """Test GET /api/budgets/{budget_id}"""
        response = await client.get(f"/api/budgets/{sample_budget.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_budget.id
        assert data["name"] == sample_budget.name
        assert "spent" in data
        assert "remaining" in data
        assert "percentage_used" in data

    @pytest.mark.asyncio
    async def test_get_budget_not_found_endpoint(self, client):
        """Test GET /api/budgets/{budget_id} with non-existent id."""
        response = await client.get("/api/budgets/9999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_budget_endpoint(self, client, sample_budget):
        """Test PUT /api/budgets/{budget_id}"""
        response = await client.put(
            f"/api/budgets/{sample_budget.id}",
            json={
                "name": "Updated Budget Name",
                "amount": "1200.00",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Budget Name"
        assert data["amount"] == "1200.00"

    @pytest.mark.asyncio
    async def test_delete_budget_endpoint(self, client, sample_budget):
        """Test DELETE /api/budgets/{budget_id}"""
        response = await client.delete(f"/api/budgets/{sample_budget.id}")

        assert response.status_code == 204

        # Verify deletion
        response = await client.get(f"/api/budgets/{sample_budget.id}")
        assert response.status_code == 404