from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Expense


def test_create_expense_success(client, db_session: Session):
    payload = {"amount": "12.50", "category": "Food", "description": "Lunch", "date": "2026-04-23"}
    r = client.post("/expenses", json=payload, headers={"Idempotency-Key": "k1"})
    assert r.status_code == 201
    body = r.json()

    assert body["id"]
    assert body["category"] == "Food"
    assert body["description"] == "Lunch"
    assert body["date"] == "2026-04-23"
    assert body["created_at"]
    assert Decimal(body["amount"]) == Decimal("12.50")

    count = db_session.query(func.count(Expense.id)).scalar()
    assert count == 1


def test_create_expense_validation_amount_gt_zero(client, db_session: Session):
    payload = {"amount": "0.00", "category": "Food", "description": "Lunch", "date": "2026-04-23"}
    r = client.post("/expenses", json=payload, headers={"Idempotency-Key": "k_amount"})
    assert r.status_code == 422

    count = db_session.query(func.count(Expense.id)).scalar()
    assert count == 0


def test_idempotency_replay_same_request_returns_same_response_and_no_duplicate(client, db_session: Session):
    payload = {"amount": "10.00", "category": "Bills", "description": "Internet", "date": "2026-04-01"}
    headers = {"Idempotency-Key": "idem-1"}

    r1 = client.post("/expenses", json=payload, headers=headers)
    assert r1.status_code == 201
    b1 = r1.json()

    r2 = client.post("/expenses", json=payload, headers=headers)
    assert r2.status_code == 201
    b2 = r2.json()

    assert b2 == b1
    count = db_session.query(func.count(Expense.id)).scalar()
    assert count == 1


def test_idempotency_same_key_different_payload_returns_conflict(client, db_session: Session):
    payload1 = {"amount": "10.00", "category": "Bills", "description": "Internet", "date": "2026-04-01"}
    payload2 = {"amount": "11.00", "category": "Bills", "description": "Internet", "date": "2026-04-01"}
    headers = {"Idempotency-Key": "idem-2"}

    r1 = client.post("/expenses", json=payload1, headers=headers)
    assert r1.status_code == 201

    r2 = client.post("/expenses", json=payload2, headers=headers)
    assert r2.status_code == 409

    count = db_session.query(func.count(Expense.id)).scalar()
    assert count == 1


def test_filter_by_category(client, db_session: Session):
    client.post(
        "/expenses",
        json={"amount": "5.00", "category": "Food", "description": None, "date": "2026-04-10"},
        headers={"Idempotency-Key": "f1"},
    )
    client.post(
        "/expenses",
        json={"amount": "7.00", "category": "Travel", "description": None, "date": "2026-04-11"},
        headers={"Idempotency-Key": "f2"},
    )

    r = client.get("/expenses", params={"category": "Food"})
    assert r.status_code == 200
    body = r.json()
    assert "items" in body
    assert "total_amount" in body
    assert body["total_amount"] == "5.00"
    items = body["items"]
    assert len(items) == 1
    assert items[0]["category"] == "Food"


def test_sort_by_date_desc(client, db_session: Session):
    client.post(
        "/expenses",
        json={"amount": "1.00", "category": "Misc", "description": None, "date": "2026-04-01"},
        headers={"Idempotency-Key": "s1"},
    )
    client.post(
        "/expenses",
        json={"amount": "2.00", "category": "Misc", "description": None, "date": "2026-04-30"},
        headers={"Idempotency-Key": "s2"},
    )

    r = client.get("/expenses", params={"sort": "date_desc"})
    assert r.status_code == 200
    body = r.json()
    items = body["items"]
    assert len(items) == 2
    assert items[0]["date"] == "2026-04-30"
    assert items[1]["date"] == "2026-04-01"

    assert body["total_amount"] == "3.00"

