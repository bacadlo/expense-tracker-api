from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.transaction import TransactionType
from app.schemas.transaction import (
    TransactionCreate,
    TransactionListResponse,
    TransactionResponse,
    TransactionUpdate,
)
from app.services import transaction_service

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.post("/", response_model=TransactionResponse, status_code=201)
async def create_transaction(data: TransactionCreate, db: AsyncSession = Depends(get_db)):
    return await transaction_service.create_transaction(db, data)


@router.get("/", response_model=TransactionListResponse)
async def list_transactions(
    category_id: int | None = None,
    type: TransactionType | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    items, total = await transaction_service.list_transactions(
        db,
        category_id=category_id,
        type=type,
        start_date=start_date,
        end_date=end_date,
        page=page,
        per_page=per_page,
    )
    return TransactionListResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(transaction_id: int, db: AsyncSession = Depends(get_db)):
    return await transaction_service.get_transaction(db, transaction_id)


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: int, data: TransactionUpdate, db: AsyncSession = Depends(get_db)
):
    return await transaction_service.update_transaction(db, transaction_id, data)


@router.delete("/{transaction_id}", status_code=204)
async def delete_transaction(transaction_id: int, db: AsyncSession = Depends(get_db)):
    await transaction_service.delete_transaction(db, transaction_id)
