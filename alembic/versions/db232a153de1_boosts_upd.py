"""boosts upd

Revision ID: db232a153de1
Revises: 0b87a3ae61a5
Create Date: 2026-01-11 12:35:00.926087

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'db232a153de1'
down_revision: Union[str, Sequence[str], None] = '0b87a3ae61a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('squads', 'available_boosts')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('squads', sa.Column('available_boosts', sa.INTEGER(), autoincrement=False, nullable=False))