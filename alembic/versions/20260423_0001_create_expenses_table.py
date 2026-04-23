"""create expenses table

Revision ID: 20260423_0001
Revises: 
Create Date: 2026-04-23

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

from sqlalchemy.dialects.postgresql import UUID

revision = "20260423_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Cross-db: store UUID as CHAR(36) to support SQLite local dev.
    # PostgreSQL uses native UUID at runtime via `app.models.GUID`.
    op.create_table(
        "expenses",
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_expenses_category"), "expenses", ["category"], unique=False)
    op.create_index(op.f("ix_expenses_date"), "expenses", ["date"], unique=False)
    op.create_index(op.f("ix_expenses_created_at"), "expenses", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_expenses_created_at"), table_name="expenses")
    op.drop_index(op.f("ix_expenses_date"), table_name="expenses")
    op.drop_index(op.f("ix_expenses_category"), table_name="expenses")
    op.drop_table("expenses")

