# Expense Tracker Backend (FastAPI)

Production-ready project scaffold (no business logic yet).

## Run locally (SQLite fallback)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Health checks:
- `GET /health`
- `GET /expenses/health`

## Use PostgreSQL

Set `DATABASE_URL` (see `.env.example`), then run:

```bash
uvicorn app.main:app --reload
```

## Migrations (recommended for production)

This repo includes Alembic.

```bash
alembic upgrade head
```

