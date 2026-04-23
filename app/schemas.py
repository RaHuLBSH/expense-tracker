from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from pydantic import Field, condecimal


class APIBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


MoneyDecimal = condecimal(max_digits=12, decimal_places=2)


class ExpenseCreate(APIBaseSchema):
    amount: MoneyDecimal = Field(..., gt=0, description="Amount in major currency units (2dp).")
    category: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    date: date


class ExpenseRead(APIBaseSchema):
    id: UUID
    amount: Decimal
    category: str
    description: str | None
    date: date
    created_at: datetime


class ExpenseListResponse(APIBaseSchema):
    items: list[ExpenseRead]
    # Keep precision: serialize as string (never float).
    total_amount: str
