"""wqe

Revision ID: cde518b5be8b
Revises: d2e48eede09a
Create Date: 2026-01-18 22:46:11.991848

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'cde518b5be8b'
down_revision: Union[str, Sequence[str], None] = 'd2e48eede09a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('users', 'birth_date')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('users', sa.Column('birth_date', sa.DATE(), autoincrement=False, nullable=True))