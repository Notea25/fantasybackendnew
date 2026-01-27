"""Add birth_date and registration_date to users

Revision ID: f1a4c9d8e3ab
Revises: cde518b5be8b
Create Date: 2026-01-27 17:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f1a4c9d8e3ab"
down_revision: Union[str, Sequence[str], None] = "cde518b5be8b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Re-introduce birth_date on users and add registration_date to match the
    current SQLAlchemy model.
    """
    op.add_column("users", sa.Column("birth_date", sa.Date(), nullable=True))
    op.add_column("users", sa.Column("registration_date", sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "registration_date")
    op.drop_column("users", "birth_date")
