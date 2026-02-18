import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.transaction import TransactionType


class TransactionCreate(BaseModel):
    amount: Decimal = Field(gt=0, decimal_places=2)
    type: TransactionType
    description: str | None = None
    date: datetime.date
    category_id: int


class TransactionUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    type: TransactionType | None = None
    description: str | None = None
    date: datetime.date | None = None
    category_id: int | None = None


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    type: TransactionType
    description: str | None
    date: datetime.date
    category_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime


class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    total: int
    page: int
    per_page: int
