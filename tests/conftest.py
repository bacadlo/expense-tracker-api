import asyncio
import os
import sys
from datetime import date, datetime
from decimal import Decimal

# Set test environment before any app imports
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["APP_ENV"] = "test"
os.environ["DEBUG"] = "false"

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.budget import Budget
from app.models.category import Category
from app.models.transaction import Transaction, TransactionType


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def async_db():
    """Create a test database and return a session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def app_with_db(async_db):
    """Create FastAPI app with test database."""
    from app.main import create_app
    from app.database import get_db

    app = create_app()

    async def override_get_db():
        yield async_db

    app.dependency_overrides[get_db] = override_get_db
    yield app


@pytest_asyncio.fixture
async def client(app_with_db):
    """Create a test client."""
    from httpx import ASGITransport

    async with AsyncClient(transport=ASGITransport(app=app_with_db), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def sample_category(async_db):
    """Create a sample category."""
    category = Category(
        name="Food & Dining",
        description="Food and restaurant expenses",
    )
    async_db.add(category)
    await async_db.flush()
    await async_db.refresh(category)
    return category


@pytest_asyncio.fixture
async def sample_transaction(async_db, sample_category):
    """Create a sample transaction."""
    txn = Transaction(
        amount=Decimal("50.00"),
        type=TransactionType.EXPENSE,
        description="Dinner",
        date=date(2024, 1, 15),
        category_id=sample_category.id,
    )
    async_db.add(txn)
    await async_db.flush()
    await async_db.refresh(txn)
    return txn


@pytest_asyncio.fixture
async def sample_budget(async_db, sample_category):
    """Create a sample budget."""
    budget = Budget(
        name="Monthly Food Budget",
        amount=Decimal("500.00"),
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
        category_id=sample_category.id,
    )
    async_db.add(budget)
    await async_db.flush()
    await async_db.refresh(budget)
    return budget
