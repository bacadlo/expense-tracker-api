from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictException, NotFoundException
from app.models.category import Category
from app.models.transaction import Transaction, TransactionType


class TestCategoryEndpoints:
    """Test category API endpoints."""

    @pytest.mark.asyncio
    async def test_create_category(self, client):
        """Test POST /api/categories/"""
        response = await client.post(
            "/api/categories/",
            json={
                "name": "Travel",
                "description": "Travel and transportation expenses",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Travel"
        assert data["description"] == "Travel and transportation expenses"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_category_minimal(self, client):
        """Test creating category with minimal fields."""
        response = await client.post(
            "/api/categories/",
            json={"name": "Entertainment"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Entertainment"
        assert data["description"] is None

    @pytest.mark.asyncio
    async def test_create_category_long_name(self, client):
        """Test creating category with long name."""
        long_name = "A" * 100  # Test with long category name
        response = await client.post(
            "/api/categories/",
            json={"name": long_name},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == long_name

    @pytest.mark.asyncio
    async def test_list_categories(self, client, sample_category):
        """Test GET /api/categories/"""
        response = await client.get("/api/categories/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Check that categories are sorted by name
        names = [cat["name"] for cat in data]
        assert names == sorted(names)

    @pytest.mark.asyncio
    async def test_get_category(self, client, sample_category):
        """Test GET /api/categories/{category_id}"""
        response = await client.get(f"/api/categories/{sample_category.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_category.id
        assert data["name"] == sample_category.name

    @pytest.mark.asyncio
    async def test_get_category_not_found(self, client):
        """Test GET /api/categories/{category_id} with non-existent id."""
        response = await client.get("/api/categories/9999")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_category(self, client, sample_category):
        """Test PUT /api/categories/{category_id}"""
        response = await client.put(
            f"/api/categories/{sample_category.id}",
            json={
                "name": "Updated Category",
                "description": "Updated description",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Category"
        assert data["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_update_category_partial(self, client, sample_category):
        """Test partial update of category."""
        response = await client.put(
            f"/api/categories/{sample_category.id}",
            json={"description": "Only updating description"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_category.name  # unchanged
        assert data["description"] == "Only updating description"

    @pytest.mark.asyncio
    async def test_update_category_not_found(self, client):
        """Test updating non-existent category."""
        response = await client.put(
            "/api/categories/9999",
            json={"name": "New Name"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_category(self, client, sample_category):
        """Test DELETE /api/categories/{category_id}"""
        response = await client.delete(f"/api/categories/{sample_category.id}")

        assert response.status_code == 204

        # Verify deletion
        response = await client.get(f"/api/categories/{sample_category.id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_category_not_found(self, client):
        """Test deleting non-existent category."""
        response = await client.delete("/api/categories/9999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_category_with_transactions(
        self, client, async_db, sample_category, sample_transaction
    ):
        """Test deleting category that has transactions."""
        response = await client.delete(f"/api/categories/{sample_category.id}")

        # Should fail due to existing transactions
        assert response.status_code == 409
        data = response.json()
        assert "detail" in data
        assert "transaction" in data["detail"].lower()