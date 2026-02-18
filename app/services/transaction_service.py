from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundException
from app.models.transaction import Transaction, TransactionType
from app.schemas.transaction import TransactionCreate, TransactionUpdate


async def create_transaction(db: AsyncSession, data: TransactionCreate) -> Transaction:
    txn = Transaction(**data.model_dump())
    db.add(txn)
    await db.flush()
    await db.refresh(txn)
    return txn


async def get_transaction(db: AsyncSession, transaction_id: int) -> Transaction:
    txn = await db.get(Transaction, transaction_id)
    if not txn:
        raise NotFoundException("Transaction", transaction_id)
    return txn


async def list_transactions(
    db: AsyncSession,
    *,
    category_id: int | None = None,
    type: TransactionType | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[Transaction], int]:
    query = select(Transaction)
    count_query = select(func.count(Transaction.id))

    if category_id is not None:
        query = query.where(Transaction.category_id == category_id)
        count_query = count_query.where(Transaction.category_id == category_id)
    if type is not None:
        query = query.where(Transaction.type == type)
        count_query = count_query.where(Transaction.type == type)
    if start_date is not None:
        query = query.where(Transaction.date >= start_date)
        count_query = count_query.where(Transaction.date >= start_date)
    if end_date is not None:
        query = query.where(Transaction.date <= end_date)
        count_query = count_query.where(Transaction.date <= end_date)

    total = (await db.execute(count_query)).scalar_one()

    query = query.order_by(Transaction.date.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def update_transaction(
    db: AsyncSession, transaction_id: int, data: TransactionUpdate
) -> Transaction:
    txn = await get_transaction(db, transaction_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(txn, field, value)
    await db.flush()
    await db.refresh(txn)
    return txn


async def delete_transaction(db: AsyncSession, transaction_id: int) -> None:
    txn = await get_transaction(db, transaction_id)
    await db.delete(txn)
    await db.flush()
