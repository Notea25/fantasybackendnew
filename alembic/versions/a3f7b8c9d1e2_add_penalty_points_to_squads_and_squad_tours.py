"""Add penalty_points to squads and squad_tours

Revision ID: a3f7b8c9d1e2
Revises: 75882eb987f6
Create Date: 2026-01-31 08:37:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3f7b8c9d1e2'
down_revision: Union[str, Sequence[str], None] = '75882eb987f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add penalty_points to squads table
    op.add_column('squads', sa.Column('penalty_points', sa.Integer(), nullable=False, server_default='0'))
    
    # Add penalty_points to squad_tours table
    op.add_column('squad_tours', sa.Column('penalty_points', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove penalty_points from squad_tours table
    op.drop_column('squad_tours', 'penalty_points')
    
    # Remove penalty_points from squads table
    op.drop_column('squads', 'penalty_points')
