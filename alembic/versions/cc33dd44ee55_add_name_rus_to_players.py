"""add name_rus to players

Revision ID: cc33dd44ee55
Revises: bb22cc33dd44
Create Date: 2026-02-05 17:28:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc33dd44ee55'
down_revision: Union[str, Sequence[str], None] = 'bb22cc33dd44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add name_rus column to players table."""
    op.add_column('players', sa.Column('name_rus', sa.String(), nullable=True))


def downgrade() -> None:
    """Remove name_rus column from players table."""
    op.drop_column('players', 'name_rus')
