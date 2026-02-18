from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Category(TimestampMixin, Base):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(String(255))

    transactions: Mapped[list["Transaction"]] = relationship(  # noqa: F821
        back_populates="category",
    )
    budgets: Mapped[list["Budget"]] = relationship(  # noqa: F821
        back_populates="category",
    )
