"""2

Revision ID: 0be71e2312bf
Revises: 0394b38750b2
Create Date: 2026-01-05 12:49:35.218179

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0be71e2312bf'
down_revision: Union[str, Sequence[str], None] = '0394b38750b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('birth_date', sa.Date(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'birth_date')