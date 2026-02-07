"""Rename match status to is_finished and add finished_at

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-02-07 14:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3d4e5f6g7h8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6g7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.
    
    Rename status column to is_finished (change type from string to boolean)
    and add finished_at timestamp column.
    """
    # Add new columns
    op.add_column("matches", sa.Column("is_finished", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("matches", sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True))
    
    # Drop old status column
    op.drop_column("matches", "status")


def downgrade() -> None:
    """Downgrade schema."""
    # Add back status column
    op.add_column("matches", sa.Column("status", sa.String(), nullable=False, server_default="Not Started"))
    
    # Drop new columns
    op.drop_column("matches", "finished_at")
    op.drop_column("matches", "is_finished")
