"""Add stats JSON to listings + last_run_at to schedules.

Revision ID: 0002
Revises: 0001
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("listings",
                  sa.Column("stats", sa.JSON(), nullable=False,
                            server_default="{}"))
    op.add_column("schedules",
                  sa.Column("last_run_at", sa.DateTime(timezone=True),
                            nullable=True))


def downgrade() -> None:
    op.drop_column("schedules", "last_run_at")
    op.drop_column("listings", "stats")
