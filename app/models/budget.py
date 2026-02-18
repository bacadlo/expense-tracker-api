from datetime import date
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Budget(TimestampMixin, Base):
    __tablename__ = "budgets"

    name: Mapped[str] = mapped_column(String(100))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    start_date: Mapped[date]
    end_date: Mapped[date]
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))

    category: Mapped["Category | None"] = relationship(back_populates="budgets")  # noqa: F821
