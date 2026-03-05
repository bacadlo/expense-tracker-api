from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundException
from app.models.category import Category
from app.models.transaction import Transaction, TransactionType
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.services import transaction_service


class TestTransactionService:
    """Test transaction service functions."""

    @pytest.mark.asyncio
    async def test_create_transaction(self, async_db: AsyncSession, sample_category):
        """Test creating a transaction."""
        data = TransactionCreate(
            amount=Decimal("100.00"),
            type=TransactionType.EXPENSE,
            description="Test expense",
            date=date(2024, 1, 10),
            category_id=sample_category.id,
        )

        txn = await transaction_service.create_transaction(async_db, data)

        assert txn.id is not None
        assert txn.amount == Decimal("100.00")
        assert txn.type == TransactionType.EXPENSE
        assert txn.description == "Test expense"
        assert txn.date == date(2024, 1, 10)
        assert txn.category_id == sample_category.id

    @pytest.mark.asyncio
    async def test_get_transaction(self, async_db: AsyncSession, sample_transaction):
        """Test getting a transaction."""
        txn = await transaction_service.get_transaction(
            async_db, sample_transaction.id
        )

        assert txn.id == sample_transaction.id
        assert txn.amount == Decimal("50.00")
        assert txn.type == TransactionType.EXPENSE

    @pytest.mark.asyncio
    async def test_get_transaction_not_found(self, async_db: AsyncSession):
        """Test getting a non-existent transaction."""
        with pytest.raises(NotFoundException) as exc_info:
            await transaction_service.get_transaction(async_db, 9999)

        assert "Transaction" in str(exc_info.value.message)
        assert "9999" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_list_transactions(self, async_db: AsyncSession, sample_transaction):
        """Test listing transactions."""
        transactions, total = await transaction_service.list_transactions(async_db)

        assert len(transactions) > 0
        assert total >= 1

    @pytest.mark.asyncio
    async def test_list_transactions_with_filters(
        self, async_db: AsyncSession, sample_category
    ):
        """Test listing transactions with filters."""
        # Create multiple transactions
        for i in range(3):
            txn = Transaction(
                amount=Decimal("25.00"),
                type=TransactionType.EXPENSE,
                description=f"Expense {i}",
                date=date(2024, 1, i + 1),
                category_id=sample_category.id,
            )
            async_db.add(txn)

        await async_db.flush()

        # Filter by category
        transactions, total = await transaction_service.list_transactions(
            async_db, category_id=sample_category.id
        )
        assert total >= 3

        # Filter by type
        transactions, total = await transaction_service.list_transactions(
            async_db, type=TransactionType.EXPENSE
        )
        assert total >= 3

        # Filter by date range
        transactions, total = await transaction_service.list_transactions(
            async_db, start_date=date(2024, 1, 1), end_date=date(2024, 1, 31)
        )
        assert total >= 3

    @pytest.mark.asyncio
    async def test_list_transactions_pagination(
        self, async_db: AsyncSession, sample_category
    ):
        """Test pagination in list_transactions."""
        # Create 25 transactions
        for i in range(25):
            txn = Transaction(
                amount=Decimal("10.00"),
                type=TransactionType.INCOME,
                description=f"Income {i}",
                date=date(2024, 1, 1),
                category_id=sample_category.id,
            )
            async_db.add(txn)

        await async_db.flush()

        # Test first page
        page1, total = await transaction_service.list_transactions(
            async_db, page=1, per_page=10
        )
        assert len(page1) == 10
        assert total >= 25

        # Test second page
        page2, total = await transaction_service.list_transactions(
            async_db, page=2, per_page=10
        )
        assert len(page2) == 10

    @pytest.mark.asyncio
    async def test_update_transaction(
        self, async_db: AsyncSession, sample_transaction
    ):
        """Test updating a transaction."""
        update_data = TransactionUpdate(
            amount=Decimal("75.50"),
            description="Updated description",
        )

        updated = await transaction_service.update_transaction(
            async_db, sample_transaction.id, update_data
        )

        assert updated.id == sample_transaction.id
        assert updated.amount == Decimal("75.50")
        assert updated.description == "Updated description"
        assert updated.type == TransactionType.EXPENSE  # unchanged

    @pytest.mark.asyncio
    async def test_update_transaction_not_found(self, async_db: AsyncSession):
        """Test updating a non-existent transaction."""
        update_data = TransactionUpdate(amount=Decimal("100.00"))

        with pytest.raises(NotFoundException):
            await transaction_service.update_transaction(async_db, 9999, update_data)

    @pytest.mark.asyncio
    async def test_delete_transaction(
        self, async_db: AsyncSession, sample_transaction
    ):
        """Test deleting a transaction."""
        txn_id = sample_transaction.id

        await transaction_service.delete_transaction(async_db, txn_id)

        with pytest.raises(NotFoundException):
            await transaction_service.get_transaction(async_db, txn_id)

    @pytest.mark.asyncio
    async def test_delete_transaction_not_found(self, async_db: AsyncSession):
        """Test deleting a non-existent transaction."""
        with pytest.raises(NotFoundException):
            await transaction_service.delete_transaction(async_db, 9999)


