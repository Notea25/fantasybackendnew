"""remove age and number from players

Revision ID: g8h9i0j1k2l3
Revises: fcd9b8e3f2a1
Create Date: 2026-02-07 10:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'g8h9i0j1k2l3'
down_revision: Union[str, Sequence[str], None] = 'fcd9b8e3f2a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Drop age and number columns from players table."""
    # Drop age column
    op.drop_column('players', 'age')
    
    # Drop number column
    op.drop_column('players', 'number')


def downgrade() -> None:
    """Downgrade schema - Re-add age and number columns to players table."""
    # Re-add number column
    op.add_column('players', sa.Column('number', sa.Integer(), nullable=True))
    
    # Re-add age column
    op.add_column('players', sa.Column('age', sa.Integer(), nullable=True))
