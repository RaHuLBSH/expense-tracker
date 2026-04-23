"""create idempotency keys table

Revision ID: 20260423_0002
Revises: 20260423_0001
Create Date: 2026-04-23

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260423_0002"
down_revision = "20260423_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "idempotency_keys",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("response_body", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_idempotency_keys_key"), "idempotency_keys", ["key"], unique=True)
    op.create_index(op.f("ix_idempotency_keys_request_hash"), "idempotency_keys", ["request_hash"], unique=False)
    op.create_index(op.f("ix_idempotency_keys_created_at"), "idempotency_keys", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_idempotency_keys_created_at"), table_name="idempotency_keys")
    op.drop_index(op.f("ix_idempotency_keys_request_hash"), table_name="idempotency_keys")
    op.drop_index(op.f("ix_idempotency_keys_key"), table_name="idempotency_keys")
    op.drop_table("idempotency_keys")

