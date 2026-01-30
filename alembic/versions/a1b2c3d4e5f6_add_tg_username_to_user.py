"""Add tg_username to User model

Revision ID: a1b2c3d4e5f6
Revises: f1a4c9d8e3ab
Create Date: 2026-01-30 19:50:49.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "f1a4c9d8e3ab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.
    
    Add tg_username field to users table to store Telegram username,
    and allow username to be empty string for user-created usernames.
    """
    op.add_column("users", sa.Column("tg_username", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "tg_username")
