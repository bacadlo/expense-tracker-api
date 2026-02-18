import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BudgetCreate(BaseModel):
    name: str
    amount: Decimal = Field(gt=0, decimal_places=2)
    start_date: datetime.date
    end_date: datetime.date
    category_id: int | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class BudgetUpdate(BaseModel):
    name: str | None = None
    amount: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    start_date: datetime.date | None = None
    end_date: datetime.date | None = None
    category_id: int | None = None


class BudgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    amount: Decimal
    start_date: datetime.date
    end_date: datetime.date
    category_id: int | None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class BudgetDetailResponse(BudgetResponse):
    spent: Decimal
    remaining: Decimal
    percentage_used: float
