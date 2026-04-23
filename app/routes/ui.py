from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Expense

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(tags=["ui"])


@router.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    category: str | None = None,
    sort: str | None = "date_desc",
    db: Session = Depends(get_db),
):
    q = db.query(Expense)
    if category:
        q = q.filter(Expense.category == category)

    if sort in (None, "", "date_desc"):
        q = q.order_by(Expense.date.desc(), Expense.created_at.desc())
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sort value. Supported: date_desc")

    items = q.all()
    total = db.query(func.coalesce(func.sum(Expense.amount), 0)).select_from(Expense)
    if category:
        total = total.filter(Expense.category == category)
    total_val = total.scalar()
    if not isinstance(total_val, Decimal):
        total_val = Decimal(str(total_val))
    total_amount = str(total_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "items": items,
            "total_amount": total_amount,
            "category": category or "",
            "sort": sort or "date_desc",
        },
    )


@router.post("/ui/expenses", response_class=HTMLResponse)
def create_expense_from_form(
    amount: str = Form(...),
    category: str = Form(...),
    description: str | None = Form(default=None),
    date: str = Form(...),
    db: Session = Depends(get_db),
):
    # Minimal server-side validation; API has stronger validation for clients.
    try:
        amount_dec = Decimal(amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid amount")
    if amount_dec <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Amount must be > 0")
    if not category.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Category is required")

    expense = Expense(
        amount=amount_dec,
        category=category.strip(),
        description=(description.strip() if description and description.strip() else None),
        date=date,  # SQLAlchemy will coerce ISO date string for SQLite/Postgres drivers
    )
    db.add(expense)
    db.commit()

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

