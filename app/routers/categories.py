from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.exceptions import ConflictException, NotFoundException
from app.models.category import Category
from app.models.transaction import Transaction
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.post("/", response_model=CategoryResponse, status_code=201)
async def create_category(data: CategoryCreate, db: AsyncSession = Depends(get_db)):
    category = Category(**data.model_dump())
    db.add(category)
    await db.flush()
    await db.refresh(category)
    return category


@router.get("/", response_model=list[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).order_by(Category.name))
    return list(result.scalars().all())


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, db: AsyncSession = Depends(get_db)):
    category = await db.get(Category, category_id)
    if not category:
        raise NotFoundException("Category", category_id)
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int, data: CategoryUpdate, db: AsyncSession = Depends(get_db)
):
    category = await db.get(Category, category_id)
    if not category:
        raise NotFoundException("Category", category_id)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(category, field, value)

    await db.flush()
    await db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=204)
async def delete_category(category_id: int, db: AsyncSession = Depends(get_db)):
    category = await db.get(Category, category_id)
    if not category:
        raise NotFoundException("Category", category_id)

    # Check for existing transactions
    count = (
        await db.execute(
            select(func.count(Transaction.id)).where(Transaction.category_id == category_id)
        )
    ).scalar_one()

    if count > 0:
        raise ConflictException(
            f"Cannot delete category: {count} transaction(s) still reference it"
        )

    await db.delete(category)
    await db.flush()
