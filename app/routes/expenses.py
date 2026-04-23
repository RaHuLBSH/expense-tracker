from __future__ import annotations

import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends
from fastapi import Header, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Expense, IdempotencyKey
from app.schemas import ExpenseCreate, ExpenseListResponse, ExpenseRead

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.get("/health")
def expenses_healthcheck(db: Session = Depends(get_db)) -> dict:
    """
    Placeholder endpoint proving router wiring + DB dependency injection.
    """

    _ = db
    return {"status": "ok"}


@router.get("", response_model=ExpenseListResponse)
def list_expenses(
    category: str | None = None,
    sort: str | None = "date_desc",
    db: Session = Depends(get_db),
) -> ExpenseListResponse:
    base_q = db.query(Expense)

    if category is not None:
        base_q = base_q.filter(Expense.category == category)

    if sort in (None, "", "date_desc"):
        items_q = base_q.order_by(Expense.date.desc(), Expense.created_at.desc())
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid sort value. Supported: date_desc",
        )

    items = items_q.all()

    # Build a separate SUM query using the same filter(s) explicitly.
    total_q = db.query(func.coalesce(func.sum(Expense.amount), 0)).select_from(Expense)
    if category is not None:
        total_q = total_q.filter(Expense.category == category)

    total: Decimal = total_q.scalar()
    if not isinstance(total, Decimal):
        total = Decimal(str(total))

    total_str = str(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    return ExpenseListResponse(items=items, total_amount=total_str)


def _request_hash(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@router.post("", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense_in: ExpenseCreate,
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> ExpenseRead | JSONResponse:
    if not idempotency_key or not idempotency_key.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Idempotency-Key header is required")

    payload = expense_in.model_dump(mode="json")
    req_hash = _request_hash(payload)

    # 1) Try to reserve the key (unique constraint makes this race-safe).
    try:
        idem = IdempotencyKey(key=idempotency_key.strip(), request_hash=req_hash)
        db.add(idem)
        db.flush()  # forces INSERT; will raise on duplicate key
    except IntegrityError:
        db.rollback()

        existing = db.query(IdempotencyKey).filter(IdempotencyKey.key == idempotency_key.strip()).first()
        if existing is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Idempotency lookup failed")

        if existing.request_hash != req_hash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Idempotency-Key already used with a different request payload",
            )

        # Same key + same payload: return the stored response, if available.
        if existing.response_body is None or existing.response_status is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Request with this Idempotency-Key is currently being processed",
            )

        return JSONResponse(status_code=existing.response_status, content=existing.response_body)

    # 2) Key reserved: create the expense and store the response atomically.
    expense = Expense(
        amount=expense_in.amount,
        category=expense_in.category,
        description=expense_in.description,
        date=expense_in.date,
    )
    db.add(expense)
    db.flush()  # assign UUID
    db.refresh(expense)

    response_model = ExpenseRead.model_validate(expense)
    response_body = response_model.model_dump(mode="json")

    idem.response_status = status.HTTP_201_CREATED
    idem.response_body = response_body

    db.commit()
    return response_model