class TestTransactionEndpoints:
    """Test transaction API endpoints."""

    @pytest.mark.asyncio
    async def test_create_transaction_endpoint(
        self, client, sample_category
    ):
        """Test POST /api/transactions/"""
        response = await client.post(
            "/api/transactions/",
            json={
                "amount": "150.50",
                "type": "expense",
                "description": "Test transaction",
                "date": "2024-01-20",
                "category_id": sample_category.id,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == "150.50"
        assert data["type"] == "expense"
        assert data["description"] == "Test transaction"

    @pytest.mark.asyncio
    async def test_create_transaction_invalid_amount(self, client, sample_category):
        """Test creating transaction with invalid amount."""
        response = await client.post(
            "/api/transactions/",
            json={
                "amount": "-50.00",  # negative
                "type": "expense",
                "date": "2024-01-20",
                "category_id": sample_category.id,
            },
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_list_transactions_endpoint(self, client, sample_transaction):
        """Test GET /api/transactions/"""
        response = await client.get("/api/transactions/")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert len(data["items"]) > 0

    @pytest.mark.asyncio
    async def test_list_transactions_with_filters_endpoint(
        self, client, sample_category
    ):
        """Test GET /api/transactions/ with filters."""
        response = await client.get(
            "/api/transactions/",
            params={
                "category_id": sample_category.id,
                "type": "expense",
                "page": 1,
                "per_page": 20,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_get_transaction_endpoint(self, client, sample_transaction):
        """Test GET /api/transactions/{transaction_id}"""
        response = await client.get(f"/api/transactions/{sample_transaction.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_transaction.id
        assert data["amount"] == "50.00"

    @pytest.mark.asyncio
    async def test_get_transaction_not_found_endpoint(self, client):
        """Test GET /api/transactions/{transaction_id} with non-existent id."""
        response = await client.get("/api/transactions/9999")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_transaction_endpoint(self, client, sample_transaction):
        """Test PUT /api/transactions/{transaction_id}"""
        response = await client.put(
            f"/api/transactions/{sample_transaction.id}",
            json={
                "amount": "99.99",
                "description": "Updated via API",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == "99.99"
        assert data["description"] == "Updated via API"

    @pytest.mark.asyncio
    async def test_delete_transaction_endpoint(self, client, sample_transaction):
        """Test DELETE /api/transactions/{transaction_id}"""
        response = await client.delete(f"/api/transactions/{sample_transaction.id}")

        assert response.status_code == 204

        # Verify deletion
        response = await client.get(f"/api/transactions/{sample_transaction.id}")
        assert response.status_code == 404